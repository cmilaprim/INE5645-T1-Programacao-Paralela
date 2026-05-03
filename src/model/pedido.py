"""
Model: Definição da classe Pedido
Padrão: MVC - Model
Autor: [Nome dos alunos]
"""

from enum import Enum
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
import uuid


class StatusPedido(Enum):
    """Estados possíveis de um pedido"""
    NOVO = "Novo"
    VALIDADO = "Validado"
    REJEITADO_VALIDACAO = "Rejeitado na Validação"
    APROVADO_FINANCEIRO = "Aprovado Financeiramente"
    REJEITADO_FINANCEIRO = "Rejeitado Financeiramente"
    ENTREGUE = "Entregue"
    FALHA_ENTREGA = "Falha na Entrega"


@dataclass
class Pedido:
    """
    Representa um pedido de compra no sistema.
    
    Attributes:
        id: Identificador único do pedido
        cliente_id: ID do cliente
        item: Descrição do item sendo comprado
        valor: Valor do pedido
        status: Status atual do pedido
        timestamp_criacao: Quando foi criado
        timestamps: Histórico de timestamps por etapa
    """
    id: str
    cliente_id: str
    item: str
    valor: float
    status: StatusPedido = StatusPedido.NOVO
    timestamp_criacao: datetime = None
    timestamps: dict = None  # {'validacao': datetime, 'financeiro': datetime, ...}
    
    def __post_init__(self):
        if self.timestamp_criacao is None:
            self.timestamp_criacao = datetime.now()
        if self.timestamps is None:
            self.timestamps = {}
    
    def registrar_timestamp(self, etapa: str):
        """Registra o timestamp de uma etapa do processamento"""
        self.timestamps[etapa] = datetime.now()
    
    def atualizar_status(self, novo_status: StatusPedido):
        """Atualiza o status do pedido"""
        self.status = novo_status
        etapa = novo_status.value.lower().replace(' ', '_')
        self.registrar_timestamp(etapa)
    
    def para_dict(self) -> dict:
        """Converte o pedido para dicionário (para serialização/logs)"""
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'item': self.item,
            'valor': self.valor,
            'status': self.status.value,
            'timestamp_criacao': self.timestamp_criacao.isoformat(),
            'timestamps': {k: v.isoformat() for k, v in self.timestamps.items()}
        }
    
    def __str__(self):
        return f"Pedido({self.id}, Cliente={self.cliente_id}, Item={self.item}, Status={self.status.value})"


def criar_pedido(cliente_id: str, item: str, valor: float) -> Pedido:
    """Factory function para criar um novo pedido"""
    pedido_id = str(uuid.uuid4())[:8]  # ID curto
    return Pedido(
        id=pedido_id,
        cliente_id=cliente_id,
        item=item,
        valor=valor
    )
