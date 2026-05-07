from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ConfiguracaoSistema:
    """
    Configurações do sistema de vendas paralelo.

    Controla:
    - Número de workers em cada etapa (Worker Pool)
    - Taxas de falha em cada validação
    - Número de clientes e pedidos
    - Tamanho das filas/buffers do padrão Produtor/Consumidor
    - Tempos de processamento simulados
    - Arquivo de log/relatório
    """

    # quantos workers por etapa
    num_validadores: int                = 2
    num_financeiros: int                = 2
    num_logisticos: int                 = 2

    #taxas de falha 
    taxa_falha_validacao: float         = 0.25
    taxa_falha_financeira: float        = 0.25
    taxa_falha_logistica: float         = 0.25

    #define quantos clientes e pedidos
    num_clientes: int                   = 4
    pedidos_por_cliente: int            = 6

    #fila limitada
    tamanho_fila: int                   = 10

    #tempos de processamento em segundos
    tempo_processamento_min: float      = 0.5
    tempo_processamento_max: float      = 2.0

    arquivo_log: str = "sistema_vendas.log"

    
    itens_disponiveis: List[str] = field(default_factory=lambda: [
        "Notebook",
        "Mouse",
        "Teclado",
        "Monitor",
        "Webcam",
        "Headphone",
        "SSD",
        "Memória RAM",
    ])
    
    nomes_clientes: List[str] = field(default_factory=lambda:[
        "João Silva",
        "Maria Santos",
        "Pedro Oliveira",
        "Ana Costa",
    ])

    def __post_init__(self):
        self._validar()

    def _validar(self):
        """Valida configurações para falhar cedo, antes de iniciar processos."""
        if self.num_clientes <= 0:
            raise ValueError("num_clientes deve ser maior que zero")
        if self.pedidos_por_cliente <= 0:
            raise ValueError("pedidos_por_cliente deve ser maior que zero")
        if self.num_validadores <= 0:
            raise ValueError("num_validadores deve ser maior que zero")
        if self.num_financeiros <= 0:
            raise ValueError("num_financeiros deve ser maior que zero")
        if self.num_logisticos <= 0:
            raise ValueError("num_logisticos deve ser maior que zero")
        if self.tamanho_fila <= 0:
            raise ValueError("tamanho_fila deve ser maior que zero")
        if self.tempo_processamento_min < 0:
            raise ValueError("tempo_processamento_min não pode ser negativo")
        if self.tempo_processamento_max < self.tempo_processamento_min:
            raise ValueError("tempo_processamento_max deve ser maior ou igual ao mínimo")

        taxas = {
            "taxa_falha_validacao": self.taxa_falha_validacao,
            "taxa_falha_financeira": self.taxa_falha_financeira,
            "taxa_falha_logistica": self.taxa_falha_logistica,
        }
        for nome, valor in taxas.items():
            if not 0.0 <= valor <= 1.0:
                raise ValueError(f"{nome} deve estar entre 0.0 e 1.0")

    def total_pedidos_esperados(self) -> int:
        """Calcula total de pedidos que serão gerados."""
        return self.num_clientes * self.pedidos_por_cliente

    def __str__(self):
        return f"""
        CONFIGURAÇÃO DO SISTEMA DE VENDAS  
            WORKER POOLS                                  
            • Validadores: {self.num_validadores:<30}
            • Financeiros: {self.num_financeiros:<30}
            • Logísticos: {self.num_logisticos:<31}
                                                        
        TAXAS DE FALHA                                
            • Validação: {self.taxa_falha_validacao * 100:>5.1f}%{'':<21}
            • Financeira: {self.taxa_falha_financeira * 100:>5.1f}%{'':<20}
            • Logística: {self.taxa_falha_logistica * 100:>5.1f}%{'':<21}
                                                        
        PRODUÇÃO                                     
            • Clientes: {self.num_clientes:<33}
            • Pedidos por cliente: {self.pedidos_por_cliente:<22}
            • Total esperado: {self.total_pedidos_esperados():<26}
                                                        
        FILAS / BUFFERS                               
            • Tamanho máximo por fila: {self.tamanho_fila:<16}                                              
            TIMING (segundos)                             
            • Min: {self.tempo_processamento_min:<37}  
            • Max: {self.tempo_processamento_max:<37}

"""

#configuração padrão
CONFIG_PADRAO = ConfiguracaoSistema()

#configuração para testes rápidos
CONFIG_TESTE = ConfiguracaoSistema(
    num_validadores=2,
    num_financeiros=1,
    num_logisticos=1,
    pedidos_por_cliente=10,
    tamanho_fila=10,
    tempo_processamento_min=0.1,
    tempo_processamento_max=0.5,
    arquivo_log="sistema_vendas.log"
    )

# configuração para teste pesado
CONFIG_PESADO = ConfiguracaoSistema(
    num_validadores=5,
    num_financeiros=4,
    num_logisticos=3,
    pedidos_por_cliente=200,
    tamanho_fila=50,
    tempo_processamento_min=0.5,
    tempo_processamento_max=2.0,
    arquivo_log="sistema_vendas.log"
    )
