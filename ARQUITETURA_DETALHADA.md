# Arquitetura - 3 Padrões de Projeto Paralelo - INE 5645

## 🎯 RESUMO: 3 PADRÕES DISTINTOS

Este sistema implementa **3 padrões de projeto paralelo diferentes e bem definidos**:

1. **Producer-Consumer** - Cliente produz, workers consomem via filas
2. **Pipeline** - 3 estágios paralelos (Validação → Financeira → Logística)
3. **Worker Pool** - Múltiplos workers em cada estágio

---

## 1. PADRÃO 1: PRODUCER-CONSUMER

### O Conceito
Um **produtor** gera dados e coloca em uma fila. Um ou mais **consumidores** pegam dados da fila e os processam.

```
Cliente (Produtor)
  ↓
[Fila de Pedidos] ← Thread-safe
  ↓
Validador 1 (Consumidor)
Validador 2 (Consumidor)
Validador 3 (Consumidor)
```

### No Código
**Arquivo**: `src/workers/workers.py` (linha 14)

**Produtor** - `cliente_worker()`:
```python
def cliente_worker(...):
    for num_pedido in range(config.pedidos_por_cliente):
        pedido = criar_pedido(...)
        fila_saida.put(pedido)  # ← PRODUZ
```

**Consumidores** - Todos os 3 workers:
```python
def validador_worker(...):
    while True:
        pedido = fila_entrada.get(timeout=5)  # ← CONSOME
        # processar...
        fila_saida.put(pedido)  # ← PASSA ADIANTE
```

### Por Que é Bom?
✓ Produtor não sabe quantos consumidores existem  
✓ Fila absorve picos de carga  
✓ Fácil escalar: adicionar mais consumidores melhora throughput  
✓ Sincronização automática (Queue é thread-safe)

---

## 2. PADRÃO 2: PIPELINE

### O Conceito
Uma **sequência de estágios** onde cada estágio processa dados e passa para o próximo. Todos rodam em **paralelo real**.

```
Entrada
  ↓
┌─────────────────┐
│  ESTÁGIO 1      │  Validação
│ (3 workers)     │
└─────────────────┘
  ↓ (fila)
┌─────────────────┐
│  ESTÁGIO 2      │  Financeira
│ (2 workers)     │
└─────────────────┘
  ↓ (fila)
┌─────────────────┐
│  ESTÁGIO 3      │  Logística
│ (2 workers)     │
└─────────────────┘
  ↓
Saída

Importante: Os 3 estágios rodam SIMULTANEAMENTE!
Pedido A pode estar no Estágio 1 ENQUANTO Pedido B está no Estágio 2
ENQUANTO Pedido C está no Estágio 3
```

### No Código
**Arquivo**: `src/controller/orchestrator.py` (linha 73)

```python
# Estágio 1: Validação
self.fila_pedidos          # Entrada
  → [3 validadores]
    → self.fila_validados  # Saída para próximo estágio

# Estágio 2: Financeira  
self.fila_validados        # Entrada
  → [2 financeiros]
    → self.fila_aprovados  # Saída para próximo estágio

# Estágio 3: Logística
self.fila_aprovados        # Entrada
  → [2 logísticos]
    → Fim do pipeline
```

### Por Que é Bom?
✓ Paralelismo máximo: 3 estágios REALMENTE em paralelo  
✓ Divisão clara de responsabilidade  
✓ Throughput muito melhor que serial  
✓ Pode adicionar/remover estágios facilmente

### Visualização
```
TEMPO →

Pedido A: [Validação     ] [Financeira    ] [Logística]
Pedido B:                 [Validação     ] [Financeira]
Pedido C:                                  [Validação ]

Note: Vários pedidos em estágios diferentes SIMULTANEAMENTE
```

---

## 3. PADRÃO 3: WORKER POOL

### O Conceito
Um **pool fixo de workers idênticos** que processam dados da mesma fila. O trabalho é distribuído automaticamente entre eles.

```
        Fila de Entrada
           /    |    \
          /     |     \
    [Worker 1] [Worker 2] [Worker 3]

Todos processam a mesma fila.
Trabalho distribuído automaticamente.
Cada worker tem um ID único para rastreamento.
```

### No Código
**Arquivo**: `src/controller/orchestrator.py` + `src/workers/workers.py`

**Criação do Pool** (orchestrator.py):
```python
# Pool de Validadores
for validador_id in range(self.config.num_validadores):  # Ex: 3
    p = Process(target=validador_worker, args=(validador_id, ...))
    p.start()

# Pool de Financeiros
for financeiro_id in range(self.config.num_financeiros):  # Ex: 2
    p = Process(target=financeiro_worker, args=(financeiro_id, ...))
    p.start()

# Pool de Logísticos
for logistica_id in range(self.config.num_logisticos):  # Ex: 2
    p = Process(target=logistica_worker, args=(logistica_id, ...))
    p.start()
```

**Uso do Pool** (workers.py):
```python
def validador_worker(worker_id, ...):
    # worker_id identifica qual worker (0, 1, 2, etc)
    while True:
        pedido = fila_entrada.get()  # Distribui automaticamente
        print(f"Worker-{worker_id}: processando {pedido.id}")
        processar(pedido)
```

### Por Que é Bom?
✓ Controle fino sobre nível de paralelismo  
✓ Balanceamento automático entre workers  
✓ Fácil escalar: aumentar número de workers no config  
✓ Melhor utilização de CPU multicore  
✓ Rastreamento individual de cada worker

### Exemplo Real
```
Configuração: 3 validadores, 2 financeiros, 2 logísticos

Então temos: 3 + 2 + 2 = 7 processos rodam EM PARALELO

Cada um em seu núcleo de CPU (em máquina multicore)
```

---

## 4. COMO OS 3 PADRÕES TRABALHAM JUNTOS

```
┌──────────────────────────────────────────────────────────────┐
│              SISTEMA COMPLETO                                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  PADRÃO 1: PRODUCER-CONSUMER                                 │
│  ─────────────────────────────────────                       │
│  Cliente (Produtor) →  [Fila] ← Validadores (Consumidores)  │
│                                                              │
│  PADRÃO 2: PIPELINE                                          │
│  ─────────────────────                                       │
│  Validadores → [Fila] → Financeiros → [Fila] → Logísticos  │
│                                                              │
│  PADRÃO 3: WORKER POOL                                       │
│  ─────────────────────                                       │
│  [Val-1] [Val-2] [Val-3]  ← Pool de Validadores            │
│  [Fin-1] [Fin-2]           ← Pool de Financeiros            │
│  [Log-1] [Log-2]           ← Pool de Logísticos             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Fluxo Completo
```
1. Cliente cria pedido
   ↓
2. Coloca em fila (Producer-Consumer)
   ↓
3. Um dos 3 validadores pega (Worker Pool de Estágio 1)
   ↓
4. Coloca em fila_validados (Pipeline)
   ↓
5. Um dos 2 financeiros pega (Worker Pool de Estágio 2)
   ↓
6. Coloca em fila_aprovados (Pipeline)
   ↓
7. Um dos 2 logísticos pega (Worker Pool de Estágio 3)
   ↓
8. Entrega!

Enquanto isso: Pedido B está no estágio 2, Pedido C no estágio 1
(Pipeline paralelismo)
```

---

## 5. ONDE CADA PADRÃO ESTÁ NO CÓDIGO

### Producer-Consumer
- **Arquivo**: `src/workers/workers.py`
- **Linha**: 14
- **Funções**: `cliente_worker()` (produtor), todos os 3 workers (consumidores)
- **Filas**: `fila_pedidos`, `fila_validados`, `fila_aprovados`

### Pipeline
- **Arquivo**: `src/workers/workers.py`
- **Linhas**: 73 (comentário), 80, 175, 272
- **Estágios**: 
  - Estágio 1: `validador_worker()`
  - Estágio 2: `financeiro_worker()`
  - Estágio 3: `logistica_worker()`
- **Conexão**: Cada worker consome de uma fila e produz para a próxima

### Worker Pool
- **Arquivo**: `src/controller/orchestrator.py`
- **Funções de criação**: 
  - Linha ~80: Criação de Pool de Validadores
  - Linha ~95: Criação de Pool de Financeiros
  - Linha ~110: Criação de Pool de Logísticos
- **Identificação**: `worker_id` em cada função worker

---

## 6. CONFIGURAÇÃO DOS PADRÕES

Edite `src/model/config.py`:

```python
CONFIG_PADRAO = ConfiguracaoSistema(
    # WORKER POOL: Tamanho de cada pool
    num_validadores=3,      # Pool de 3 validadores
    num_financeiros=2,      # Pool de 2 financeiros
    num_logisticos=2,       # Pool de 2 logísticos
    
    # PRODUCER-CONSUMER: Taxa de produção vs consumo
    num_clientes=1,
    pedidos_por_cliente=50,
    
    # PIPELINE: Tempos de processamento
    tempo_processamento_min=0.5,
    tempo_processamento_max=2.0,
)
```

**Aumentar `num_validadores`?** → Mais paralelismo no Pool → Mais rápido  
**Mudar tempos de processamento?** → Afeta timing do Pipeline  
**Aumentar `pedidos_por_cliente`?** → Mais trabalho para o Producer-Consumer

---

## 7. VERIFICAÇÃO: Você tem 3 padrões?

Checklist:
- [ ] **Producer-Consumer**: Cliente produz, validadores consomem via fila
- [ ] **Pipeline**: 3 estágios (Validação→Financeira→Logística) rodam em paralelo
- [ ] **Worker Pool**: Múltiplos workers em cada estágio processam simultaneamente

Se todos 3 estão ✓, você tem um sistema **profissional com 3 padrões paralelo**! 🎉

---

## 8. RESUMO TÉCNICO

| Aspecto | Producer-Consumer | Pipeline | Worker Pool |
|---------|------------------|----------|------------|
| **O quê?** | Produtor → Fila → Consumidor | 3 estágios em série | N workers em paralelo |
| **Onde?** | Cliente → Validadores | Val → Fin → Log | Cada estágio |
| **Benefício** | Desacoplamento | Paralelismo máximo | Controle fino |
| **Sincronização** | Via Fila (Queue) | Via Filas | Via Filas |
| **Escalabilidade** | Adicione consumidores | Adicione estágios | Aumentar workers |

---

**Última atualização**: 3 de maio de 2026
