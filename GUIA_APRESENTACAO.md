# 🎓 GUIA DE APRESENTAÇÃO - INE 5645 T1

## 🎯 COMO APRESENTAR ESTE PROJETO

Este documento orienta você sobre como apresentar o trabalho para o professor/banca.

---

## 📺 DEMONSTRAÇÃO PRÁTICA (5 minutos)

### Passo 1: Abrir Terminal
```bash
cd "/home/camila/INE5645 - T1 - Programacao Concorrente"
```

### Passo 2: Executar Teste Rápido
```bash
python3 main.py --teste
```

**O que mostrar:**
- Padrões listados no início do programa
- Processos iniciando (cliente, validadores, financeiros, logísticos)
- Configuração do sistema
- Resumo final com estatísticas

**Tempo:** 4-5 segundos

### Passo 3: Mostrar Log
```bash
less sistema_vendas.log
```

**Destacar:**
```
[PRODUTOR] criando pedidos
[VALIDACAO] Worker-0 e Worker-1 processando SIMULTANEAMENTE
[FINANCEIRA] Worker-0 recebendo de VALIDACAO
[LOGISTICA] Worker-0 entregando
```

**Isso prova:** Producer-Consumer + Pipeline + Worker Pool

### Passo 4: Mostrar JSON
```bash
cat sistema_vendas.json
```

**Destacar:**
- "tempo_total_segundos": 3.82
- "validacao_sucesso": 10 (todos os 10 pedidos processados)
- "tempos_por_etapa": Mostra que cada estágio foi executado

---

## 📊 APRESENTAÇÃO TÉCNICA (10 minutos)

### Slide 1: Objetivos
Mostrar o documento **SUMARIO_VISUAL.md**

```bash
cat SUMARIO_VISUAL.md | head -50
```

**Falar:**
- "Este trabalho implementa 3 padrões de projeto paralelo"
- "Em uma arquitetura MVC"
- "Com verdadeiro paralelismo usando multiprocessing"

### Slide 2: Producer-Consumer
**Comando:**
```bash
cat ARQUITETURA_DETALHADA.md | grep -A 30 "1. PADRÃO 1"
```

**Diagrama:**
```
Cliente (Produtor)
  ↓
[Fila de Pedidos]
  ↓
Validador 1, 2, 3 (Consumidores)
```

**Falar:**
- "O cliente produz pedidos"
- "Coloca na fila thread-safe"
- "Múltiplos validadores consomem independentemente"

### Slide 3: Pipeline
**Comando:**
```bash
cat ARQUITETURA_DETALHADA.md | grep -A 40 "2. PADRÃO 2"
```

**Timeline:**
```
P1: [Validação] [Financeira] [Logística]
P2:            [Validação] [Financeira] [Logística]
P3:                       [Validação] [Financeira]
```

**Falar:**
- "3 estágios sequenciais rodando em paralelo"
- "Cada pedido passa pela pipeline"
- "Ganho de throughput vs serial"

### Slide 4: Worker Pool
**Comando:**
```bash
cat ARQUITETURA_DETALHADA.md | grep -A 40 "3. PADRÃO 3"
```

**Diagrama:**
```
Fila [P1] [P2] [P3] [P4]
      ↓    ↓    ↓    ↓
    [W1] [W2] [W3]
```

**Falar:**
- "Múltiplos workers idênticos"
- "Distribuição automática de carga"
- "Escalabilidade: mais workers = mais rápido"

### Slide 5: Arquitetura MVC
**Mostrar:**
```
Model:      Pedido, StatusPedido, Config (src/model/)
View:       MonitorSistema, logging, JSON (src/view/)
Controller: OrchestradorSistemaVendas (src/controller/)
Workers:    cliente, validador, financeiro, logistica (src/workers/)
```

**Falar:**
- "Separação clara de responsabilidades"
- "Model: dados do domínio"
- "View: monitoramento e relatório"
- "Controller: orquestração de processos"

### Slide 6: Performance
**Comando:**
```bash
cat PERFORMANCE_ANALISE.md | grep -A 20 "📈 GRÁFICOS"
```

**Dados:**
- Mínimo (1+1): 66.53s para 50 pedidos
- Máximo (5+4): 31.91s para 50 pedidos
- **Ganho: 2.08× mais rápido**

**Falar:**
- "Worker Pool oferece escalabilidade linear"
- "Cada worker adicional melhora throughput"
- "Ganho medido: 2.08× com 9 workers vs 3"

---

## 💻 DEMONSTRAÇÃO DE CÓDIGO (8 minutos)

### Abrir VS Code
```bash
code .
```

### Mostrar Arquivo 1: main.py
```
Destacar:
- import multiprocessing
- argparse para 4 modos
- OrchestradorSistemaVendas
- try/except com exit codes
```

**Falar:** "Entry point com CLI que suporta 4 modos de execução"

### Mostrar Arquivo 2: src/model/pedido.py
```
Destacar:
- StatusPedido enum (7 estados)
- Pedido dataclass
- criar_pedido() factory
```

**Falar:** "Model define a estrutura de dados e ciclo de vida de um pedido"

### Mostrar Arquivo 3: src/controller/orchestrator.py
```
Destacar:
- iniciar_sistema() cria 7 processos
- self.fila_pedidos, self.fila_validados, self.fila_aprovados
- aguardar_conclusao() com sinais None
```

**Falar:** "Controller orquestra todos os processos e sincroniza com Queues"

### Mostrar Arquivo 4: src/workers/workers.py
```
Destacar:
- cliente_worker() (Produtor)
- validador_worker() (Pipeline estágio 1 + Pool + Consumer)
- financeiro_worker() (Pipeline estágio 2 + Pool + Consumer)
- logistica_worker() (Pipeline estágio 3 + Pool + Consumer)

Linha chave: fila_entrada.get(timeout=5) e fila_saida.put(pedido)
```

**Falar:** 
- "Implementação dos 3 padrões em 4 funções"
- "Cada worker consome de uma fila e produz para a próxima"
- "Timeout evita deadlock"

### Mostrar Arquivo 5: src/view/monitor.py
```
Destacar:
- registrar_evento() com threading.Lock
- gerar_relatorio_final()
- Parse de log para JSON
```

**Falar:** "View centraliza monitoramento e geração de relatórios"

---

## 🎨 VISUAL AIDS (Imprimir se Possível)

### Diagrama 1: Arquitetura Geral
```
┌────────────────────────────────────────────────────┐
│  SISTEMA DE VENDAS PARALELO - 3 PADRÕES            │
├────────────────────────────────────────────────────┤
│                                                    │
│  PADRÃO 1: PRODUCER-CONSUMER                      │
│  Cliente → [Fila] ← Validadores                   │
│                                                    │
│  PADRÃO 2: PIPELINE                               │
│  [Val] → [Fila] → [Fin] → [Fila] → [Log]         │
│                                                    │
│  PADRÃO 3: WORKER POOL                            │
│  [W1] [W2] [W3] ← Múltiplos workers              │
│                                                    │
│  Total: 7 processos paralelos                     │
│  Verdadeiro paralelismo em múltiplos núcleos      │
│                                                    │
└────────────────────────────────────────────────────┘
```

### Diagrama 2: Comparação de Performance
```
VELOCIDADE (pedidos/segundo)

2.6 p/s ├─────────────────────┐
        │                     │
2.0 p/s ├─────────────────    │
        │                     │
1.5 p/s ├─────────────────    ├─────────────
        │                     │
1.0 p/s ├──                   │
        │                     │
0.5 p/s ├──                   ├─────────────
        │
0.0 p/s └───────────────────────────────────
        Mínimo  Teste  Máximo
        (1+1)   (2+1)  (5+4)
        0.75    2.6    1.57
        
        GANHO: 2.08× com mais workers
```

---

## 🗣️ SCRIPT DE APRESENTAÇÃO (5 minutos)

### Introdução (30 segundos)
```
"Bom dia/tarde. Apresento o trabalho INE 5645 T1 - 
Programação Paralela e Distribuída.

Implementei um sistema de processamento de pedidos com:
- 3 padrões de projeto paralelo distintos
- Verdadeiro paralelismo usando múltiplos núcleos
- Arquitetura MVC bem estruturada"
```

### Demonstração Prática (1 minuto)
```
"Primeiro, vou mostrar o sistema funcionando..."
[Executar: python3 main.py --teste]
"Veem aqui os processos iniciando..."
[Mostrar log com grep]
"E os 3 padrões em ação..."
```

### Padrão 1 (1 minuto)
```
"Primeiro padrão: Producer-Consumer.
O cliente é o produtor independente que gera pedidos.
Os validadores são consumidores que pegam da fila.
Benefício: desacoplamento total."
```

### Padrão 2 (1 minuto)
```
"Segundo padrão: Pipeline.
3 estágios sequenciais rodando em paralelo.
Validação → Financeira → Logística.
Cada estágio passa o trabalho para o próximo."
```

### Padrão 3 (1 minuto)
```
"Terceiro padrão: Worker Pool.
Múltiplos workers idênticos em cada estágio.
Distribuição automática de carga.
Resultado: ganho linear com mais workers."
```

### Performance (30 segundos)
```
"Medições de performance:
Com 1 worker em cada estágio: 66.53 segundos
Com 5+4 workers: 31.91 segundos
Ganho: 2.08 vezes mais rápido com paralelismo"
```

---

## ❓ POSSÍVEIS PERGUNTAS E RESPOSTAS

### P: Por que usar multiprocessing em vez de threading?
**R:** "Porque Python tem GIL (Global Interpreter Lock) que impede verdadeiro paralelismo em threads. Com multiprocessing, cada processo tem seu próprio interpretador Python e pode rodar em núcleo diferente."

### P: Como funciona a sincronização entre processos?
**R:** "Usamos multiprocessing.Queue() que é thread-safe e process-safe. Funciona como um buffer entre produtor e consumidor. Quando consumidor termina, busca próximo item da fila."

### P: Por que há "falhas" aleatórias nos pedidos?
**R:** "São intencionais para simular um sistema real. Taxa de falha configurável em ConfiguracaoSistema. Alguns pedidos falham em validação, financeira ou logística, como em sistema real."

### P: Como você implementou os 3 padrões em um único sistema?
**R:** "Pipeline fornece os 3 estágios. Cada estágio usa:
- Producer-Consumer: recebe de fila anterior, passa para fila posterior
- Worker Pool: múltiplos workers em cada estágio
São 3 padrões sobrepostos no mesmo sistema."

### P: Como você mediu o ganho de performance?
**R:** "Executei o sistema com diferentes configurações:
- Baseline: 1 validador, 1 financeiro
- Com Pool: 5 validadores, 4 financeiros
Ambos com 50 pedidos. Midindo tempo total e calculando speedup."

### P: Qual é o limite de escalabilidade?
**R:** "Limite é o número de núcleos de CPU. Se tiver 8 núcleos, máximo 8 workers em paralelo real. Com mais workers, há overhead de context switching que reduz ganho."

---

## 📁 ARQUIVOS PARA MOSTRAR

### Essenciais
1. **SUMARIO_VISUAL.md** - Visão geral dos 3 padrões
2. **sistema_vendas.log** - Prova de execução
3. **sistema_vendas.json** - Estatísticas
4. **src/workers/workers.py** - Implementação dos padrões

### Complementares
5. **ARQUITETURA_DETALHADA.md** - Explicação detalhada
6. **PERFORMANCE_ANALISE.md** - Comparativo de performance
7. **main.py** - Entry point
8. **src/controller/orchestrator.py** - Orquestração

---

## ⏱️ TIMING SUGERIDO

```
Total: 15-20 minutos

├─ Demonstração prática: 5 min
├─ Apresentação dos 3 padrões: 5 min
├─ Análise de código: 5 min
└─ Perguntas/Discussão: 5 min
```

---

## 🎯 OBJETIVO DA APRESENTAÇÃO

Deixar claro que você compreende:
1. ✅ Os 3 padrões de projeto paralelo
2. ✅ Como implementá-los em Python
3. ✅ Como sincronizar múltiplos processos
4. ✅ Como arquitetar um sistema paralelo
5. ✅ Como medir performance

---

**Boa apresentação!** 🚀
