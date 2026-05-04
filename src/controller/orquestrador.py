from multiprocessing import Queue, Process
import time
from typing import List

from src.model.config import ConfiguracaoSistema
from src.view.monitor import inicializar_monitor, obter_monitor
from src.workers.workers import (
    cliente_worker,
    validador_worker,
    financeiro_worker,
    logistica_worker
)


class Orquestrador:
    """Orquestra o sistema paralelo"""
    
    def __init__(self, config: ConfiguracaoSistema = None):
        self.config = config or ConfiguracaoSistema()
        self.fila_pedidos = Queue()
        self.fila_validados = Queue()
        self.fila_aprovados = Queue()
        self.processos: List[Process] = []
        inicializar_monitor()
    
    def iniciar_sistema(self):
        """Inicia todos os workers"""
        print("\n" + "="*60)
        print("SISTEMA DE VENDAS PARALELO - INICIANDO")
        print("="*60)
        print(self.config)
        
        #produtores
        print("\nINICIANDO CLIENTES...")
        for cliente_id in range(self.config.num_clientes):
            p = Process(target=cliente_worker, args=(cliente_id, self.config, self.fila_pedidos), name=f"cliente-{cliente_id}")
            p.start()
            self.processos.append(p)
        
        # Validadores
        print("INICIANDO VALIDADORES...")
        for validador_id in range(self.config.num_validadores):
            # Pipeline 
            p = Process(target=validador_worker, args=(validador_id, self.config, self.fila_pedidos, self.fila_validados), name=f"validador-{validador_id}")
            p.start()
            self.processos.append(p)
        
        # Financeiros
        print("INICIANDO FINANCEIROS...")
        for financeiro_id in range(self.config.num_financeiros):
            p = Process(target=financeiro_worker, args=(financeiro_id, self.config, self.fila_validados, self.fila_aprovados), name=f"financeiro-{financeiro_id}")
            p.start()
            self.processos.append(p)
        
        # Logísticos
        print("INICIANDO LOGÍSTICOS...")
        for logistica_id in range(self.config.num_logisticos):
            p = Process(target=logistica_worker, args=(logistica_id, self.config, self.fila_aprovados), name=f"logistica-{logistica_id}")
            p.start()
            self.processos.append(p)
        
        print(f"\n✓ {len(self.processos)} processos iniciados\n")
    
    def aguardar_conclusao(self):
        """Aguarda que todos os processos terminem"""
        print("Aguardando conclusão...\n")
        
        #produtores
        for p in self.processos:
            if "cliente" in p.name:
                p.join()
        
        #sinal de parada para validadores
        for _ in range(self.config.num_validadores):
            self.fila_pedidos.put(None)
        
        #validadores
        for p in self.processos:
            if "validador" in p.name:
                p.join()
        
        #sinal de parada para financeiros
        for _ in range(self.config.num_financeiros):
            self.fila_validados.put(None)
        
        #financeiros
        for p in self.processos:
            if "financeiro" in p.name:
                p.join()
        
        #sinal de parada para logísticos
        for _ in range(self.config.num_logisticos):
            self.fila_aprovados.put(None)
        
        #logísticos
        for p in self.processos:
            if "logistica" in p.name:
                p.join()
        
        print("\n✓ Todos os processos concluídos")
    
    def parar_sistema(self):
        """Para o sistema"""
        print("\nParando sistema...")
        for p in self.processos:
            if p.is_alive():
                p.terminate()
                p.join(timeout=2)
                if p.is_alive():
                    p.kill()
    
    def executar(self):
        """Executa o sistema completo"""
        try:
            self.iniciar_sistema()
            self.aguardar_conclusao()
            
            monitor = obter_monitor()
            monitor.exibir_resumo_final()
            
        except KeyboardInterrupt:
            print("\n\nSistema interrompido")
            self.parar_sistema()
        except Exception as e:
            print(f"\nErro: {e}")
            self.parar_sistema()
            raise
