from dataclasses import dataclass
from typing import Tuple


@dataclass
class ConfiguracaoSistema:
    """
    Configurações do sistema de vendas paralelo.
    
    Controla:
    - Número de workers em cada etapa (Worker Pool)
    - Taxas de falha em cada validação
    - Número de clientes e pedidos
    - Tempos de processamento
    """
    
    #worker Pool - define quantos workers por etapa
    num_validadores: int = 3          #validação de pedidos
    num_financeiros: int = 2          #validação financeira
    num_logisticos: int = 2           #logística/entrega
    
    #taxa de Falha - define a taxa de falha em cada etapa
    taxa_falha_validacao: float = 0.1      #10% dos pedidos falham
    taxa_falha_financeira: float = 0.15    #15% dos pedidos falham
    taxa_falha_logistica: float = 0.05     #5% dos pedidos falham
    
    #produção - define quantos clientes e pedidos
    num_clientes: int = 2                  #2 clientes gerando pedidos
    pedidos_por_cliente: int = 5           #50 pedidos por cliente
    
    #timing - define os tempos de processamento
    tempo_processamento_min: float = 0.5    #mínimo 0.5 segundos
    tempo_processamento_max: float = 2.0    #máximo 2.0 segundos
    
    #itens disponíveis para compra
    itens_disponiveis: list = None
    
    #nomes dos clientes
    nomes_clientes: dict = None
    
    def __post_init__(self):
        if self.itens_disponiveis is None:
            self.itens_disponiveis = [
                "Notebook",
                "Mouse",
                "Teclado",
                "Monitor",
                "Webcam",
                "Headphone",
                "SSD",
                "Memória RAM"
            ]
        
        if self.nomes_clientes is None:
            self.nomes_clientes = {}
    
    def total_pedidos_esperados(self) -> int:
        """Calcula total de pedidos que serão gerados"""
        return self.num_clientes * self.pedidos_por_cliente
    
    def __str__(self):
        return f"""
╔════════════════════════════════════════════════╗
║   CONFIGURAÇÃO DO SISTEMA DE VENDAS PARALELO   ║
╠════════════════════════════════════════════════╣
║  WORKER POOLS                                   ║
║  • Validadores: {self.num_validadores}                                ║
║  • Financeiros: {self.num_financeiros}                                ║
║  • Logísticos: {self.num_logisticos}                                 ║
║                                                 ║
║  TAXAS DE FALHA                                ║
║  • Validação: {self.taxa_falha_validacao*100:.1f}%                             ║
║  • Financeira: {self.taxa_falha_financeira*100:.1f}%                            ║
║  • Logística: {self.taxa_falha_logistica*100:.1f}%                             ║
║                                                 ║
║  PRODUÇÃO                                      ║
║  • Clientes: {self.num_clientes}                               ║
║  • Pedidos por cliente: {self.pedidos_por_cliente}                      ║
║  • Total esperado: {self.total_pedidos_esperados()}                        ║
║                                                 ║
║  TIMING (segundos)                             ║
║  • Min: {self.tempo_processamento_min}                               ║
║  • Max: {self.tempo_processamento_max}                              ║
╚════════════════════════════════════════════════╝
"""


#config padrão
CONFIG_PADRAO = ConfiguracaoSistema(
    nomes_clientes={
        "CLT-000": "João Silva",
        "CLT-001": "Maria Santos",
        "CLT-002": "Pedro Oliveira",
        "CLT-003": "Ana Costa",
    }
)

#config para testes rápidos
CONFIG_TESTE = ConfiguracaoSistema(
    num_validadores=2,
    num_financeiros=1,
    num_logisticos=1,
    pedidos_por_cliente=10,
    tempo_processamento_min=0.1,
    tempo_processamento_max=0.5,
    nomes_clientes={
        "CLT-000": "João Silva",
        "CLT-001": "Maria Santos",
        "CLT-002": "Pedro Oliveira",
        "CLT-003": "Ana Costa",
    }
)

#config para teste pesado
CONFIG_PESADO = ConfiguracaoSistema(
    num_validadores=5,
    num_financeiros=4,
    num_logisticos=3,
    pedidos_por_cliente=200,
    tempo_processamento_min=0.5,
    tempo_processamento_max=2.0,
    nomes_clientes={
        "CLT-000": "João Silva",
        "CLT-001": "Maria Santos",
        "CLT-002": "Pedro Oliveira",
        "CLT-003": "Ana Costa",
    }
)
