from collections import Counter
from datetime import datetime
from multiprocessing import Process, Queue, current_process
from typing import Optional
import json
import os


TIPO_EVENTO = "evento"
TIPO_PEDIDO_FINALIZADO = "pedido_finalizado"
TIPO_FINALIZAR = "finalizar"
TIPO_ERRO = "erro"


def timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def arquivo_json_de(arquivo_log: str) -> str:
    base, _ = os.path.splitext(arquivo_log)
    return base + ".json"


def escrever_linha_log(arquivo_log: str, linha: str):
    with open(arquivo_log, "a", encoding="utf-8") as arquivo:
        arquivo.write(linha + "\n")


def cabecalho_mensagem(mensagem: dict) -> str:
    return (f"[{mensagem.get('timestamp', timestamp())}] " f"[PID {mensagem.get('pid', '-')}] " f"[{mensagem.get('processo', '-')}]")

def prefixo_monitor() -> str:
    return (f"[{timestamp()}] "f"[PID {os.getpid()}] " f"[{current_process().name}] " f"[MONITOR]")

def mensagem_base(tipo: str) -> dict:
    return {"tipo": tipo,"timestamp": timestamp(), "pid": os.getpid(), "processo": current_process().name}


def formatar_evento(mensagem: dict) -> str:
    linha = (f"{cabecalho_mensagem(mensagem)} " 
            f"[{str(mensagem.get('etapa', '')).upper()} {mensagem.get('worker_id', '-')}] " 
            f"{mensagem.get('pedido_id', '-')} - " 
            f"{mensagem.get('evento', '')}")

    detalhes = mensagem.get("detalhes")
    if detalhes:
        linha += f" | {detalhes}"

    return linha

def formatar_pedido_finalizado(mensagem: dict) -> str:
    pedido = mensagem["pedido"]
    return (f"{cabecalho_mensagem(mensagem)} "f"[PEDIDO_FINALIZADO] {pedido['id']} - {pedido['status']}")


def formatar_erro(mensagem: dict) -> str:
    return (f"{cabecalho_mensagem(mensagem)} "f"[ERRO] {mensagem.get('detalhes', '')}")

def inicializar_log(arquivo_log: str, timestamp_inicio: datetime):
    with open(arquivo_log, "w", encoding="utf-8") as arquivo:
        arquivo.write("SISTEMA DE VENDAS - Iniciado em " f"{timestamp_inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")
        arquivo.write("=" * 80 + "\n\n")


def salvar_relatorio_json(arquivo_json: str, timestamp_inicio: datetime, 
                        timestamp_fim: datetime, total_esperado: Optional[int], 
                        pedidos: list, contadores_status: Counter, eventos_registrados: int):

    tempo_total = (timestamp_fim - timestamp_inicio).total_seconds()

    relatorio = {
        "tempo_total_segundos": tempo_total,
        "timestamp_inicio": timestamp_inicio.isoformat(),
        "timestamp_fim": timestamp_fim.isoformat(),
        "total_esperado": total_esperado,
        "total_pedidos": len(pedidos),
        "contadores_por_status": dict(contadores_status),
        "eventos_registrados": eventos_registrados,
        "pedidos": pedidos
    }

    with open(arquivo_json, "w", encoding="utf-8") as arquivo:
        json.dump(relatorio, arquivo, indent=2, ensure_ascii=False)


def monitor_worker(fila_eventos: Queue,arquivo_log: str,arquivo_json: str,timestamp_inicio_iso: str,total_esperado: Optional[int] = None):
    timestamp_inicio = datetime.fromisoformat(timestamp_inicio_iso)

    inicializar_log(arquivo_log, timestamp_inicio)

    pedidos = []
    contadores_status = Counter()
    eventos_registrados = 0

    escrever_linha_log(arquivo_log, f"{prefixo_monitor()} Active Object iniciado")

    while True:
        mensagem = fila_eventos.get()

        if mensagem is None or mensagem.get("tipo") == TIPO_FINALIZAR:
            break

        eventos_registrados += 1
        tipo = mensagem.get("tipo")

        if tipo == TIPO_EVENTO:
            linha = formatar_evento(mensagem)

        elif tipo == TIPO_PEDIDO_FINALIZADO:
            pedido = mensagem["pedido"]
            pedidos.append(pedido)
            contadores_status[pedido["status"]] += 1
            linha = formatar_pedido_finalizado(mensagem)

        elif tipo == TIPO_ERRO:
            linha = formatar_erro(mensagem)

        else:
            linha = f"{prefixo_monitor()} Mensagem desconhecida: {mensagem}"

        escrever_linha_log(arquivo_log, linha)

    timestamp_fim = datetime.now()

    salvar_relatorio_json(arquivo_json=arquivo_json, timestamp_inicio=timestamp_inicio, timestamp_fim=timestamp_fim, 
                        total_esperado=total_esperado, pedidos=pedidos, contadores_status=contadores_status, eventos_registrados=eventos_registrados)

    escrever_linha_log(arquivo_log, f"{prefixo_monitor()} Active Object finalizado")
    escrever_linha_log(arquivo_log, f"Total de pedidos finalizados: {len(pedidos)}")
    escrever_linha_log(arquivo_log, f"Contadores por status: {dict(contadores_status)}")
    escrever_linha_log(arquivo_log, f"Relatório JSON: {arquivo_json}")


def registrar_evento(fila_monitor: Optional[Queue], etapa: str, worker_id: int, pedido_id: str, evento: str, detalhes: str = ""):
    if fila_monitor is None:
        return

    mensagem = mensagem_base(TIPO_EVENTO)
    mensagem.update({
        "etapa": etapa,
        "worker_id": worker_id,
        "pedido_id": pedido_id,
        "evento": evento,
        "detalhes": detalhes    
        })

    fila_monitor.put(mensagem)


def registrar_pedido_finalizado(fila_monitor: Optional[Queue], pedido):
    if fila_monitor is None:
        return

    mensagem = mensagem_base(TIPO_PEDIDO_FINALIZADO)
    mensagem["pedido"] = pedido.para_dict()

    fila_monitor.put(mensagem)


def registrar_erro(fila_monitor: Optional[Queue], detalhes: str):
    if fila_monitor is None:
        return

    mensagem = mensagem_base(TIPO_ERRO)
    mensagem["detalhes"] = detalhes

    fila_monitor.put(mensagem)

class MonitorSistema:
    def __init__(self, arquivo_log: str = None, total_esperado: Optional[int] = None):
        self.arquivo_log = arquivo_log or "sistema_vendas.log"
        self.arquivo_json = arquivo_json_de(self.arquivo_log)
        self.timestamp_inicio = datetime.now()
        self.total_esperado = total_esperado
        self.fila_eventos = Queue()
        self.processo = Process(
            target=monitor_worker,
            args=(self.fila_eventos, self.arquivo_log, self.arquivo_json, self.timestamp_inicio.isoformat(), self.total_esperado),
            name="monitor-active-object")

    def iniciar(self):
        self.processo.start()

    def finalizar(self):
        if self.processo.is_alive():
            self.fila_eventos.put({"tipo": TIPO_FINALIZAR})
            self.processo.join()

        if self.processo.exitcode not in (0, None):
            raise RuntimeError(f"Monitor terminou com erro. exitcode={self.processo.exitcode}")

    def parar_forcado(self):
        if self.processo.is_alive():
            self.processo.terminate()
            self.processo.join(timeout=2)

            if self.processo.is_alive():
                self.processo.kill()

    def gerar_relatorio_final(self) -> dict:
        if not os.path.exists(self.arquivo_json):
            return {
                "tempo_total_segundos": (datetime.now() - self.timestamp_inicio).total_seconds(),
                "timestamp_inicio": self.timestamp_inicio.isoformat(),
                "timestamp_fim": datetime.now().isoformat(),
                "total_esperado": self.total_esperado,
                "total_pedidos": 0,
                "contadores_por_status": {},
                "eventos_registrados": 0,
                "pedidos": []
            }

        with open(self.arquivo_json, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)

    def exibir_resumo_final(self):
        relatorio = self.gerar_relatorio_final()

        tempo_total = relatorio["tempo_total_segundos"]
        total_pedidos = relatorio["total_pedidos"]
        total_esperado = relatorio.get("total_esperado")
        throughput = total_pedidos / tempo_total if tempo_total > 0 else 0.0

        print("SISTEMA CONCLUÍDO")
        print(f"Tempo total: {tempo_total:.2f} segundos")
        print(f"Pedidos finalizados: {total_pedidos}")

        if total_esperado is not None:
            print(f"Pedidos esperados: {total_esperado}")

        print(f"Throughput: {throughput:.2f} pedidos/s")
        print("\nContadores por status:")

        for status, quantidade in relatorio.get("contadores_por_status", {}).items():
            print(f"  - {status}: {quantidade}")

        print(f"\nLog salvo em: {self.arquivo_log}")
        print(f"Relatório JSON salvo em: {self.arquivo_json}")

        return relatorio