"""
Workers: Processadores de pedidos
Padrões: Producer-Consumer, Pipeline, Worker Pool
"""

import time
import random
from datetime import datetime
from multiprocessing import Queue
from src.model.pedido import Pedido, StatusPedido, criar_pedido
from src.model.config import ConfiguracaoSistema
from src.view.monitor import obter_monitor


def timestamp():
    """Retorna timestamp com milissegundos"""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def cliente_worker(cliente_id: int, config: ConfiguracaoSistema, fila_saida: Queue):
    """produz pedidos e coloca na fila"""
    
    for num_pedido in range(config.pedidos_por_cliente):
        item = random.choice(config.itens_disponiveis)
        valor = round(random.uniform(100, 5000), 2)
        
        pedido = criar_pedido(cliente_id=f"CLT-{cliente_id:03d}", item=item, valor=valor, config=config)
        
        fila_saida.put(pedido)
        
        print(f"[{timestamp()}] [INICIANDO [PROD {cliente_id}]] - {pedido.nome_cliente} {pedido.id} ({item})")
        time.sleep(random.uniform(0.05, 0.15))
    
    print(f"[{timestamp()}] [PROD {cliente_id}] LIBERADO")


def validador_worker(worker_id: int, config: ConfiguracaoSistema, fila_entrada: Queue, fila_saida: Queue):
    """valida pedidos - estágio 1, consome da fila de entrada e produz na fila de saída"""
    
    while True:
        try:
            pedido: Pedido = fila_entrada.get(timeout=3)
            
            if pedido is None:
                break
            
            print(f"[{timestamp()}]   [INICIANDO [VAL {worker_id}]]: {pedido.id} - {pedido.nome_cliente}")
            
            #simula o tempo de processamento, cada worker "trabalha" por um tempo, depois processa o próximo pedido
            time.sleep(random.uniform(config.tempo_processamento_min, config.tempo_processamento_max))
            
            #falha ou sucesso
            if random.random() < config.taxa_falha_validacao:
                pedido.atualizar_status(StatusPedido.REJEITADO_VALIDACAO)
                print(f"[{timestamp()}]   [FINALIZAÇÃO [VAL {worker_id}]]: {pedido.id} REJEITADO")
            else:
                pedido.atualizar_status(StatusPedido.VALIDADO)
                fila_saida.put(pedido)
                print(f"[{timestamp()}]   [FINALIZAÇÃO [VAL {worker_id}]]: {pedido.id} OK")
        
        except Exception:
            pass
    
    print(f"[{timestamp()}]   [VAL {worker_id}]] LIBERADO")


def financeiro_worker(worker_id: int, config: ConfiguracaoSistema, fila_entrada: Queue, fila_saida: Queue):
    """valida financeiramente - estágio 2, consome da fila de entrada e produz na fila de saída"""
    
    while True:
        try:
            pedido: Pedido = fila_entrada.get(timeout=3)
            
            if pedido is None:
                break
        
            print(f"[{timestamp()}]     [INICIANDO [FIN {worker_id}]]: {pedido.id}")
            
            #simula o tempo de processamento
            time.sleep(random.uniform(config.tempo_processamento_min, config.tempo_processamento_max))
            
            #falha ou sucesso
            if random.random() < config.taxa_falha_financeira:
                pedido.atualizar_status(StatusPedido.REJEITADO_FINANCEIRO)
                print(f"[{timestamp()}]     [FINALIZAÇÃO [FIN {worker_id}]]: {pedido.id} RECUSADO")
            else:
                pedido.atualizar_status(StatusPedido.APROVADO_FINANCEIRO)
                fila_saida.put(pedido)
                print(f"[{timestamp()}]     [FINALIZAÇÃO [FIN {worker_id}]]: {pedido.id} OK")
        
        except Exception:
            pass
    
    print(f"[{timestamp()}]     [FIN {worker_id}] LIBERADO")


def logistica_worker(worker_id: int, config: ConfiguracaoSistema, fila_entrada: Queue):
    """entrega pedidos - estágio 3, consome da fila de entrada"""
    
    monitor = obter_monitor()
    
    while True:
        try:
            pedido: Pedido = fila_entrada.get(timeout=3)
            if pedido is None:
                break
            
            print(f"[{timestamp()}]       [INICIANDO ENTREGA PELO [LOG {worker_id}]]: {pedido.id}")
            
            #simula o tempo de processamento
            time.sleep(random.uniform(config.tempo_processamento_min, config.tempo_processamento_max))
            
            #falha ou sucesso
            if random.random() < config.taxa_falha_logistica:
                pedido.atualizar_status(StatusPedido.FALHA_ENTREGA)
                print(f"[{timestamp()}]       [FINALIZAÇÃO [LOG {worker_id}]]: {pedido.id} FALHA")
            else:
                pedido.atualizar_status(StatusPedido.ENTREGUE)
                print(f"[{timestamp()}]       [FINALIZAÇÃO [LOG {worker_id}]]: {pedido.id} ENTREGUE")
            
            monitor.registrar_pedido(pedido)
        
        except Exception:
            pass
    
    print(f"[{timestamp()}]       [LOG {worker_id}] LIBERADO")
