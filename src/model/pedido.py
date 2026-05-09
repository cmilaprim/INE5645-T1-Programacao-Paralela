from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict
import uuid

class StatusPedido(Enum):
    NOVO = "Novo"
    VALIDADO = "Validado"
    REJEITADO_VALIDACAO = "Rejeitado na Validação"
    APROVADO_FINANCEIRO = "Aprovado Financeiramente"
    REJEITADO_FINANCEIRO = "Rejeitado Financeiramente"
    ENTREGUE = "Entregue"
    FALHA_ENTREGA = "Falha na Entrega"


STATUS_FINAIS = {
    StatusPedido.REJEITADO_VALIDACAO,
    StatusPedido.REJEITADO_FINANCEIRO,
    StatusPedido.ENTREGUE,
    StatusPedido.FALHA_ENTREGA,
}

@dataclass
class Pedido:
    id: str
    cliente_id: str
    nome_cliente: str
    item: str
    valor: float
    status: StatusPedido = StatusPedido.NOVO
    timestamp_criacao: datetime = field(default_factory=datetime.now)
    timestamps: Dict[str, datetime] = field(default_factory=dict)

    def registrar_timestamp(self, etapa: str):
        self.timestamps[etapa] = datetime.now()

    def atualizar_status(self, novo_status: StatusPedido):
        self.status = novo_status
        etapa = novo_status.value.lower().replace(" ", "_")
        self.registrar_timestamp(etapa)

    def esta_finalizado(self) -> bool:
        return self.status in STATUS_FINAIS

    def para_dict(self) -> dict:
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "nome_cliente": self.nome_cliente,
            "item": self.item,
            "valor": self.valor,
            "status": self.status.value,
            "timestamp_criacao": self.timestamp_criacao.isoformat(),
            "timestamps": {k: v.isoformat() for k, v in self.timestamps.items()}
        }

    def __str__(self):
        return (
            f"Pedido({self.id}, Cliente={self.nome_cliente}, "
            f"Item={self.item}, Status={self.status.value})"
        )


def criar_pedido(cliente_id: str, nome_cliente: str, item: str, valor: float, config=None) -> Pedido:
    pedido_id = str(uuid.uuid4())[:8]

    return Pedido(id=pedido_id, cliente_id=cliente_id, nome_cliente=nome_cliente, item=item, valor=valor)