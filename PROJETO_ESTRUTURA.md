# Estrutura Completa do Projeto - INE 5645 T1

## 📦 ARQUIVOS DO PROJETO

```
INE5645 - T1 - Programacao Concorrente/
│
├── 📁 src/                              ← Código-fonte (MVC)
│   ├── 📁 model/                        ← Camada Model
│   │   ├── pedido.py                   ← Domain model (Pedido, StatusPedido)
│   │   ├── config.py                   ← Configurações do sistema
│   │   └── __init__.py
│   │
│   ├── 📁 view/                         ← Camada View
│   │   ├── monitor.py                  ← Monitoramento e logging
│   │   └── __init__.py
│   │
│   ├── 📁 controller/                   ← Camada Controller
│   │   ├── orchestrator.py             ← Orquestração do sistema
│   │   └── __init__.py
│   │
│   ├── 📁 workers/                      ← Worker processes
│   │   ├── workers.py                  ← Implementação dos 3 padrões
│   │   └── __init__.py
│   │
│   └── __init__.py
│
├── 📄 main.py                          ← Entry point (CLI)
├── 📄 requirements.txt                 ← Dependências (vazio - só stdlib)
│
├── 📄 README.md                        ← Guia de uso
├── 📄 INSTALACAO.md                    ← Instruções de instalação
├── 📄 TESTES.md                        ← Casos de teste
├── 📄 STATUS.md                        ← Status do projeto
├── 📄 ARQUITETURA.md                   ← Visão geral de arquitetura
├── 📄 ARQUITETURA_DETALHADA.md         ← 3 padrões explicados (NOVO)
├── 📄 PADROES_EXEMPLO_PRATICO.md       ← Exemplos de execução (NOVO)
├── 📄 PERFORMANCE_ANALISE.md           ← Análise de performance (NOVO)
│
├── 📄 sistema_vendas.log               ← Log de execução (gerado)
└── 📄 sistema_vendas.json              ← Relatório JSON (gerado)
```

---

## 🎯 PADRÕES IMPLEMENTADOS

### ✅ PADRÃO 1: PRODUCER-CONSUMER
**Arquivo**: `src/workers/workers.py`  
**Linha**: 14-35 (cliente_worker), 80+ (consumidores)

**Descrição**: 
- Cliente produz pedidos independentemente
- Coloca na fila_pedidos via `.put()`
- Validadores (e demais workers) consomem via `.get()`
- Fila absorve diferenças de ritmo

**Benefício**: Desacoplamento total entre produtor e consumidores

---

### ✅ PADRÃO 2: PIPELINE
**Arquivo**: `src/workers/workers.py` + `src/controller/orchestrator.py`  
**Linhas**: 73 (comentário documentação), 80, 175, 272

**Descrição**:
- 3 estágios sequenciais executam em PARALELO:
  1. **Validação** (validadores) → fila_validados
  2. **Financeira** (financeiros) → fila_aprovados
  3. **Logística** (logísticos) → fim

**Benefício**: Máximo paralelismo com todas as etapas ocupadas

---

### ✅ PADRÃO 3: WORKER POOL
**Arquivo**: `src/controller/orchestrator.py`  
**Funções**: 
- Linha ~80-90: Criação pool validadores
- Linha ~95-105: Criação pool financeiros
- Linha ~110-120: Criação pool logísticos

**Descrição**:
- Múltiplos workers idênticos por estágio
- Trabalho distribuído automaticamente
- Cada worker identificado por ID único

**Benefício**: Escalabilidade horizontal (+ workers = + rápido)

---

## 🏗️ ARQUITETURA MVC

### Model (`src/model/`)
```python
# pedido.py
- Pedido(dataclass)           ← Dados de pedido
- StatusPedido(enum)          ← 7 estados de ciclo de vida
- criar_pedido()              ← Factory function

# config.py  
- ConfiguracaoSistema         ← Centraliza configurações
- CONFIG_PADRAO               ← Default (50 pedidos, 3-2-2 workers)
- CONFIG_TESTE                ← Fast (10 pedidos, 2-1-1 workers)
- CONFIG_PESADO               ← Heavy (200 pedidos, 5-4-4 workers)
```

### View (`src/view/`)
```python
# monitor.py
- MonitorSistema              ← Observador central
  ├─ registrar_evento()       ← Log thread-safe
  ├─ registrar_tempo_processamento()
  ├─ gerar_relatorio_final()  ← JSON stats
  └─ exibir_resumo_final()    ← Console output
```

### Controller (`src/controller/`)
```python
# orchestrator.py
- OrchestradorSistemaVendas
  ├─ iniciar_sistema()        ← Cria 7 processos
  ├─ aguardar_conclusao()     ← Aguarda termino com sinais None
  └─ executar()               ← Orquestra tudo
```

### Workers (`src/workers/`)
```python
# workers.py
- cliente_worker()            ← Produtor (1 processo)
- validador_worker()          ← Consumidor estágio 1 (N processos)
- financeiro_worker()         ← Consumidor estágio 2 (M processos)
- logistica_worker()          ← Consumidor estágio 3 (P processos)
```

---

## 🔄 FLUXO DE DADOS

```
                    ┌──────────────────┐
                    │ cliente_worker   │ ← PADRÃO 1: Produtor
                    │ (PRODUTOR)       │
                    └────────┬─────────┘
                             │ put()
                             ↓
                   ┌─────────────────┐
                   │ fila_pedidos    │ ← Thread-safe Queue
                   └────────┬────────┘
                            │ get()
              ┌─────────────┼─────────────┐
              │             │             │
       ┌──────▼────┐ ┌──────▼────┐ ┌──────▼────┐
       │Validador-0│ │Validador-1│ │Validador-2│ ← PADRÃO 3: Pool
       │ CONSUMER  │ │ CONSUMER  │ │ CONSUMER  │
       └──────┬────┘ └──────┬────┘ └──────┬────┘
              │             │             │
              └─────────────┼─────────────┘
                            │ put()
                   ┌─────────────────┐
                   │ fila_validados  │ ← Pipeline conecta estágios
                   └────────┬────────┘
                            │ get()
              ┌─────────────┴─────────────┐
              │                           │
       ┌──────▼────────┐        ┌──────────▼─────┐
       │ Financeiro-0  │        │ Financeiro-1   │ ← PADRÃO 3: Pool
       │   CONSUMER    │        │   CONSUMER     │
       └──────┬────────┘        └──────┬─────────┘
              │                       │
              └───────────┬───────────┘
                          │ put()
                 ┌─────────────────┐
                 │ fila_aprovados  │ ← Pipeline estágio 3
                 └────────┬────────┘
                          │ get()
              ┌───────────┴───────────┐
              │                       │
       ┌──────▼────────┐    ┌─────────▼──────┐
       │ Logístico-0   │    │ Logístico-1    │ ← PADRÃO 3: Pool
       │   CONSUMER    │    │   CONSUMER     │
       └──────┬────────┘    └─────────┬──────┘
              │                       │
              └───────────┬───────────┘
                          │
                    ┌─────▼──────┐
                    │   SUCESSO   │
                    │  Entregue   │
                    └─────────────┘
```

---

## 📊 COMPARAÇÃO DE PERFORMANCE

### Teste 1: --custom 5 4 50
```
• 5 validadores + 4 financeiros + 1 logístico
• 50 pedidos
• Resultado: 31.91 segundos
• Throughput: 1.57 pedidos/segundo
```

### Teste 2: --custom 1 1 50
```
• 1 validador + 1 financeiro + 1 logístico
• 50 pedidos
• Resultado: 66.53 segundos
• Throughput: 0.75 pedidos/segundo
```

### Ganho de Paralelismo
```
Speedup = 66.53 / 31.91 = 2.08×
Com 9 processos vs 3 processos
Worker Pool + Pipeline = 2× mais rápido
```

---

## 🚀 MODOS DE EXECUÇÃO

```bash
# Modo TESTE (rápido)
python3 main.py --teste

# Modo DEFAULT (normal)
python3 main.py

# Modo PESADO (pesado)
python3 main.py --pesado

# Modo CUSTOMIZADO (N1 validadores, N2 financeiros, N3 logísticos)
python3 main.py --custom 5 4 50
```

---

## 📄 DOCUMENTAÇÃO

| Arquivo | Propósito |
|---------|-----------|
| **README.md** | Guia geral do projeto |
| **INSTALACAO.md** | Como instalar e executar |
| **TESTES.md** | Casos de teste e validação |
| **STATUS.md** | Status de conclusão |
| **ARQUITETURA.md** | Visão geral da arquitetura |
| **ARQUITETURA_DETALHADA.md** | ⭐ 3 Padrões explicados em detalhes |
| **PADROES_EXEMPLO_PRATICO.md** | ⭐ Exemplos reais de execução |
| **PERFORMANCE_ANALISE.md** | ⭐ Análise de performance |

---

## 🔑 CLASSES E FUNÇÕES PRINCIPAIS

### src/model/pedido.py
```python
StatusPedido                    # Enum: 7 estados
Pedido                          # Dataclass com ordem de compra
criar_pedido()                  # Factory function
```

### src/model/config.py
```python
ConfiguracaoSistema             # Dataclass centralizada
CONFIG_PADRAO                   # Default: 50 pedidos
CONFIG_TESTE                    # Fast: 10 pedidos
CONFIG_PESADO                   # Heavy: 200 pedidos
```

### src/view/monitor.py
```python
MonitorSistema                  # Observador central
  .registrar_evento()           # Log thread-safe
  .gerar_relatorio_final()      # JSON + console
```

### src/controller/orchestrator.py
```python
OrchestradorSistemaVendas       # Controller
  .iniciar_sistema()            # Cria processos
  .aguardar_conclusao()         # Aguarda com sinais
  .executar()                   # Orquestra
```

### src/workers/workers.py
```python
cliente_worker()                # Producer
validador_worker()              # Pipeline stage 1 + Pool
financeiro_worker()             # Pipeline stage 2 + Pool
logistica_worker()              # Pipeline stage 3 + Pool
```

---

## 🎓 CONCEITOS-CHAVE

### True Parallelism
✓ Múltiplos processos (multiprocessing)  
✓ Múltiplos núcleos de CPU  
✓ **NÃO é threading** (Python GIL não afeta)

### Sincronização
✓ multiprocessing.Queue (thread-safe)  
✓ Sinais de término (None)  
✓ Join de processos

### Escalabilidade
✓ Worker Pool escalável  
✓ Pipeline adiciona estágios  
✓ Producer-Consumer desacoplado

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

- [x] **Model**: Pedido, StatusPedido, Config (src/model/)
- [x] **View**: Monitor com logging e JSON (src/view/)
- [x] **Controller**: Orchestrador coordenando tudo (src/controller/)
- [x] **Pattern 1**: Producer-Consumer (cliente → validadores)
- [x] **Pattern 2**: Pipeline (3 estágios sequenciais paralelos)
- [x] **Pattern 3**: Worker Pool (múltiplos workers por estágio)
- [x] **True Parallelism**: multiprocessing com múltiplos núcleos
- [x] **Sincronização**: Queues thread-safe + sinais de término
- [x] **Logging**: sistema_vendas.log com timestamps
- [x] **Relatório**: sistema_vendas.json com estatísticas
- [x] **CLI**: 4 modos de execução (teste, default, pesado, custom)
- [x] **Documentação**: 8 arquivos de guia
- [x] **Performance**: Teste comparativo mostrando ganho 2.08×

---

## 🎯 PRÓXIMAS ETAPAS

1. **Adicionar nomes de autores** nos docstrings Python
2. **Gerar gráficos de performance** para o relatório
3. **Escrever relatório final** com explicação dos padrões
4. **Preparar apresentação** para defesa em lab

---

**Projeto Status**: ✅ COMPLETO - Todos os 3 padrões funcionando com verdadeiro paralelismo

**Última atualização**: 3 de maio de 2026
