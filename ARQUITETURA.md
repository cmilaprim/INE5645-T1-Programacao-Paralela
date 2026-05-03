# Arquitetura de Vendas Paralelas - INE 5645

## 1. VISÃO GERAL

```
┌─────────────────────────────────────────────────────────────┐
│                   SISTEMA DE VENDAS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CONTROLLER (Orquestrador)                                  │
│  ├─ Inicia processos produtores/consumidores                │
│  ├─ Gerencia filas de comunicação                           │
│  └─ Coordena o fluxo                                        │
│                                                             │
│  CLIENTES                 PROCESSAMENTO                      │
│  (Produtor)               (Pipeline)                         │
│  │                                                           │
│  ├─→ Fila de Pedidos                                        │
│      │                                                       │
│      ├─→ [Validação Pedido]          ← Worker Pool 1        │
│          │                                                   │
│          ├─→ Fila de Validados                              │
│              │                                               │
│              ├─→ [Validação Financeira] ← Worker Pool 2      │
│                  │                                           │
│                  ├─→ Fila de Aprovados                       │
│                      │                                       │
│                      ├─→ [Logística]     ← Worker Pool 3     │
│                          │                                   │
│                          ├─→ Fila de Entregues               │
│                                                             │
│  MODEL (Dados de Negócio)                                   │
│  ├─ Pedido (status, cliente, item)                          │
│  ├─ Validações                                              │
│  └─ Histórico                                               │
│                                                             │
│  VIEW (Monitoramento)                                       │
│  └─ Logs de progresso, estatísticas                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 2. OS 3 PADRÕES DE PROJETO

### Padrão 1: PRODUCER-CONSUMER
**Onde**: Clientes → Fila de Pedidos → Validação

```python
# Cliente (Produtor)
def cliente_gera_pedidos():
    while True:
        pedido = criar_novo_pedido()
        fila_pedidos.put(pedido)  # Produz

# Validação (Consumidor)
def validador_consome():
    while True:
        pedido = fila_pedidos.get()  # Consome
        validar_pedido(pedido)
        fila_validados.put(pedido)
```

**Vantagem**: Clientes não precisam saber da validação, filas absorvem picos de carga
**Desvantagem**: Mais difícil debugar ordem de eventos

---

### Padrão 2: PIPELINE/ASSEMBLY LINE
**Onde**: Validação → Financeira → Logística (3 estágios paralelos)

```python
# Cada estágio é independente, em processo separado
ESTÁGIO 1: Validação      (processa fila_pedidos)
ESTÁGIO 2: Financeira     (processa fila_validados)
ESTÁGIO 3: Logística      (processa fila_aprovados)

# Cada etapa roda em paralelo em núcleo diferente
```

**Vantagem**: Paralelismo real, cada estágio em seu próprio processo
**Desvantagem**: Um estágio lento torna todo o pipeline lento

---

### Padrão 3: WORKER POOL
**Onde**: Cada estágio usa múltiplos workers

```python
# Pool de 3 validadores trabalhando concorrentemente
for i in range(3):
    Process(target=worker_validador, args=(i,)).start()

# Pool de 2 financeiros
for i in range(2):
    Process(target=worker_financeiro, args=(i,)).start()

# Pool de 2 logísticos
for i in range(2):
    Process(target=worker_logistica, args=(i,)).start()
```

**Vantagem**: Controle fino sobre concorrência, melhor uso de CPU
**Desvantagem**: Necessário tunar número de workers

---

## 3. ESTRUTURA MVC

### MODEL (`model/`)
```
pedido.py          → Classe Pedido (dados)
validacoes.py      → Regras de validação
```

### VIEW (`view/`)
```
monitor.py         → Exibe logs e estatísticas
```

### CONTROLLER (`controller/`)
```
orchestrator.py    → Orquestra filas e processos
```

### WORKERS (`workers/`)
```
cliente_worker.py         → Gera pedidos (Produtor)
validacao_worker.py       → Valida pedidos
financeira_worker.py      → Valida financeiro
logistica_worker.py       → Entrega pedido
```

## 4. COMO USAR MULTIPROCESSING

```python
from multiprocessing import Process, Queue

# Filas de comunicação (thread-safe entre processos!)
fila_pedidos = Queue()
fila_validados = Queue()
fila_aprovados = Queue()

# Iniciar processos
processos = []

# 1 produtor
p_cliente = Process(target=cliente_gera_pedidos, args=(fila_pedidos,))
p_cliente.start()
processos.append(p_cliente)

# 3 validadores (Worker Pool)
for i in range(3):
    p_val = Process(target=validador_worker, args=(i, fila_pedidos, fila_validados))
    p_val.start()
    processos.append(p_val)

# 2 financeiros (Worker Pool)
for i in range(2):
    p_fin = Process(target=financeiro_worker, args=(i, fila_validados, fila_aprovados))
    p_fin.start()
    processos.append(p_fin)

# 2 logísticos (Worker Pool)
for i in range(2):
    p_log = Process(target=logistica_worker, args=(i, fila_aprovados))
    p_log.start()
    processos.append(p_log)

# Aguardar
for p in processos:
    p.join()
```

## 5. FLUXO DE DADOS

```
Cliente (Processo 1)
   ↓ Queue (thread-safe)
Validador 1,2,3 (Processos 2-4) ← Cada um em seu núcleo
   ↓ Queue
Financeiro 1,2 (Processos 5-6)  ← Cada um em seu núcleo
   ↓ Queue
Logística 1,2 (Processos 7-8)   ← Cada um em seu núcleo
   ↓
Banco de Dados / Arquivo
```

**Resultado**: 8 processos paralelos em verdadeiro paralelismo! 🚀

## 6. EXEMPLO DE PEDIDO (Model)

```python
class Pedido:
    def __init__(self, id, cliente, item):
        self.id = id
        self.cliente = cliente
        self.item = item
        self.status = "Novo"  # Novo → Validado → Aprovado → Entregue
        self.timestamp_criacao = datetime.now()
    
    def para_dict(self):
        return {
            'id': self.id,
            'cliente': self.cliente,
            'item': self.item,
            'status': self.status,
            'timestamp': self.timestamp_criacao.isoformat()
        }
```

## 7. CONFIGURABILIDADE

```python
# Facilmente ajustável
CONFIG = {
    'num_validadores': 3,
    'num_financeiros': 2,
    'num_logisticos': 2,
    'taxa_falha_validacao': 0.1,      # 10% de falha
    'taxa_falha_financeira': 0.15,    # 15% de falha
    'taxa_falha_logistica': 0.05,     # 5% de falha
    'num_clientes': 1,
    'pedidos_por_cliente': 50,
    'tempo_processamento': (0.5, 2.0),  # segundos (min, max)
}
```

## 8. RESUMO DOS PADRÕES

| Padrão | Onde | Benefício | Desvantagem |
|--------|------|-----------|------------|
| Producer-Consumer | Clientes → Validação | Desacoplamento, escalável | Complexidade |
| Pipeline | Validação → Financeira → Logística | Paralelismo máximo | Gargalo sequencial |
| Worker Pool | Cada estágio tem múltiplos workers | Controle fino | Tuning necessário |

## 9. PRÓXIMOS PASSOS

1. ✅ Entender arquitetura (feito)
2. ⬜ Criar estrutura de diretórios
3. ⬜ Implementar Model (Pedido)
4. ⬜ Implementar Workers
5. ⬜ Implementar Controller (Orchestrator)
6. ⬜ Implementar View (Monitor)
7. ⬜ Testar com múltiplas configurações
8. ⬜ Escrever relatório
