from __future__ import annotations
import argparse
import copy
from multiprocessing import freeze_support

from src.controller.orquestrador import Orquestrador
from src.model.config import CONFIG_PADRAO, CONFIG_PESADO, CONFIG_TESTE


CONFIGURACOES = {
    "padrao": CONFIG_PADRAO,
    "teste": CONFIG_TESTE,
    "pesado": CONFIG_PESADO,
}


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Executa o sistema de vendas paralelo."
    )
    parser.add_argument(
        "--config",
        choices=CONFIGURACOES.keys(),
        default="padrao",
        help="Configuracao base para executar.",
    )
    parser.add_argument("--clientes", type=int, default=None)
    parser.add_argument("--pedidos-por-cliente", type=int, default=None)
    parser.add_argument("--validadores", type=int, default=None)
    parser.add_argument("--financeiros", type=int, default=None)
    parser.add_argument("--logisticos", type=int, default=None)
    parser.add_argument("--tamanho-fila", type=int, default=None)
    parser.add_argument("--falha-validacao", type=float, default=None)
    parser.add_argument("--falha-financeira", type=float, default=None)
    parser.add_argument("--falha-logistica", type=float, default=None)
    parser.add_argument("--tempo-min", type=float, default=None)
    parser.add_argument("--tempo-max", type=float, default=None)
    parser.add_argument("--arquivo-log", type=str, default=None)
    return parser


def aplicar_sobrescritas(config, args):
    sobrescritas = {
        "num_clientes": args.clientes,
        "pedidos_por_cliente": args.pedidos_por_cliente,
        "num_validadores": args.validadores,
        "num_financeiros": args.financeiros,
        "num_logisticos": args.logisticos,
        "tamanho_fila": args.tamanho_fila,
        "taxa_falha_validacao": args.falha_validacao,
        "taxa_falha_financeira": args.falha_financeira,
        "taxa_falha_logistica": args.falha_logistica,
        "tempo_processamento_min": args.tempo_min,
        "tempo_processamento_max": args.tempo_max,
        "arquivo_log": args.arquivo_log,
    }

    for atributo, valor in sobrescritas.items():
        if valor is not None:
            setattr(config, atributo, valor)

    if hasattr(config, "_validar"):
        config._validar()

    return config


def main() -> None:
    args = criar_parser().parse_args()
    config = copy.deepcopy(CONFIGURACOES[args.config])
    config = aplicar_sobrescritas(config, args)
    Orquestrador(config).executar()


if __name__ == "__main__":
    freeze_support()
    main()
