from collections import Counter
from datetime import datetime
from multiprocessing import Process, Queue, current_process
from typing import Any, Dict, Optional
import json
import os


TIPO_EVENTO = "evento"
TIPO_PEDIDO_FINALIZADO = "pedido_finalizado"
TIPO_FINALIZAR = "finalizar"
TIPO_ERRO = "erro"


monitor_global = None

def timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def arquivo_json_de(arquivo_log: str) -> str:
    return arquivo_log.replace(".log", ".json")

def prefixo_monitor() -> str:
    return f"[{timestamp()}] [PID {os.getpid()}] [{current_process().name}] [MONITOR]"


def escrever_linha_log(arquivo_log: str, linha: str):
    with open(arquivo_log, "a", encoding="utf-8") as f:
        f.write(linha + "\n")

def monitor_worker(fila_eventos: Queue, arquivo_log: str, arquivo_json: str, timestamp_inicio_iso: str, total_esperado: Optional[int] = None):
    timestamp_inicio = datetime.fromisoformat(timestamp_inicio_iso)
    
    with open(arquivo_log, "w", encoding="utf-8") as f:
        f.write(
            "SISTEMA DE VENDAS - Iniciado em "
            f"{timestamp_inicio.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        f.write("=" * 80 + "\n\n")

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
            linha = (f"[{mensagem.get('timestamp', timestamp())}] "
                    f"[PID {mensagem.get('pid', '-')}] "
                    f"[{mensagem.get('processo', '-')}] "
                    f"[{str(mensagem.get('etapa', '')).upper()} {mensagem.get('worker_id', '-')}] "
                    f"{mensagem.get('pedido_id', '-')} - "
                    f"{mensagem.get('evento', '')}")
            
            detalhes = mensagem.get("detalhes")
            if detalhes:
                linha += f" | {detalhes}"
            escrever_linha_log(arquivo_log, linha)

        elif tipo == TIPO_PEDIDO_FINALIZADO:
            pedido_dict = mensagem["pedido"]
            pedidos.append(pedido_dict)
            contadores_status[pedido_dict["status"]] += 1
            escrever_linha_log(
                arquivo_log, 
                f"[{mensagem.get('timestamp', timestamp())}] " 
                f"[PID {mensagem.get('pid', '-')}] " 
                f"[{mensagem.get('processo', '-')}] " 
                f"[PEDIDO_FINALIZADO] {pedido_dict['id']} - {pedido_dict['status']}")

        elif tipo == TIPO_ERRO:
            escrever_linha_log(
                arquivo_log,
                f"[{mensagem.get('timestamp', timestamp())}] "
                f"[PID {mensagem.get('pid', '-')}] "
                f"[{mensagem.get('processo', '-')}] "
                f"[ERRO] {mensagem.get('detalhes', '')}")

        else:
            escrever_linha_log(arquivo_log, f"{prefixo_monitor()} Mensagem desconhecida: {mensagem}")

    timestamp_fim = datetime.now()
    tempo_total = (timestamp_fim - timestamp_inicio).total_seconds()
    
    relatorio = {
        "tempo_total_segundos": tempo_total,
        "timestamp_inicio": timestamp_inicio.isoformat(),
        "timestamp_fim": timestamp_fim.isoformat(),
        "total_esperado": total_esperado,
        "total_pedidos": len(pedidos),
        "contadores_por_status": dict(contadores_status),
        "eventos_registrados": eventos_registrados,
        "pedidos": pedidos,
    }

    with open(arquivo_json, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)

    escrever_linha_log(arquivo_log, f"{prefixo_monitor()} Active Object finalizado")
    escrever_linha_log(arquivo_log, f"Total de pedidos finalizados: {len(pedidos)}")
    escrever_linha_log(arquivo_log, f"Contadores por status: {dict(contadores_status)}")
    escrever_linha_log(arquivo_log, f"Relatório JSON: {arquivo_json}")


def registrar_evento(fila_monitor: Optional[Queue], etapa: str, worker_id: int, pedido_id: str, evento: str,detalhes: str = ""):
    if fila_monitor is None:
        return
    fila_monitor.put({"tipo": TIPO_EVENTO,"timestamp": timestamp(), "pid": os.getpid(), "processo": current_process().name, "etapa": etapa, "worker_id": worker_id, "pedido_id": pedido_id, "evento": evento, "detalhes": detalhes})


def registrar_pedido_finalizado(fila_monitor: Optional[Queue], pedido):
    if fila_monitor is None:
        return
    fila_monitor.put({"tipo": TIPO_PEDIDO_FINALIZADO, "timestamp": timestamp(), "pid": os.getpid(), "processo": current_process().name, "pedido": pedido.para_dict()})


def registrar_erro(fila_monitor: Optional[Queue], detalhes: str):
    if fila_monitor is None:
        return
    
    fila_monitor.put({"tipo": TIPO_ERRO,"timestamp": timestamp(), "pid": os.getpid(),"processo": current_process().name, "detalhes": detalhes})

class MonitorSistema:
    def __init__(self, arquivo_log: str = None, total_esperado: Optional[int] = None):
        self.arquivo_log = arquivo_log or "sistema_vendas.log"
        self.arquivo_json = arquivo_json_de(self.arquivo_log)
        self.timestamp_inicio = datetime.now()
        self.total_esperado = total_esperado
        self.fila_eventos = Queue()
        self.processo = Process(target=monitor_worker, args=(self.fila_eventos, self.arquivo_log, self.arquivo_json, self.timestamp_inicio.isoformat(), self.total_esperado), name="monitor-active-object")

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
                "pedidos": [],
            }

        with open(self.arquivo_json, "r", encoding="utf-8") as f:
            return json.load(f)

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

