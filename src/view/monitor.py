import json
from datetime import datetime
from threading import Lock
from collections import defaultdict
import os


class MonitorSistema:
    """Monitor de estatísticas"""
    
    def __init__(self, arquivo_log: str = None):
        self.arquivo_log = arquivo_log or "sistema_vendas.log"
        self.arquivo_pedidos = "pedidos_temporario.jsonl"
        self.lock = Lock()
        self.timestamp_inicio = datetime.now()
        self.pedidos_status = defaultdict(int)
        self.inicializar_arquivo()
    
    def inicializar_arquivo(self):
        """Cria arquivo de log"""
        with open(self.arquivo_log, 'w') as f:
            f.write(f"SISTEMA DE VENDAS - Iniciado em {self.timestamp_inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
        # Limpar arquivo temporário de pedidos
        if os.path.exists(self.arquivo_pedidos):
            os.remove(self.arquivo_pedidos)
    
    def registrar_evento(self, etapa: str, worker_id: int, pedido_id: str, evento: str, detalhes: str = ""):
        """Registra eventos (simplificado)"""
        with self.lock:
            with open(self.arquivo_log, 'a') as f:
                f.write(f"[{etapa.upper()}] Worker-{worker_id}: {pedido_id} - {evento}\n")
    
    def registrar_pedido(self, pedido):
        """Registra um pedido finalizado em arquivo JSONL"""
        with open(self.arquivo_pedidos, 'a') as f:
            json.dump(pedido.para_dict(), f)
            f.write('\n')
    
    def gerar_relatorio_final(self) -> dict:
        """Gera relatório final simples"""
        tempo_total = (datetime.now() - self.timestamp_inicio).total_seconds()
        
        # Ler pedidos do arquivo JSONL
        pedidos_lista = []
        if os.path.exists(self.arquivo_pedidos):
            with open(self.arquivo_pedidos, 'r') as f:
                for linha in f:
                    if linha.strip():
                        pedidos_lista.append(json.loads(linha))
        
        return {
            'tempo_total_segundos': tempo_total,
            'timestamp_inicio': self.timestamp_inicio.isoformat(),
            'timestamp_fim': datetime.now().isoformat(),
            'total_pedidos': len(pedidos_lista),
            'pedidos': pedidos_lista,
        }
    
    def exibir_resumo_final(self):
        """Exibe resumo final"""
        relatorio = self.gerar_relatorio_final()
        tempo_total = relatorio['tempo_total_segundos']
        
        print("\n" + "="*60)
        print("SISTEMA CONCLUÍDO")
        print("="*60)
        print(f"Tempo total: {tempo_total:.2f} segundos")
        print(f"Log salvo em: {self.arquivo_log}")
        print("="*60 + "\n")
        
        # Salvar JSON
        arquivo_json = self.arquivo_log.replace('.log', '.json')
        with open(arquivo_json, 'w') as f:
            json.dump(relatorio, f, indent=2)
        
        return relatorio


monitor_global = None

def inicializar_monitor(arquivo_log: str = None) -> MonitorSistema:
    """Inicializa o monitor global"""
    global monitor_global
    monitor_global = MonitorSistema(arquivo_log)
    return monitor_global


def obter_monitor() -> MonitorSistema:
    """Obtém a instância global do monitor"""
    global monitor_global
    if monitor_global is None:
        monitor_global = MonitorSistema()
    return monitor_global
