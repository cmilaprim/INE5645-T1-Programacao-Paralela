# Sistema de Vendas

## 1. Abertura

O trabalho implementa um protótipo de sistema de vendas usando programação paralela. A ideia é simular clientes criando pedidos, validadores verificando os pedidos, a etapa financeira aprovando ou recusando pagamentos e a logística entregando os pedidos aprovados.

O objetivo principal foi usar processos, filas e padrões de projeto paralelos para criar um fluxo concorrente e multiprocessado, em vez de executar tudo sequencialmente.

## 2. Problema modelado

O sistema simula uma venda de itens. Cada cliente gera vários pedidos. Cada pedido passa por três etapas principais:

1. validação do pedido;
2. validação financeira;
3. logística/entrega.

Cada etapa pode falhar de acordo com uma taxa configurável. Assim, um pedido pode ser rejeitado na validação, recusado financeiramente, entregue com sucesso ou falhar na entrega.

## 3. Arquitetura geral

A arquitetura foi construída como um pipeline com filas entre as etapas:

```text
Clientes produtores
        |
        v
fila_pedidos
        |
        v
validadores
        |
        v
fila_validados
        |
        v
financeiros
        |
        v
fila_aprovados
        |
        v
logísticos
        |
        v
monitor / relatório final
```

As etapas trabalham ao mesmo tempo. Enquanto os clientes ainda produzem novos pedidos, os validadores já processam pedidos anteriores, o financeiro já processa pedidos validados e a logística já começa as entregas dos pedidos aprovados.

## 4. Concorrência e paralelismo

A concorrência aparece porque várias atividades ficam em andamento no mesmo intervalo de tempo. Por exemplo, um cliente pode estar criando um pedido enquanto um validador processa outro pedido e a logística entrega um terceiro.

O paralelismo aparece porque essas atividades rodam em processos diferentes do sistema operacional. Nos logs, isso é evidenciado pelos PIDs diferentes, como `PID 3132`, `PID 7944`, `PID 17788`, etc.

Uma frase para explicar:

> A concorrência está na sobreposição das etapas do pipeline; o paralelismo está no uso de múltiplos processos executando essas etapas.

## 5. Padrões de projeto utilizados

### 5.1 Produtor/Consumidor

Os clientes são produtores de pedidos. Os validadores são consumidores da fila de pedidos. Depois, os validadores viram produtores para a fila dos financeiros, e assim por diante.

Esse padrão aparece nas filas:

```text
fila_pedidos
fila_validados
fila_aprovados
fila_monitor
```

A fila limitada cria disputa por recurso. Se a fila enche, o produtor espera; se a fila está vazia, o consumidor espera.

### 5.2 Worker Pool

Cada etapa possui vários workers do mesmo tipo:

```text
num_validadores
num_financeiros
num_logisticos
```

Esses workers ficam vivos e retiram tarefas das filas. Isso evita criar um processo novo para cada pedido e melhora a organização do fluxo.

### 5.3 Pipeline

O pedido passa por etapas encadeadas: produção, validação, financeiro e logística. A saída de uma etapa é a entrada da próxima. Isso permite que diferentes etapas trabalhem simultaneamente em pedidos diferentes.

### 5.4 Active Object

O monitor funciona como um Active Object. Os workers não escrevem diretamente no relatório final. Eles enviam eventos para uma fila, e o processo do monitor consome esses eventos em ordem, salvando log e JSON final.

Isso evita que vários processos escrevam no mesmo arquivo ao mesmo tempo.

## 6. Papel dos principais arquivos

### `main.py`

É o ponto de entrada. Lê os argumentos da linha de comando, escolhe uma configuração e chama o orquestrador.

Exemplo:

```bash
python main.py --config teste
```

### `config.py`

Define as configurações do sistema: número de clientes, pedidos por cliente, quantidade de workers, tamanho das filas, taxas de falha, tempos de processamento e arquivo de log.

### `pedido.py`

Define a entidade `Pedido`, seus estados possíveis e os métodos para atualizar status e converter o pedido para dicionário.

### `orquestrador.py`

É o controlador principal. Cria as filas, inicia o monitor, cria os processos dos workers e coordena o encerramento ordenado do pipeline.

### `workers.py`

Contém as funções executadas pelos processos: cliente, validador, financeiro e logística.

### `monitor.py`

Centraliza os eventos dos workers, grava o log textual e gera o relatório JSON final.

## 7. Por que encerrar em cascata?

O sistema inicia todas as etapas praticamente junto. Os validadores não esperam os clientes terminarem para começar.

O que acontece no final é diferente: o orquestrador espera os clientes terminarem para saber que não haverá mais pedidos novos. Depois envia `None` para os validadores, indicando que eles podem encerrar quando consumirem tudo.

A ordem é:

```text
espera clientes
envia None para validadores
espera validadores
envia None para financeiros
espera financeiros
envia None para logísticos
espera logísticos
finaliza monitor
```

Isso evita que uma etapa seja finalizada antes de receber todos os pedidos que ainda poderiam chegar.


## 8. Gargalo e throughput

O throughput é calculado como:

```text
pedidos finalizados / tempo total
```

A etapa mais lenta limita a vazão do sistema. Se houver 3 validadores, 2 financeiros e apenas 1 logístico, a logística tende a ser o gargalo, principalmente se os tempos médios forem parecidos.

As filas limitadas ajudam a mostrar backpressure: quando a etapa final é mais lenta, a fila anterior pode encher, fazendo os financeiros esperarem, depois os validadores, e por fim os clientes.

## 9. Vantagens da solução

- Usa paralelismo real com `multiprocessing`.
- Separa responsabilidades por arquivo e por etapa.
- Usa filas para desacoplar produtores e consumidores.
- Permite configurar número de workers e taxas de falha.
- Gera logs com timestamp, PID, processo e etapa.
- Gera relatório JSON final com métricas.
- Facilita demonstrar concorrência, paralelismo, pipeline e disputa por recurso.

## 10. Desvantagens e limitações

- Como é uma simulação, as validações são aleatórias e não representam regras reais de negócio.
- `multiprocessing` tem custo maior que threads para criar processos e trocar objetos entre filas.
- A ordem do log representa a ordem em que o monitor recebeu os eventos, não necessariamente uma ordem física perfeita de execução.
- O desempenho depende do gargalo do pipeline.
- Para poucos pedidos, o overhead dos processos pode ser maior que o benefício do paralelismo.

## 11. Demonstração sugerida

1. Rodar configuração rápida:

```bash
python main.py --config teste
```

2. Mostrar os PIDs diferentes no log.
3. Mostrar que clientes, validadores, financeiro e logística aparecem intercalados.
4. Abrir o JSON final.
5. Explicar contadores por status.
6. Rodar um segundo teste alterando número de logísticos:

```bash
python main.py --config teste --logisticos 2
```

7. Comparar tempo total e throughput.
