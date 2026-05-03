"""
Programa Principal - Sistema de Vendas Paralelo
INE 5645 - Programação Paralela e Distribuída

Autor: [Nome dos alunos]
Data: 2026

Este programa implementa um protótipo de sistema de vendas paralelo,
explorando 3 padrões de projeto para programação concorrente:

1. Producer-Consumer (Produtor-Consumidor)
2. Pipeline (Linha de Montagem)
3. Worker Pool (Pool de Workers)

Usa multiprocessing para verdadeiro paralelismo em múltiplos núcleos.
"""

import sys
import argparse
from pathlib import Path

# Adicionar src ao path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path.parent))

from src.model.config import ConfiguracaoSistema, CONFIG_PADRAO, CONFIG_TESTE, CONFIG_PESADO
from src.controller.orchestrator import OrchestradorSistemaVendas


def exibir_banner():
    """Exibe banner do sistema"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║     SISTEMA DE VENDAS PARALELO - INE 5645                     ║
║     Programação Paralela e Distribuída - UFSC 2026/1          ║
║                                                                ║
║  Padrões de Projeto Paralelo:                                 ║
║  ✓ Producer-Consumer (Clientes → Validação)                   ║
║  ✓ Pipeline (Validação → Financeira → Logística)              ║
║  ✓ Worker Pool (Múltiplos workers por etapa)                  ║
║                                                                ║
║  Arquitetura: MVC                                             ║
║  Linguagem: Python com multiprocessing                        ║
║  Paralelismo: Múltiplos núcleos de processamento              ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
""")


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Sistema de Vendas Paralelo - INE 5645",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
    Exemplos de uso:
        python main.py                    # Usa configuração padrão
        python main.py --teste            # Usa configuração de teste (rápido)
        python main.py --pesado           # Usa configuração pesada (muitos pedidos)
        python main.py --custom 5 3 100   # num_validadores num_financeiros pedidos
        """
    )
    
    # Argumentos
    parser.add_argument(
        '--teste',
        action='store_true',
        help='Usar configuração de teste (rápida)'
    )
    parser.add_argument(
        '--pesado',
        action='store_true',
        help='Usar configuração pesada (muitos pedidos)'
    )
    parser.add_argument(
        '--custom',
        nargs=3,
        type=int,
        metavar=('VAL', 'FIN', 'PED'),
        help='Configuração customizada: num_validadores num_financeiros pedidos_por_cliente'
    )
    parser.add_argument(
        '--log',
        type=str,
        default='sistema_vendas.log',
        help='Arquivo de log (padrão: sistema_vendas.log)'
    )
    
    args = parser.parse_args()
    
    exibir_banner()
    
    # Escolher configuração
    if args.teste:
        config = CONFIG_TESTE
        print("Usando configuração de TESTE (rápida)")
    elif args.pesado:
        config = CONFIG_PESADO
        print("Usando configuração PESADA (muitos pedidos)")
    elif args.custom:
        num_val, num_fin, num_ped = args.custom
        config = ConfiguracaoSistema(
            num_validadores=num_val,
            num_financeiros=num_fin,
            pedidos_por_cliente=num_ped
        )
        print(f"Usando configuração CUSTOMIZADA")
    else:
        config = CONFIG_PADRAO
        print("Usando configuração PADRÃO")
    
    print(f"Log será salvo em: {args.log}\n")
    
    # Criar e executar orquestrador
    orquestrador = OrchestradorSistemaVendas(config)
    
    try:
        # Executar sistema
        orquestrador.executar()
        
        print("\nSistema concluído com sucesso!")
        print(f"Verifique o arquivo 'sistema_vendas.log' para detalhes")
        print(f"Verifique o arquivo 'sistema_vendas.json' para estatísticas\n")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nSistema interrompido pelo usuário")
        return 1
    except Exception as e:
        print(f"\nErro: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == '__main__':
    sys.exit(main())
