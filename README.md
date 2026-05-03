# README - Sistema de Vendas Paralelo

**Disciplina**: Programação Paralela e Distribuída (INE 5645)  
**Universidade**: UFSC  
**Semestre**: 2026/1  
**Autores**: [Adicione nomes aqui]

## 📋 Resumo

Este projeto implementa um **protótipo de sistema de vendas paralelo** que simula o fluxo de processamento de pedidos com múltiplas etapas concorrentes usando **Python com multiprocessing** para garantir verdadeiro paralelismo em múltiplos núcleos.

## 🎯 Padrões de Projeto Implementados

### 1. **Producer-Consumer** (Padrão Produtor-Consumidor)
- **Aplicação**: Clientes produzem pedidos → Fila → Validadores consomem
- **Benefício**: Desacoplamento entre produção e consumo, absorve picos de carga
- **Implementação**: Fila `fila_pedidos` conecta `cliente_worker` e `validador_worker`

### 2. **Pipeline** (Padrão Linha de Montagem)  
- **Aplicação**: 3 estágios paralelos (Validação → Financeira → Logística)
- **Benefício**: Paralelismo máximo, cada etapa em seu próprio processo
- **Implementação**: Filas conectam estágios: `fila_pedidos` → `fila_validados` → `fila_aprovados`

### 3. **Worker Pool** (Padrão Pool de Workers)
- **Aplicação**: Múltiplos workers (processos) por estágio
- **Benefício**: Controle fino de concorrência e balanceamento de carga
- **Implementação**: N validadores, N financeiros, N logísticos processam em paralelo

## 🏗️ Arquitetura MVC

```
src/
├── model/                 # Dados e configuração
│   ├── pedido.py         # Classe Pedido com seus estados
│   └── config.py         # Configuração do sistema (workers, taxas falha, etc)
├── view/                 # Interface e monitoramento
│   └── monitor.py        # Logs e relatórios
├── controller/           # Orquestração
│   └── orchestrator.py   # Coordena filas e processos
└── workers/              # Processamento paralelo
    └── workers.py        # Funções worker (cliente, validadores, etc)
```

## 🚀 Como Executar

### Pré-requisitos
- Python 3.7+
- Nenhuma dependência externa (usa apenas `multiprocessing` da stdlib)

### Execução Rápida (Recomendado para Teste)
```bash
cd "INE5645 - T1 - Programacao Concorrente"
python3 main.py --teste
```
⏱️ Tempo esperado: ~5 segundos

### Execução Padrão
```bash
python3 main.py
```
⏱️ Tempo esperado: ~15-30 segundos

### Execução com Carga Pesada
```bash
python3 main.py --pesado
```
⏱️ Tempo esperado: ~30-60 segundos

### Configuração Customizada
```bash
python3 main.py --custom 4 3 100
```
(4 validadores, 3 financeiros, 100 pedidos)

## 📊 Saídas Geradas

Cada execução gera:

1. **`sistema_vendas.log`** - Log detalhado de todos os eventos
   ```
   [16:23:36.752] [PRODUTOR] Worker-0: Pedido abc123 - CRIADO (Notebook - R$1234.56)
   [16:23:36.850] [VALIDACAO] Worker-0: Pedido abc123 - INICIO (Cliente: CLT-000)
   [16:23:37.120] [VALIDACAO] Worker-0: Pedido abc123 - SUCESSO (Tempo: 0.27s)
   ...
   ```

2. **`sistema_vendas.json`** - Relatório estatístico
   ```json
   {
     "tempo_total_segundos": 4.58,
     "pedidos_processados": {
       "validacao_sucesso": 9,
       "validacao_falha": 1,
       "financeira_sucesso": 9,
       "logistica_sucesso": 9
     },
     "tempos_por_etapa": {
       "validacao": {"minimo": 0.11, "maximo": 0.43, "media": 0.27, ...},
       ...
     }
   }
   ```

## 💡 Conceitos Principais

### Por que `multiprocessing` e não `threading`?
- **threading**: Compartilha memória, sujeito ao GIL (Global Interpreter Lock), **sem paralelismo real**
- **multiprocessing**: Processos separados, **com paralelismo real em múltiplos núcleos** ✓

### Filas (Queue)
- Thread-safe e process-safe
- Conectam estágios do pipeline
- Permitem comunicação entre processos

### Sincronização
- Sem locks explícitos (filas fazem isso automaticamente)
- Cada worker processa independentemente
- Falha em um worker não afeta outros

## 📈 Casos de Teste

### Teste 1: Rápido
```bash
python3 main.py --teste
# 10 pedidos, 2 validadores, 1 financeiro, 1 logístico
# ~5 segundos
```

### Teste 2: Padrão
```bash
python3 main.py
# 50 pedidos, 3 validadores, 2 financeiros, 2 logísticos
# ~15-30 segundos
```

### Teste 3: Pesado
```bash
python3 main.py --pesado
# 200 pedidos, 5 validadores, 4 financeiros, 3 logísticos
# ~30-60 segundos
```

## 🔧 Customização

Edite `src/model/config.py` para ajustar:

```python
CONFIG_PADRAO = ConfiguracaoSistema(
    num_validadores=3,           # Aumentar = mais paralelismo
    num_financeiros=2,
    num_logisticos=2,
    taxa_falha_validacao=0.1,    # 10% falham
    taxa_falha_financeira=0.15,
    taxa_falha_logistica=0.05,
    pedidos_por_cliente=50,
    tempo_processamento_min=0.5, # Segundos
    tempo_processamento_max=2.0
)
```

## 📚 Estrutura do Código

### model/pedido.py
- `StatusPedido`: Enum dos 7 estados possíveis
- `Pedido`: Dataclass com id, cliente, item, valor, status, timestamps
- `criar_pedido()`: Factory function

### model/config.py
- `ConfiguracaoSistema`: Todas as configurações do sistema
- Pré-definidas: `CONFIG_PADRAO`, `CONFIG_TESTE`, `CONFIG_PESADO`

### view/monitor.py
- `MonitorSistema`: Gerencia logs e estatísticas
- `registrar_evento()`: Registra evento em arquivo e console
- `gerar_relatorio_final()`: Cria JSON com estatísticas

### controller/orchestrator.py
- `OrchestradorSistemaVendas`: Coordena todo o sistema
- `iniciar_sistema()`: Cria processos workers
- `aguardar_conclusao()`: Aguarda finalização com sinais de parada

### workers/workers.py
- `cliente_worker()`: Produtor (Producer-Consumer)
- `validador_worker()`: Consumidor 1 (Worker Pool)
- `financeiro_worker()`: Consumidor 2 (Worker Pool)
- `logistica_worker()`: Consumidor 3 (Worker Pool)

## ✅ Validação

Após executar, verifique:
- [ ] Nenhuma mensagem de erro
- [ ] Arquivo `sistema_vendas.log` criado com eventos
- [ ] Arquivo `sistema_vendas.json` criado com estatísticas
- [ ] Número de sucessos + falhas = total de pedidos esperado
- [ ] Tempo total razoável

## 🎓 Aprendizados

Este projeto demonstra:
1. ✅ Paralelismo real em Python via multiprocessing
2. ✅ 3 padrões de projeto paralelo implementados
3. ✅ Sincronização via filas (Producer-Consumer)
4. ✅ Arquitetura MVC para sistemas paralelos
5. ✅ Escalabilidade através de worker pools
6. ✅ Monitoramento de sistemas concorrentes

---

**Última atualização**: 03 de maio de 2026
