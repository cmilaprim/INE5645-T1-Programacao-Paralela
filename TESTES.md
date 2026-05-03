# Testes e Validação

## 🧪 Teste 1: Validação Rápida (Comece aqui!)

```bash
cd "INE5645 - T1 - Programacao Concorrente"
python3 main.py --teste
```

**Tempo esperado**: 5-10 segundos

**Deve exibir**:
```
╔════════════════════════════════════════════════════════════════╗
║     SISTEMA DE VENDAS PARALELO - INE 5645                     ║
...
✓ Sistema iniciado com 7 processos paralelos
[eventos sendo processados]
✓ Todos os processos concluídos em X.XX segundos
✅ Sistema concluído com sucesso!
```

**Verificações**:
- [ ] Nenhum erro ("Traceback")
- [ ] Eventos sendo processados (CRIADO, INICIO, SUCESSO, FALHA)
- [ ] Arquivo `sistema_vendas.log` criado
- [ ] Arquivo `sistema_vendas.json` criado

---

## 🧪 Teste 2: Configuração Padrão

```bash
python3 main.py
```

**Configuração**: 50 pedidos, 3 validadores, 2 financeiros, 2 logísticos
**Tempo esperado**: 15-30 segundos

**Verificar resultado**:
```bash
# Ver estatísticas
cat sistema_vendas.json | python3 -m json.tool

# Contar sucessos/falhas
grep "SUCESSO" sistema_vendas.log | wc -l
grep "FALHA" sistema_vendas.log | wc -l
```

---

## 🧪 Teste 3: Carga Pesada

```bash
python3 main.py --pesado
```

**Configuração**: 200 pedidos, 5 validadores, 4 financeiros, 3 logísticos
**Tempo esperado**: 30-60 segundos

Demonstra escalabilidade do sistema.

---

## 🧪 Teste 4: Comparação de Performance

Testar com diferentes números de workers:

```bash
# Teste A: Poucos workers
rm -f sistema_vendas.*
python3 main.py --custom 1 1 50
echo "Tempo (1 val, 1 fin):" && grep "tempo_total" sistema_vendas.json

# Teste B: Médio
rm -f sistema_vendas.*
python3 main.py --custom 3 2 50
echo "Tempo (3 val, 2 fin):" && grep "tempo_total" sistema_vendas.json

# Teste C: Muitos
rm -f sistema_vendas.*
python3 main.py --custom 5 3 50
echo "Tempo (5 val, 3 fin):" && grep "tempo_total" sistema_vendas.json
```

**Esperado**: Tempo diminui até atingir limite (mais workers = mais rápido, até saturation)

---

## 📊 Análise de Resultados

### Verificar Eventos Processados

```bash
# Total de eventos
grep -c "CRIADO\|INICIO\|SUCESSO\|FALHA" sistema_vendas.log

# Sucessos por etapa
echo "Validação:" && grep "VALIDACAO.*SUCESSO" sistema_vendas.log | wc -l
echo "Financeira:" && grep "FINANCEIRA.*SUCESSO" sistema_vendas.log | wc -l
echo "Logística:" && grep "LOGISTICA.*SUCESSO" sistema_vendas.log | wc -l

# Falhas por etapa
echo "Validação falhas:" && grep "VALIDACAO.*FALHA" sistema_vendas.log | wc -l
echo "Financeira falhas:" && grep "FINANCEIRA.*FALHA" sistema_vendas.log | wc -l
echo "Logística falhas:" && grep "LOGISTICA.*FALHA" sistema_vendas.log | wc -l
```

### Interpretar JSON

```json
{
  "tempo_total_segundos": 4.58,              // Tempo de execução total
  "timestamp_inicio": "2026-05-03T16:23:36", // Quando começou
  "pedidos_processados": {
    "validacao_sucesso": 9,                  // Passaram validação
    "validacao_falha": 1,                    // Falharam validação
    "financeira_sucesso": 9,                 // Aprovados financeiramente
    "financeira_falha": 0,                   // Rejeitados financeiramente
    "logistica_sucesso": 9                   // Entregues
  },
  "tempos_por_etapa": {
    "validacao": {
      "minimo": 0.11,      // Pedido mais rápido: 0.11s
      "maximo": 0.43,      // Pedido mais lento: 0.43s
      "media": 0.273,      // Tempo médio: 0.273s
      "total": 2.46,       // Tempo total gasto (todos validadores juntos)
      "count": 9           // Número de pedidos processados
    },
    // ... financeira e logistica
  }
}
```

---

## ✅ Checklist de Sucesso

- [ ] Teste rápido completa sem erros
- [ ] Arquivos de log e JSON criados
- [ ] Número de pedidos processados bate com esperado
- [ ] Taxa de falha próxima à configurada (±variação)
- [ ] Tempos por etapa são razoáveis
- [ ] Modo customizado funciona

---

## 🎯 Casos de Uso para Relatório

### Caso 1: Performance Escalável
```bash
# Mostrar que mais workers = melhor performance
python3 main.py --custom 1 1 100  # Benchmark lento
python3 main.py --custom 5 3 100  # Benchmark rápido
# Comparar tempos no relatório
```

### Caso 2: Confiabilidade
```bash
# Verificar se taxas de falha correspondem à configuração
python3 main.py --teste
# Taxa falha validação: esperado ~10%
# Taxa falha financeira: esperado ~15%
# Taxa falha logística: esperado ~5%
```

### Caso 3: Balanceamento de Carga
```bash
# Ver se workers processam equitativamente
tail -100 sistema_vendas.log | grep "SUCESSO" | cut -d' ' -f7 | sort | uniq -c
# Deve mostrar distribuição equilibrada entre workers
```

---

## 📈 Gráficos para Incluir no Relatório

### Gráfico 1: Throughput vs Workers

```
Tempo de Execução (segundos)
^
|    
30 |●
   |  ●●
20 |      ●●
   |         ●●●
10 |             ●●●●
   |__________________|
   1    3    5    7    9  (número de workers)
```

### Gráfico 2: Taxa de Sucesso por Etapa

```
Sucesso (%)
^
|
100|●
   |      ●●
 90|
   |
 80|
   |______|
  Validação  Financeira  Logística
```

### Gráfico 3: Distribuição de Tempo

```
Tempo (segundos)
^
|  ▓
|  ▓  ░
|  ▓  ░ ▒
|  ▓  ░ ▒ 
|__|▓__|░__|▒__
   Val  Fin  Log
   (Validation, Financial, Logistics)
```

---

## 🚨 Possíveis Desvios (Normal!)

- **Tempos variam**: Cada execução é diferente (simulação)
- **Taxa falha não é exata**: São probabilidades
- **Performance varia**: Depende da máquina
- **Ordem dos pedidos varia**: Processamento paralelo não é determinístico

---

## 📝 Exemplo de Execução Completa

```bash
# 1. Preparar
cd "INE5645 - T1 - Programacao Concorrente"
rm -f sistema_vendas.*

# 2. Executar
python3 main.py --teste

# 3. Analisar
echo "=== LOG COMPLETO ==="
head -30 sistema_vendas.log

echo "=== ESTATÍSTICAS ==="
python3 -c "import json; print(json.dumps(json.load(open('sistema_vendas.json')), indent=2))"

echo "=== RESUMO ==="
echo "Total eventos:" $(grep -c "SUCESSO\|FALHA" sistema_vendas.log)
echo "Sucessos validação:" $(grep "VALIDACAO.*SUCESSO" sistema_vendas.log | wc -l)
echo "Sucessos entrega:" $(grep "LOGISTICA.*SUCESSO" sistema_vendas.log | wc -l)
```

---

**Última atualização**: 03 de maio de 2026
