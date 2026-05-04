import sys
import argparse
from pathlib import Path

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path.parent))

from src.model.config import ConfiguracaoSistema, CONFIG_PADRAO, CONFIG_TESTE, CONFIG_PESADO
from src.controller.orquestrador import Orquestrador


def main():
    parser = argparse.ArgumentParser(
        description="Sistema de Vendas Paralelo - INE 5645",
        epilog="Exemplos:\n  python main.py\n  python main.py --teste\n  python main.py --pesado"
    )
    
    parser.add_argument('--teste', action='store_true', help='configuração rápida para testes')
    parser.add_argument('--pesado', action='store_true', help='configuração com muitos pedidos')
    
    args = parser.parse_args()
    
    if args.teste:
        config = CONFIG_TESTE
        print("\n Usando configuração TESTE (rápida)")
    elif args.pesado:
        config = CONFIG_PESADO
        print("\n Usando configuração PESADA")
    else:
        config = CONFIG_PADRAO
        print("\n Usando configuração PADRÃO")
    
    print(config)
    
    #inicializa o orquestrador passando a config que será usada
    orquestrador = Orquestrador(config)
    
    try:
        orquestrador.executar()
        print("✓ Sistema concluído com sucesso!\n")
        return 0
        
    except KeyboardInterrupt:
        print("\n Sistema interrompido pelo usuário\n")
        return 1
    except Exception as e:
        print(f"\n Erro: {e}\n")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == '__main__':
    sys.exit(main())
