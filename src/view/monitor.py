"""
View: Monitor e Logs do Sistema
Padrão: MVC - View
Autor: [Nome dos alunos]
"""

import sys
from datetime import datetime
from threading import Lock
from typing import Dict, List
from collections import defaultdict
import json


class MonitorSistema:
    """
    Monitora e exibe o status do sistema em tempo real.
    
    Thread-safe para ser chamado de múltiplos processos.
    Padrão Observer implícito: Cada worker atualiza o monitor.
    """
    
    def __init__(self, arquivo_log: str = None):
        self.arquivo_log = arquivo_log or "sistema_vendas.log"
        self.lock = Lock()
        
        # Estatísticas
        self.pedidos_processados = defaultdict(int)  # {'validado': 5, 'rejeitado': 2, ...}
        self.tempo_etapas = defaultdict(list)         # {'validacao': [1.5, 2.0, ...], ...}
        self.timestamp_inicio = datetime.now()
        
        self._inicializar_arquivo()
    
    def _inicializar_arquivo(self):
        """Cria arquivo de log e escreve cabeçalho"""
        with open(self.arquivo_log, 'w') as f:
            f.write(f"═══════════════════════════════════════════════════════════\n")
            f.write(f"LOG DO SISTEMA DE VENDAS PARALELO\n")
            f.write(f"Iniciado em: {self.timestamp_inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"═══════════════════════════════════════════════════════════\n\n")
    
    def registrar_evento(self, etapa: str, worker_id: int, pedido_id: str, 
                        evento: str, detalhes: str = ""):
        """
        Registra um evento do processamento.
        
        Args:
            etapa: 'validacao', 'financeira', 'logistica'
            worker_id: ID do worker que processou
            pedido_id: ID do pedido
            evento: 'INICIO', 'SUCESSO', 'FALHA'
            detalhes: Informações adicionais
        """
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        tempo_decorrido = (datetime.now() - self.timestamp_inicio).total_seconds()
        
        mensagem = f"[{timestamp}] [{etapa.upper()}] Worker-{worker_id}: Pedido {pedido_id} - {evento}"
        if detalhes:
            mensagem += f" ({detalhes})"
        
        with self.lock:
            # Escrever em arquivo
            with open(self.arquivo_log, 'a') as f:
                f.write(f"{mensagem}\n")
            
            # Imprimir no console
            print(mensagem)
            
            # Atualizar estatísticas
            if evento == "SUCESSO":
                self.pedidos_processados[f"{etapa}_sucesso"] += 1
            elif evento == "FALHA":
                self.pedidos_processados[f"{etapa}_falha"] += 1
    
    def registrar_tempo_processamento(self, etapa: str, tempo: float):
        """Registra o tempo gasto em uma etapa"""
        with self.lock:
            self.tempo_etapas[etapa].append(tempo)
    
    def gerar_relatorio_final(self) -> Dict:
        """Gera relatório final com estatísticas"""
        tempo_total = (datetime.now() - self.timestamp_inicio).total_seconds()
        
        # Contar eventos do arquivo de log
        pedidos_contagem = defaultdict(int)
        tempos_etapas = defaultdict(list)
        
        try:
            with open(self.arquivo_log, 'r') as f:
                for linha in f:
                    if 'SUCESSO' in linha:
                        if 'VALIDACAO' in linha:
                            pedidos_contagem['validacao_sucesso'] += 1
                        elif 'FINANCEIRA' in linha:
                            pedidos_contagem['financeira_sucesso'] += 1
                        elif 'LOGISTICA' in linha:
                            pedidos_contagem['logistica_sucesso'] += 1
                        
                        # Extrair tempo se estiver no log
                        if 'Tempo: ' in linha:
                            try:
                                tempo_str = linha.split('Tempo: ')[1].split('s')[0]
                                tempo = float(tempo_str)
                                if 'VALIDACAO' in linha:
                                    tempos_etapas['validacao'].append(tempo)
                                elif 'FINANCEIRA' in linha:
                                    tempos_etapas['financeira'].append(tempo)
                                elif 'LOGISTICA' in linha:
                                    tempos_etapas['logistica'].append(tempo)
                            except:
                                pass
                    
                    elif 'FALHA' in linha:
                        if 'VALIDACAO' in linha:
                            pedidos_contagem['validacao_falha'] += 1
                        elif 'FINANCEIRA' in linha:
                            pedidos_contagem['financeira_falha'] += 1
                        elif 'LOGISTICA' in linha:
                            pedidos_contagem['logistica_falha'] += 1
        except:
            pass
        
        relatorio = {
            'tempo_total_segundos': tempo_total,
            'timestamp_inicio': self.timestamp_inicio.isoformat(),
            'timestamp_fim': datetime.now().isoformat(),
            'pedidos_processados': dict(pedidos_contagem),
            'tempos_por_etapa': {}
        }
        
        # Calcular estatísticas de tempo
        for etapa, tempos in tempos_etapas.items():
            if tempos:
                relatorio['tempos_por_etapa'][etapa] = {
                    'minimo': min(tempos),
                    'maximo': max(tempos),
                    'media': sum(tempos) / len(tempos),
                    'total': sum(tempos),
                    'count': len(tempos)
                }
        
        return relatorio
    
    def exibir_resumo_final(self):
        """Exibe resumo final bonito no console e arquivo"""
        relatorio = self.gerar_relatorio_final()
        tempo_total = relatorio['tempo_total_segundos']
        
        resumo = f"""
╔════════════════════════════════════════════════════════════╗
║              RELATÓRIO FINAL DO SISTEMA                    ║
╠════════════════════════════════════════════════════════════╣
║ Tempo Total de Execução: {tempo_total:.2f} segundos
║
║ PEDIDOS PROCESSADOS:
"""
        
        for chave, valor in relatorio['pedidos_processados'].items():
            resumo += f"║   • {chave}: {valor}\n"
        
        resumo += f"""║
║ TEMPOS POR ETAPA (em segundos):
"""
        
        for etapa, stats in relatorio['tempos_por_etapa'].items():
            resumo += f"║   {etapa.upper()}:\n"
            resumo += f"║     • Mínimo: {stats['minimo']:.3f}s\n"
            resumo += f"║     • Máximo: {stats['maximo']:.3f}s\n"
            resumo += f"║     • Média: {stats['media']:.3f}s\n"
            resumo += f"║     • Total: {stats['total']:.2f}s\n"
            resumo += f"║     • Eventos: {stats['count']}\n"
        
        resumo += "╚════════════════════════════════════════════════════════════╝\n"
        
        # Exibir no console
        print(resumo)
        
        # Salvar em arquivo
        with open(self.arquivo_log, 'a') as f:
            f.write(resumo)
        
        # Salvar JSON para análise
        arquivo_json = self.arquivo_log.replace('.log', '.json')
        with open(arquivo_json, 'w') as f:
            json.dump(relatorio, f, indent=2)
        
        print(f"\n📊 Relatório JSON salvo em: {arquivo_json}")
        print(f"📄 Log completo em: {self.arquivo_log}")
        
        return relatorio


# Instância global do monitor (será usada por todos os workers)
monitor_global = None


def inicializar_monitor(arquivo_log: str = None) -> MonitorSistema:
    """Factory para inicializar o monitor global"""
    global monitor_global
    monitor_global = MonitorSistema(arquivo_log)
    return monitor_global


def obter_monitor() -> MonitorSistema:
    """Obtém a instância global do monitor"""
    global monitor_global
    if monitor_global is None:
        monitor_global = MonitorSistema()
    return monitor_global
