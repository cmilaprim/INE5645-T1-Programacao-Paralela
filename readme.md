# Sistema de Vendas

Sistema de vendas com processamento paralelo em Python. Simula fluxo de pedidos através de múltiplas etapas usando processos independentes.

## Como executar

1. Abra o terminal na pasta do projeto
2. Execute:
   ```bash
   python3 main.py
   ```

## Configuração

As configurações do sistema estão em `src/model/config.py`. Você pode ajustar:

- Número de clientes, validadores, financeiros e logísticos
- Taxa de falha em cada etapa
- Tamanho das filas

## Saída

Após a execução, será gerado:

- `sistema_vendas.json` - Relatório final em JSON com todos os pedidos e seus status

Para mais detalhes técnicos, consulte o relatório do projeto.

## Estrutura

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
