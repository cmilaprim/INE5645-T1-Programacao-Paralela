from multiprocessing import Process, Queue
from typing import List

from src.model.config import ConfiguracaoSistema
from src.view.monitor import MonitorSistema
from src.workers.workers import cliente_worker, financeiro_worker, logistica_worker, validador_worker

class Orquestrador:
    def __init__(self, config: ConfiguracaoSistema = None):
        self.config = config or ConfiguracaoSistema()

        self.fila_pedidos = Queue(maxsize=self.config.tamanho_fila)
        self.fila_validados = Queue(maxsize=self.config.tamanho_fila)
        self.fila_aprovados = Queue(maxsize=self.config.tamanho_fila)
        self.monitor = MonitorSistema(arquivo_log=self.config.arquivo_log, total_esperado=self.config.total_pedidos_esperados())
        self.fila_monitor = self.monitor.fila_eventos
        self.processos: List[Process] = []

    def iniciar_sistema(self):
        print("SISTEMA DE VENDAS PARALELO - INICIANDO")
        print(self.config)

        self.monitor.iniciar()

        print("\nINICIANDO CLIENTES...")
        for cliente_id in range(self.config.num_clientes):
            p = Process(target=cliente_worker, args=(cliente_id, self.config, self.fila_pedidos, self.fila_monitor), name=f"cliente-{cliente_id}")
            p.start()
            self.processos.append(p)

        print("INICIANDO VALIDADORES...")
        for validador_id in range(self.config.num_validadores):
            p = Process(target=validador_worker, args=(validador_id, self.config, self.fila_pedidos, self.fila_validados, self.fila_monitor), name=f"validador-{validador_id}")
            p.start()
            self.processos.append(p)

        print("INICIANDO FINANCEIROS...")
        for financeiro_id in range(self.config.num_financeiros):
            p = Process(target=financeiro_worker, args=(financeiro_id, self.config, self.fila_validados, self.fila_aprovados, self.fila_monitor), name=f"financeiro-{financeiro_id}")
            p.start()
            self.processos.append(p)

        print("INICIANDO LOGÍSTICOS...")
        for logistica_id in range(self.config.num_logisticos):
            p = Process(target=logistica_worker, args=(logistica_id, self.config, self.fila_aprovados, self.fila_monitor), name=f"logistica-{logistica_id}")
            p.start()
            self.processos.append(p)

        
        print(f"\n{len(self.processos)} processos de trabalho iniciados")
        print("Monitor iniciado\n")

    def processos_por_nome(self, prefixo: str) -> List[Process]:
        return [p for p in self.processos if p.name.startswith(prefixo)]

    def join_e_verificar(self, prefixo: str):
        for p in self.processos_por_nome(prefixo):
            p.join()
            if p.exitcode != 0:
                raise RuntimeError(f"Processo {p.name} terminou com erro. exitcode={p.exitcode}")

    def aguardar_conclusao(self):
        print("Aguardando conclusão...\n")

        self.join_e_verificar("cliente")

        for _ in range(self.config.num_validadores):
            self.fila_pedidos.put(None)
        self.join_e_verificar("validador")

        for _ in range(self.config.num_financeiros):
            self.fila_validados.put(None)
        self.join_e_verificar("financeiro")

        for _ in range(self.config.num_logisticos):
            self.fila_aprovados.put(None)
        self.join_e_verificar("logistica")

        print("\nTodos os processos de trabalho concluídos")

    def parar_sistema(self):
        print("\nParando sistema...")
        for p in self.processos:
            if p.is_alive():
                p.terminate()
                p.join(timeout=2)
                if p.is_alive():
                    p.kill()

        if self.monitor is not None:
            self.monitor.parar_forcado()

    def executar(self):
        try:
            self.iniciar_sistema()
            self.aguardar_conclusao()
            self.monitor.finalizar()
            self.monitor.exibir_resumo_final()

        except KeyboardInterrupt:
            print("\n\nSistema interrompido")
            self.parar_sistema()
            self.monitor.parar_forcado()
            raise
        except Exception as e:
            print(f"\nErro: {e}")
            self.parar_sistema()
            self.monitor.parar_forcado()
            raise
