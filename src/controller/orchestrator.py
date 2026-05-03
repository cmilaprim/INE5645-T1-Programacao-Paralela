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


class OrchestradorSistemaVendas:
    """
    CONTROLLER - Orquestra todo o sistema paralelo.
    
    Responsabilidades:
    1. Criar as filas de comunicação (Producer-Consumer)
    2. Iniciar todos os processos workers
    3. Coordenar o fluxo do pipeline
    4. Aguardar conclusão
    
    Padrões coordenados:
    - Producer-Consumer: Clientes produzem, validadores consomem
    - Pipeline: 3 estágios paralelos (Validação → Financeira → Logística)
    - Worker Pool: Múltiplos workers em cada estágio
    """
    
    def __init__(self, config: ConfiguracaoSistema = None):
        """
        Inicializa o orquestrador.
        
        Args:
            config: Configuração do sistema (ou padrão se None)
        """
        self.config = config or ConfiguracaoSistema()
        
        # Criar as filas (estrutura de comunicação entre processos)
        # Cada fila é thread-safe e process-safe!
        self.fila_pedidos = Queue()              # Cliente → Validação
        self.fila_validados = Queue()            # Validação → Financeira
        self.fila_aprovados = Queue()            # Financeira → Logística
        
        # Armazenar referências aos processos
        self.processos: List[Process] = []
        
        # Inicializar monitor (View)
        inicializar_monitor()
    
    def iniciar_sistema(self):
        """
        Inicia todos os processos do sistema.
        
        Estrutura de processos:
        
        ┌─ Clientes (1 processo produtor)
        │
        ├─ Validadores (N processes - Worker Pool)
        │
        ├─ Financeiros (N processes - Worker Pool)
        │
        └─ Logísticos (N processes - Worker Pool)
        
        Total de processos paralelos = 1 + N_val + N_fin + N_log
        """
        
        print("\n" + "="*60)
        print("INICIANDO SISTEMA DE VENDAS PARALELO")
        print("="*60)
        
        monitor = obter_monitor()
        print(self.config)
        
        # ═══════════════════════════════════════════════════════════════
        # PRODUTOR: Clientes (Producer-Consumer Pattern)
        # ═══════════════════════════════════════════════════════════════
        print("\n✓ Iniciando produtor (cliente)...")
        for cliente_id in range(self.config.num_clientes):
            p = Process(
                target=cliente_worker,
                args=(cliente_id, self.config, self.fila_pedidos),
                name=f"Cliente-{cliente_id}"
            )
            p.start()
            self.processos.append(p)
            print(f"  → Cliente-{cliente_id} iniciado")
        
        # ═══════════════════════════════════════════════════════════════
        # PIPELINE ESTÁGIO 1: Validadores (Producer-Consumer + Worker Pool)
        # ═══════════════════════════════════════════════════════════════
        print("\n✓ Iniciando validadores (Worker Pool)...")
        for validador_id in range(self.config.num_validadores):
            p = Process(
                target=validador_worker,
                args=(validador_id, self.config, self.fila_pedidos, self.fila_validados),
                name=f"Validador-{validador_id}"
            )
            p.start()
            self.processos.append(p)
            print(f"  → Validador-{validador_id} iniciado")
        
        # ═══════════════════════════════════════════════════════════════
        # PIPELINE ESTÁGIO 2: Financeiros (Consumer + Worker Pool)
        # ═══════════════════════════════════════════════════════════════
        print("\n✓ Iniciando financeiros (Worker Pool)...")
        for financeiro_id in range(self.config.num_financeiros):
            p = Process(
                target=financeiro_worker,
                args=(financeiro_id, self.config, self.fila_validados, self.fila_aprovados),
                name=f"Financeiro-{financeiro_id}"
            )
            p.start()
            self.processos.append(p)
            print(f"  → Financeiro-{financeiro_id} iniciado")
        
        # ═══════════════════════════════════════════════════════════════
        # PIPELINE ESTÁGIO 3: Logísticos (Consumer + Worker Pool)
        # ═══════════════════════════════════════════════════════════════
        print("\n✓ Iniciando logísticos (Worker Pool)...")
        for logistica_id in range(self.config.num_logisticos):
            p = Process(
                target=logistica_worker,
                args=(logistica_id, self.config, self.fila_aprovados),
                name=f"Logistica-{logistica_id}"
            )
            p.start()
            self.processos.append(p)
            print(f"  → Logístico-{logistica_id} iniciado")
        
        print(f"\n{'='*60}")
        print(f"✓ Sistema iniciado com {len(self.processos)} processos paralelos")
        print(f"{'='*60}\n")
    
    def aguardar_conclusao(self):
        """
        Aguarda que todos os processos terminem.
        
        Estratégia:
        1. Aguarda clientes terminarem
        2. Envia sinais de parada (None) nas filas
        3. Aguarda todos os workers terminarem
        """
        monitor = obter_monitor()
        
        print("\n⏳ Aguardando conclusão dos processos...")
        print("   (Isso pode levar alguns segundos)\n")
        
        tempo_inicio = time.time()
        
        # Aguardar produtor terminar
        for p in self.processos:
            if "Cliente" in p.name:
                p.join()
        
        # Enviar sinais de parada (None) para os validadores
        for _ in range(self.config.num_validadores):
            self.fila_pedidos.put(None)
        
        # Aguardar validadores terminarem
        for p in self.processos:
            if "Validador" in p.name:
                p.join()
        
        # Enviar sinais de parada para financeiros
        for _ in range(self.config.num_financeiros):
            self.fila_validados.put(None)
        
        # Aguardar financeiros terminarem
        for p in self.processos:
            if "Financeiro" in p.name:
                p.join()
        
        # Enviar sinais de parada para logísticos
        for _ in range(self.config.num_logisticos):
            self.fila_aprovados.put(None)
        
        # Aguardar logísticos terminarem
        for p in self.processos:
            if "Logistica" in p.name:
                p.join()
        
        tempo_total = time.time() - tempo_inicio
        
        print(f"\n{'='*60}")
        print(f"✓ Todos os processos concluídos em {tempo_total:.2f} segundos")
        print(f"{'='*60}\n")
    
    def parar_sistema(self):
        """Para o sistema interrompendo todos os processos"""
        print("\n⚠️  Parando sistema...")
        for p in self.processos:
            if p.is_alive():
                p.terminate()
                p.join(timeout=2)
                if p.is_alive():
                    p.kill()
        print("✓ Sistema parado")
    
    def executar(self):
        """
        Executa o sistema completo do início ao fim.
        
        Fluxo:
        1. Iniciar todos os workers
        2. Aguardar conclusão
        3. Gerar relatório
        """
        try:
            self.iniciar_sistema()
            self.aguardar_conclusao()
            
            # Gerar relatório
            monitor = obter_monitor()
            monitor.exibir_resumo_final()
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Sistema interrompido pelo usuário")
            self.parar_sistema()
        except Exception as e:
            print(f"\n❌ Erro no sistema: {e}")
            self.parar_sistema()
            raise
    
    def debug_info(self):
        """Exibe informações de debug sobre filas"""
        print("\n" + "="*60)
        print("INFORMAÇÕES DE DEBUG")
        print("="*60)
        print(f"Tamanho fila_pedidos: {self.fila_pedidos.qsize()}")
        print(f"Tamanho fila_validados: {self.fila_validados.qsize()}")
        print(f"Tamanho fila_aprovados: {self.fila_aprovados.qsize()}")
        print(f"Processos ativos: {sum(1 for p in self.processos if p.is_alive())}")
        print("="*60 + "\n")
