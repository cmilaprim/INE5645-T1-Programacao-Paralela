import time
import random
from multiprocessing import Queue, Process
from typing import Callable

from src.model.pedido import Pedido, StatusPedido, criar_pedido
from src.model.config import ConfiguracaoSistema
from src.view.monitor import obter_monitor


# ═══════════════════════════════════════════════════════════════
# PADRÃO 1: PRODUCER-CONSUMER
# Clientes geram pedidos → Fila de Pedidos → Validadores consomem
# ═══════════════════════════════════════════════════════════════

def cliente_worker(cliente_id: int, config: ConfiguracaoSistema, fila_saida: Queue):
    """
    PRODUTOR - Padrão Producer-Consumer
    
    Gera novos pedidos e coloca na fila.
    Simula clientes fazendo compras concorrentemente.
    
    Args:
        cliente_id: Identificador único do cliente
        config: Configuração do sistema
        fila_saida: Fila de pedidos (Producer-Consumer)
    """
    monitor = obter_monitor()
    
    for num_pedido in range(config.pedidos_por_cliente):
        try:
            # Criar novo pedido
            item = random.choice(config.itens_disponiveis)
            valor = round(random.uniform(100, 5000), 2)
            
            pedido = criar_pedido(
                cliente_id=f"CLT-{cliente_id:03d}",
                item=item,
                valor=valor
            )
            
            # Produzir: colocar na fila
            fila_saida.put(pedido)
            
            monitor.registrar_evento(
                etapa="produtor",
                worker_id=cliente_id,
                pedido_id=pedido.id,
                evento="CRIADO",
                detalhes=f"{item} - R${valor:.2f}"
            )
            
            # Simular intervalo entre compras
            tempo_intervalo = random.uniform(0.1, 0.5)
            time.sleep(tempo_intervalo)
            
        except Exception as e:
            monitor.registrar_evento(
                etapa="produtor",
                worker_id=cliente_id,
                pedido_id=f"pedido-{num_pedido}",
                evento="ERRO",
                detalhes=str(e)
            )
    
    monitor.registrar_evento(
        etapa="produtor",
        worker_id=cliente_id,
        pedido_id="FINAL",
        evento="CONCLUÍDO",
        detalhes=f"Gerados {config.pedidos_por_cliente} pedidos"
    )


# ═══════════════════════════════════════════════════════════════
# PADRÃO 2: PIPELINE + PADRÃO 3: WORKER POOL
# Pipeline: Validação → Financeira → Logística (3 estágios)
# Worker Pool: Múltiplos workers em cada estágio
# ═══════════════════════════════════════════════════════════════

def validador_worker(worker_id: int, config: ConfiguracaoSistema, fila_entrada: Queue, fila_saida: Queue):
    """
    CONSUMIDOR 1 - Validação de Pedidos (PIPELINE ESTÁGIO 1 + WORKER POOL)
    
    Padrões aplicados:
    1. Producer-Consumer: Consome da fila_entrada (produzida por Cliente)
    2. Pipeline: Primeiro estágio, passa resultado para próximo estágio
    3. Worker Pool: Múltiplos validadores processam em paralelo (identificados por worker_id)
    
    Args:
        worker_id: Identificador único deste validador
        config: Configuração do sistema
        fila_entrada: Pedidos para validar (Producer-Consumer)
        fila_saida: Pedidos validados (Pipeline)
    """
    monitor = obter_monitor()
    pedidos_processados = 0
    
    while True:
        try:
            # Consumir: pegar da fila
            # timeout evita ficar preso indefinidamente
            pedido: Pedido = fila_entrada.get(timeout=5)
            
            if pedido is None:  # Sinal de parada
                break
            
            tempo_inicio = time.time()
            
            monitor.registrar_evento(
                etapa="validacao",
                worker_id=worker_id,
                pedido_id=pedido.id,
                evento="INICIO",
                detalhes=f"Cliente: {pedido.cliente_id}"
            )
            
            # Simular processamento
            tempo_proc = random.uniform(
                config.tempo_processamento_min,
                config.tempo_processamento_max
            )
            time.sleep(tempo_proc)
            
            # Validar com probabilidade de sucesso
            if random.random() < config.taxa_falha_validacao:
                # FALHA
                pedido.atualizar_status(StatusPedido.REJEITADO_VALIDACAO)
                monitor.registrar_evento(
                    etapa="validacao",
                    worker_id=worker_id,
                    pedido_id=pedido.id,
                    evento="FALHA",
                    detalhes="Dados inválidos"
                )
            else:
                # SUCESSO
                pedido.atualizar_status(StatusPedido.VALIDADO)
                fila_saida.put(pedido)  # Passar para Pipeline
                tempo_decorrido = time.time() - tempo_inicio
                monitor.registrar_tempo_processamento("validacao", tempo_decorrido)
                
                monitor.registrar_evento(
                    etapa="validacao",
                    worker_id=worker_id,
                    pedido_id=pedido.id,
                    evento="SUCESSO",
                    detalhes=f"Tempo: {tempo_decorrido:.2f}s"
                )
            
            pedidos_processados += 1
            
        except Exception as e:
            # timeout da fila - continuar
            if "Empty" not in str(type(e)):
                monitor.registrar_evento(
                    etapa="validacao",
                    worker_id=worker_id,
                    pedido_id="DESCONHECIDO",
                    evento="ERRO",
                    detalhes=str(e)
                )
    
    monitor.registrar_evento(
        etapa="validacao",
        worker_id=worker_id,
        pedido_id="FINAL",
        evento="CONCLUÍDO",
        detalhes=f"Processados {pedidos_processados} pedidos"
    )


def financeiro_worker(worker_id: int, config: ConfiguracaoSistema, fila_entrada: Queue, fila_saida: Queue):
    """
    CONSUMIDOR 2 - Validação Financeira (PIPELINE ESTÁGIO 2 + WORKER POOL)
    
    Padrões aplicados:
    1. Producer-Consumer: Consome da fila_entrada (produzida por Validadores)
    2. Pipeline: Segundo estágio, passa resultado para próximo estágio
    3. Worker Pool: Múltiplos financeiros processam em paralelo (identificados por worker_id)
    
    Args:
        worker_id: Identificador único deste financeiro
        config: Configuração do sistema
        fila_entrada: Pedidos validados (vindo da Validação)
        fila_saida: Pedidos aprovados financeiramente (Pipeline)
    """
    monitor = obter_monitor()
    pedidos_processados = 0
    
    while True:
        try:
            pedido: Pedido = fila_entrada.get(timeout=5)
            
            if pedido is None or pedido.status == StatusPedido.REJEITADO_VALIDACAO:
                # Pular pedidos rejeitados
                if pedido is None:
                    break
                continue
            
            tempo_inicio = time.time()
            
            monitor.registrar_evento(
                etapa="financeira",
                worker_id=worker_id,
                pedido_id=pedido.id,
                evento="INICIO",
                detalhes=f"Valor: R${pedido.valor:.2f}"
            )
            
            # Simular processamento
            tempo_proc = random.uniform(
                config.tempo_processamento_min,
                config.tempo_processamento_max
            )
            time.sleep(tempo_proc)
            
            # Validar com probabilidade de sucesso
            if random.random() < config.taxa_falha_financeira:
                # FALHA
                pedido.atualizar_status(StatusPedido.REJEITADO_FINANCEIRO)
                monitor.registrar_evento(
                    etapa="financeira",
                    worker_id=worker_id,
                    pedido_id=pedido.id,
                    evento="FALHA",
                    detalhes="Cartão recusado"
                )
            else:
                # SUCESSO
                pedido.atualizar_status(StatusPedido.APROVADO_FINANCEIRO)
                fila_saida.put(pedido)  # Passar para Pipeline
                tempo_decorrido = time.time() - tempo_inicio
                monitor.registrar_tempo_processamento("financeira", tempo_decorrido)
                
                monitor.registrar_evento(
                    etapa="financeira",
                    worker_id=worker_id,
                    pedido_id=pedido.id,
                    evento="SUCESSO",
                    detalhes=f"Tempo: {tempo_decorrido:.2f}s"
                )
            
            pedidos_processados += 1
            
        except Exception as e:
            if "Empty" not in str(type(e)):
                monitor.registrar_evento(
                    etapa="financeira",
                    worker_id=worker_id,
                    pedido_id="DESCONHECIDO",
                    evento="ERRO",
                    detalhes=str(e)
                )
    
    monitor.registrar_evento(
        etapa="financeira",
        worker_id=worker_id,
        pedido_id="FINAL",
        evento="CONCLUÍDO",
        detalhes=f"Processados {pedidos_processados} pedidos"
    )


def logistica_worker(worker_id: int, config: ConfiguracaoSistema, fila_entrada: Queue):
    """
    CONSUMIDOR 3 - Logística e Entrega (PIPELINE ESTÁGIO 3 + WORKER POOL)
    
    Padrões aplicados:
    1. Producer-Consumer: Consome da fila_entrada (produzida por Financeiros)
    2. Pipeline: Terceiro e final estágio do pipeline
    3. Worker Pool: Múltiplos logísticos processam em paralelo (identificados por worker_id)
    
    Args:
        worker_id: Identificador único deste logístico
        config: Configuração do sistema
        fila_entrada: Pedidos aprovados (vindo de Financeira)
    """
    monitor = obter_monitor()
    pedidos_processados = 0
    
    while True:
        try:
            pedido: Pedido = fila_entrada.get(timeout=5)
            
            if pedido is None or pedido.status != StatusPedido.APROVADO_FINANCEIRO:
                if pedido is None:
                    break
                continue
            
            tempo_inicio = time.time()
            
            monitor.registrar_evento(
                etapa="logistica",
                worker_id=worker_id,
                pedido_id=pedido.id,
                evento="INICIO",
                detalhes=f"Item: {pedido.item}"
            )
            
            # Simular processamento
            tempo_proc = random.uniform(
                config.tempo_processamento_min,
                config.tempo_processamento_max
            )
            time.sleep(tempo_proc)
            
            # Validar com probabilidade de sucesso
            if random.random() < config.taxa_falha_logistica:
                # FALHA
                pedido.atualizar_status(StatusPedido.FALHA_ENTREGA)
                monitor.registrar_evento(
                    etapa="logistica",
                    worker_id=worker_id,
                    pedido_id=pedido.id,
                    evento="FALHA",
                    detalhes="Avaria na entrega"
                )
            else:
                # SUCESSO
                pedido.atualizar_status(StatusPedido.ENTREGUE)
                tempo_decorrido = time.time() - tempo_inicio
                monitor.registrar_tempo_processamento("logistica", tempo_decorrido)
                
                monitor.registrar_evento(
                    etapa="logistica",
                    worker_id=worker_id,
                    pedido_id=pedido.id,
                    evento="SUCESSO",
                    detalhes=f"Entregue! Tempo: {tempo_decorrido:.2f}s"
                )
            
            pedidos_processados += 1
            
        except Exception as e:
            if "Empty" not in str(type(e)):
                monitor.registrar_evento(
                    etapa="logistica",
                    worker_id=worker_id,
                    pedido_id="DESCONHECIDO",
                    evento="ERRO",
                    detalhes=str(e)
                )
    
    monitor.registrar_evento(
        etapa="logistica",
        worker_id=worker_id,
        pedido_id="FINAL",
        evento="CONCLUÍDO",
        detalhes=f"Processados {pedidos_processados} pedidos"
    )
