from datetime import datetime
from multiprocessing import Queue, current_process
from typing import Optional
import os
import random
import time

from src.model.config import ConfiguracaoSistema
from src.model.pedido import Pedido, StatusPedido, criar_pedido
from src.view.monitor import registrar_erro, registrar_evento, registrar_pedido_finalizado


def timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def log(etapa: str, worker_id: int, mensagem: str):
    print(
        f"[{timestamp()}] "
        f"[PID {os.getpid()}] "
        f"[{current_process().name}] "
        f"[{etapa} {worker_id}] "
        f"{mensagem}",
        flush=True
    )

def tempo_processamento(config: ConfiguracaoSistema):
    time.sleep(random.uniform(config.tempo_processamento_min, config.tempo_processamento_max))


def cliente_worker(cliente_id: int, config: ConfiguracaoSistema, fila_saida: Queue, fila_monitor: Optional[Queue] = None):
    try:
        for num_pedido in range(config.pedidos_por_cliente):
            item = random.choice(config.itens_disponiveis)
            nome_cliente = random.choice(config.nomes_clientes)
            valor = round(random.uniform(100, 5000), 2)

            pedido = criar_pedido(cliente_id=f"CLT-{cliente_id:03d}", nome_cliente=nome_cliente, item=item, valor=valor, config=config)

            fila_saida.put(pedido)

            detalhes = (
                f"cliente={pedido.nome_cliente}; item={item}; valor=R$ {valor:.2f}; "
                f"pedido {num_pedido + 1}/{config.pedidos_por_cliente}"
            )
            
            registrar_evento(fila_monitor, etapa="produtor", worker_id=cliente_id, pedido_id=pedido.id, evento="pedido_criado", detalhes=detalhes)
            log("PROD", cliente_id, f"CRIOU pedido {pedido.id} - {detalhes}")

            time.sleep(random.uniform(0.05, 0.15))

        log("PROD", cliente_id, "LIBERADO")

    except Exception as exc:
        registrar_erro(fila_monitor, f"cliente_worker {cliente_id}: {exc!r}")
        log("PROD", cliente_id, f"ERRO: {exc!r}")
        raise


def validador_worker(worker_id: int, config: ConfiguracaoSistema, fila_entrada: Queue, fila_saida: Queue, fila_monitor: Optional[Queue] = None):
    try:
        while True:
            pedido: Pedido = fila_entrada.get()

            if pedido is None:
                break

            log("VAL", worker_id, f"INICIANDO pedido {pedido.id} - {pedido.nome_cliente}")
            registrar_evento(fila_monitor, etapa="validacao", worker_id=worker_id, pedido_id=pedido.id, evento="inicio_validacao")
            
            tempo_processamento(config)

            if random.random() < config.taxa_falha_validacao:
                pedido.atualizar_status(StatusPedido.REJEITADO_VALIDACAO)
                registrar_evento(fila_monitor, etapa="validacao", worker_id=worker_id, pedido_id=pedido.id, evento="pedido_rejeitado_validacao")
                
                registrar_pedido_finalizado(fila_monitor, pedido)
                log("VAL", worker_id, f"FINALIZOU pedido {pedido.id} - REJEITADO")
            else:
                pedido.atualizar_status(StatusPedido.VALIDADO)
                registrar_evento(fila_monitor, etapa="validacao", worker_id=worker_id, pedido_id=pedido.id, evento="pedido_validado")
                fila_saida.put(pedido)
                log("VAL", worker_id, f"FINALIZOU pedido {pedido.id} - OK")

        log("VAL", worker_id, "LIBERADO")

    except Exception as exc:
        registrar_erro(fila_monitor, f"validador_worker {worker_id}: {exc!r}")
        log("VAL", worker_id, f"ERRO: {exc!r}")
        raise


def financeiro_worker(worker_id: int, config: ConfiguracaoSistema, fila_entrada: Queue, fila_saida: Queue, fila_monitor: Optional[Queue] = None):
    try:
        while True:
            pedido: Pedido = fila_entrada.get()

            if pedido is None:
                break

            log("FIN", worker_id, f"INICIANDO pedido {pedido.id}")
            registrar_evento(fila_monitor, etapa="financeiro", worker_id=worker_id, pedido_id=pedido.id, evento="inicio_financeiro")

            tempo_processamento(config)

            if random.random() < config.taxa_falha_financeira:
                pedido.atualizar_status(StatusPedido.REJEITADO_FINANCEIRO)
                registrar_evento(fila_monitor, etapa="financeiro", worker_id=worker_id, pedido_id=pedido.id, evento="pedido_rejeitado_financeiro")
                
                registrar_pedido_finalizado(fila_monitor, pedido)
                log("FIN", worker_id, f"FINALIZOU pedido {pedido.id} - RECUSADO")
            else:
                pedido.atualizar_status(StatusPedido.APROVADO_FINANCEIRO)
                registrar_evento(fila_monitor, etapa="financeiro", worker_id=worker_id, pedido_id=pedido.id, evento="pedido_aprovado_financeiro")
                
                fila_saida.put(pedido)
                log("FIN", worker_id, f"FINALIZOU pedido {pedido.id} - OK")

        log("FIN", worker_id, "LIBERADO")

    except Exception as exc:
        registrar_erro(fila_monitor, f"financeiro_worker {worker_id}: {exc!r}")
        log("FIN", worker_id, f"ERRO: {exc!r}")
        raise


def logistica_worker(worker_id: int, config: ConfiguracaoSistema, fila_entrada: Queue, fila_monitor: Optional[Queue] = None):
    try:
        while True:
            pedido: Pedido = fila_entrada.get()

            if pedido is None:
                break

            log("LOG", worker_id, f"INICIANDO entrega do pedido {pedido.id}")
            registrar_evento(fila_monitor, etapa="logistica", worker_id=worker_id, pedido_id=pedido.id, evento="inicio_logistica")

            tempo_processamento(config)

            if random.random() < config.taxa_falha_logistica:
                pedido.atualizar_status(StatusPedido.FALHA_ENTREGA)
                registrar_evento(fila_monitor, etapa="logistica", worker_id=worker_id, pedido_id=pedido.id, evento="falha_entrega")
                
                log("LOG", worker_id, f"FINALIZOU pedido {pedido.id} - FALHA")
            else:
                pedido.atualizar_status(StatusPedido.ENTREGUE)
                registrar_evento(fila_monitor, etapa="logistica", worker_id=worker_id, pedido_id=pedido.id, evento="pedido_entregue")
                log("LOG", worker_id, f"FINALIZOU pedido {pedido.id} - ENTREGUE")

            registrar_pedido_finalizado(fila_monitor, pedido)

        log("LOG", worker_id, "LIBERADO")

    except Exception as exc:
        registrar_erro(fila_monitor, f"logistica_worker {worker_id}: {exc!r}")
        log("LOG", worker_id, f"ERRO: {exc!r}")
        raise
