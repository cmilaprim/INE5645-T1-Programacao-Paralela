# Guia de Instalação e Execução

## 📋 Requisitos

- **Python**: 3.7 ou superior
- **SO**: Linux, macOS ou Windows
- **Dependências**: Nenhuma (apenas biblioteca padrão Python)

Verificar versão:
```bash
python3 --version
```

## 🔧 Instalação

### Passo 1: Navegar ao diretório
```bash
cd "INE5645 - T1 - Programacao Concorrente"
```

### Passo 2: Verificar estrutura
```bash
ls -la  # Linux/macOS
dir     # Windows
```

Deve mostrar: `main.py`, `src/`, `README.md`

### Passo 3: Nenhuma instalação de dependências necessária!

Este projeto usa apenas a biblioteca padrão Python:
- `multiprocessing` - Paralelismo real
- `time` - Medição de tempo
- `random` - Simulação
- `json` - Relatórios
- `dataclasses` - Estruturas de dados

## 🚀 Execução

### Modo Teste (Recomendado para Validação)
```bash
python3 main.py --teste
```
- Rápido (~5 segundos)
- 10 pedidos
- 2 validadores, 1 financeiro, 1 logístico
- Ideal para verificar se tudo funciona

**Resultado esperado**:
```
╔════════════════════════════════════════════════════════════════╗
║     SISTEMA DE VENDAS PARALELO - INE 5645                     ║
...
✓ Usando configuração de TESTE (rápida)
✓ Iniciando produtor (cliente)...
[eventos sendo processados]
✓ Todos os processos concluídos em X.XX segundos
✅ Sistema concluído com sucesso!
```

### Modo Padrão
```bash
python3 main.py
```
- Tempo: ~15-30 segundos
- 50 pedidos
- 3 validadores, 2 financeiros, 2 logísticos

### Modo Pesado (para teste de escalabilidade)
```bash
python3 main.py --pesado
```
- Tempo: ~30-60 segundos
- 200 pedidos
- 5 validadores, 4 financeiros, 3 logísticos

### Modo Customizado
```bash
python3 main.py --custom NUM_VAL NUM_FIN NUM_PED
```

Exemplo:
```bash
python3 main.py --custom 4 2 75
# 4 validadores, 2 financeiros, 75 pedidos
```

## 📊 Saídas Geradas

Após cada execução:

1. **`sistema_vendas.log`** (5-10 KB)
   - Arquivo de texto com todos os eventos
   - Timestamp de cada operação
   - Status (CRIADO, INICIO, SUCESSO, FALHA)

2. **`sistema_vendas.json`** (1-5 KB)
   - Relatório estruturado em JSON
   - Estatísticas de tempo e sucesso/falha
   - Fácil de processar com ferramentas

### Analisar Resultados

Ver log completo:
```bash
cat sistema_vendas.log
```

Ver últimas linhas:
```bash
tail -50 sistema_vendas.log
```

Ver JSON formatado:
```bash
python3 -c "import json; print(json.dumps(json.load(open('sistema_vendas.json')), indent=2))"
```

Ou com `jq` (se instalado):
```bash
jq . sistema_vendas.json
```

## 🐛 Troubleshooting

### Problema: "ModuleNotFoundError: No module named 'src'"
**Solução**: Verifique que está no diretório correto:
```bash
pwd  # Mostrar diretório atual
# Deve ser: /home/camila/INE5645 - T1 - Programacao Concorrente
```

### Problema: "Permission denied"
**Solução** (Linux/macOS):
```bash
chmod +x main.py
python3 main.py --teste
```

### Problema: Processamento muito lento
**Solução**: Reduzir tempos de processamento em `src/model/config.py`:
```python
CONFIG_TESTE = ConfiguracaoSistema(
    tempo_processamento_min=0.01,  # Reduzir
    tempo_processamento_max=0.1
)
```

### Problema: Muitos workers causam erro
**Solução**: Reduzir número de workers:
```bash
python3 main.py --custom 2 1 20
```

### Problema: "Queue.get() timed out"
**Normal em máquinas lentas** - não é erro, apenas timeout. Sistema continua.

## ✅ Validação de Sucesso

Você deve ver:
1. ✓ Banner inicial com informações
2. ✓ Processos sendo iniciados
3. ✓ Eventos sendo processados em tempo real
4. ✓ Resumo final com estatísticas
5. ✓ Arquivos de saída criados

## 📈 Análise de Performance

Compare execuções com diferentes configurações:

```bash
# Teste 1: Poucos workers
python3 main.py --custom 1 1 50
# Anotar tempo em sistema_vendas.json

# Teste 2: Mais workers
python3 main.py --custom 3 2 50
# Anotar tempo

# Teste 3: Muitos workers
python3 main.py --custom 5 4 50
# Anotar tempo
```

**Esperado**: Mais workers = tempo total menor (até limite de CPU)

## 💾 Limpeza

Remover arquivos de log antigos:
```bash
rm -f sistema_vendas.log sistema_vendas.json
```

## 🔍 Debug

Para execução mais verbosa:
```bash
python3 main.py --teste 2>&1 | tee debug.log
```

Isso salva toda a saída em `debug.log`

## 📞 Problemas?

Se encontrar erros:
1. Verificar que Python 3.7+ está instalado: `python3 --version`
2. Verificar estrutura de diretórios: `ls -la src/`
3. Verificar permissões: `ls -la main.py`
4. Ver logs completos: `cat sistema_vendas.log`

---

**Última atualização**: 03 de maio de 2026
