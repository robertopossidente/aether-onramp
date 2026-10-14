#!/usr/bin/env python3
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Prometheus exporter for the OCUDU disaggregated gNB (O-CU + O-DU).

* O-DU: JSON metrics pushed through the local remote control WebSocket
  (command "metrics_subscribe").
* O-CU: "[METRICS]" lines printed to the container log (the ocu binary has no
  JSON gateway).
* Container state: docker inspect.

Only the Python standard library and the docker CLI are required.
"""

import argparse
import base64
import calendar
import json
import os
import re
import select
import socket
import struct
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STALE_SECONDS = 5.0

lock = threading.Lock()
state = {
    "args": None,
    "docker": {},
    "du": {"ws_up": 0, "last": 0.0, "cells": [], "cells_ts": 0.0, "mac": [], "mac_ts": 0.0},
    "cu": {"last": 0.0, "ngap": {}, "rrc": {}, "e1ap": {}, "pdcp": {}},
    "counters": {},
}


def now():
    return time.time()


def accumulate(name, labels, delta):
    key = (name, tuple(sorted(labels.items())))
    state["counters"][key] = state["counters"].get(key, 0.0) + delta


# ---------------------------------------------------------------- WebSocket --
class WebSocket:
    def __init__(self, host, port):
        self.sock = socket.create_connection((host, port), timeout=5)
        key = base64.b64encode(os.urandom(16)).decode()
        request = (
            "GET / HTTP/1.1\r\nHost: {}:{}\r\nUpgrade: websocket\r\n"
            "Connection: Upgrade\r\nSec-WebSocket-Key: {}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        ).format(host, port, key)
        self.sock.sendall(request.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("handshake closed")
            buf += chunk
        head, _, self.buf = buf.partition(b"\r\n\r\n")
        if b" 101 " not in head.split(b"\r\n")[0]:
            raise ConnectionError("websocket upgrade refused")

    def _read(self, n):
        while len(self.buf) < n:
            self.sock.settimeout(10)
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("closed")
            self.buf += chunk
        data, self.buf = self.buf[:n], self.buf[n:]
        return data

    def send(self, payload, opcode=0x1):
        data = payload.encode() if isinstance(payload, str) else payload
        mask = os.urandom(4)
        n = len(data)
        if n < 126:
            header = struct.pack("!BB", 0x80 | opcode, 0x80 | n)
        elif n < 65536:
            header = struct.pack("!BBH", 0x80 | opcode, 0x80 | 126, n)
        else:
            header = struct.pack("!BBQ", 0x80 | opcode, 0x80 | 127, n)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        self.sock.sendall(header + mask + masked)

    def readable(self, timeout):
        if self.buf:
            return True
        ready, _, _ = select.select([self.sock], [], [], timeout)
        return bool(ready)

    def recv_message(self):
        message = b""
        while True:
            b0, b1 = struct.unpack("!BB", self._read(2))
            fin, opcode = b0 & 0x80, b0 & 0x0F
            length = b1 & 0x7F
            if length == 126:
                length = struct.unpack("!H", self._read(2))[0]
            elif length == 127:
                length = struct.unpack("!Q", self._read(8))[0]
            payload = self._read(length)
            if opcode == 0x8:
                raise ConnectionError("closed by peer")
            if opcode == 0x9:
                self.send(payload, 0xA)
                continue
            if opcode == 0xA:
                continue
            message += payload
            if fin:
                return message.decode("utf-8", "replace")

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


# ---------------------------------------------------------------------- DU --
def handle_du_message(msg):
    ts = now()
    with lock:
        du = state["du"]
        du["last"] = ts
        if "cells" in msg:
            du["cells"] = msg["cells"]
            du["cells_ts"] = ts
            for cell in msg["cells"]:
                cm = cell.get("cell_metrics", {})
                pci = str(cm.get("pci", 0))
                accumulate("ocudu_du_cell_failed_pdcch_allocs_total", {"pci": pci}, cm.get("nof_failed_pdcch_allocs", 0))
                accumulate("ocudu_du_cell_late_harqs_total", {"pci": pci, "direction": "dl"}, cm.get("late_dl_harqs", 0))
                accumulate("ocudu_du_cell_late_harqs_total", {"pci": pci, "direction": "ul"}, cm.get("late_ul_harqs", 0))
                accumulate("ocudu_du_cell_msg3_total", {"pci": pci, "result": "ok"}, cm.get("msg3_nof_ok", 0))
                accumulate("ocudu_du_cell_msg3_total", {"pci": pci, "result": "nok"}, cm.get("msg3_nof_nok", 0))
                for ue in cell.get("ue_list", []):
                    labels = {"pci": pci, "ue": str(ue.get("ue", 0)), "rnti": "0x%04x" % ue.get("rnti", 0)}
                    for direction in ("dl", "ul"):
                        for result in ("ok", "nok"):
                            accumulate(
                                "ocudu_du_ue_harq_total",
                                dict(labels, direction=direction, result=result),
                                ue.get("%s_nof_%s" % (direction, result), 0),
                            )
        elif "rlc_metrics" in msg:
            rlc = msg["rlc_metrics"]
            labels = {"ue": str(rlc.get("ue_id", 0)), "drb": str(rlc.get("drb_id", 0))}
            accumulate("ocudu_du_rlc_sdu_bytes_total", dict(labels, direction="tx"), rlc.get("tx", {}).get("num_sdu_bytes", 0))
            accumulate("ocudu_du_rlc_sdu_bytes_total", dict(labels, direction="rx"), rlc.get("rx", {}).get("num_sdu_bytes", 0))
            accumulate("ocudu_du_rlc_lost_pdus_total", labels, rlc.get("rx", {}).get("num_lost_pdus", 0))
            accumulate("ocudu_du_rlc_dropped_sdus_total", labels, rlc.get("tx", {}).get("num_dropped_sdus", 0))
        elif "du" in msg:
            mac = msg["du"].get("du_high", {}).get("mac", {}).get("dl")
            if mac is not None:
                du["mac"] = mac
                du["mac_ts"] = ts


def du_loop():
    args = state["args"]
    while True:
        ws = None
        try:
            ws = WebSocket(args.du_ws_host, args.du_ws_port)
            ws.send(json.dumps({"cmd": "metrics_subscribe"}))
            with lock:
                state["du"]["ws_up"] = 1
            last_ping = now()
            while True:
                if ws.readable(2.0):
                    try:
                        msg = json.loads(ws.recv_message())
                    except ValueError:
                        continue
                    if isinstance(msg, dict):
                        handle_du_message(msg)
                elif now() - last_ping > 10:
                    ws.send(b"", 0x9)
                    last_ping = now()
        except (OSError, ConnectionError, struct.error):
            pass
        finally:
            if ws:
                ws.close()
            with lock:
                state["du"]["ws_up"] = 0
        time.sleep(2)


# ---------------------------------------------------------------------- CU --
RATE_UNITS = {"": 1.0, "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9}
RE_SUM_ITEMS = re.compile(r"=(\d+)")


def sum_group(line, name):
    m = re.search(name + r"=\[(.*?)\]", line)
    return sum(int(v) for v in RE_SUM_ITEMS.findall(m.group(1))) if m else 0


def parse_rate(text):
    m = re.match(r"\s*([\d.]+)\s*([kKMG]?)bps", text)
    return float(m.group(1)) * RATE_UNITS[m.group(2)] if m else 0.0


def handle_cu_line(line):
    if "METRICS" not in line:
        return
    ts = now()
    with lock:
        cu = state["cu"]
        if "CU-CP NGAP metrics" in line:
            amf = re.search(r"amf_name=(\S+)", line)
            conn = re.search(r"connected=(true|false)", line)
            nssai = re.search(r"s-nssai=\(sst=(\d+)(?: sd=(\d+))?\)", line)
            slice_label = "sst:%s sd:%s" % (nssai.group(1), nssai.group(2) or "-") if nssai else "-"
            req = re.search(r"nof_pdu_sessions_requested_to_setup=(\d+)", line)
            ok = re.search(r"nof_pdu_sessions_successfully_setup=(\d+)", line)
            cu["ngap"][(amf.group(1) if amf else "unknown", slice_label)] = {
                "connected": 1 if conn and conn.group(1) == "true" else 0,
                "requested": int(req.group(1)) if req else 0,
                "setup": int(ok.group(1)) if ok else 0,
                "failed": sum_group(line, "nof_pdu_sessions_failed_to_setup"),
                "ts": ts,
            }
        elif "CU-CP RRC metrics" in line:
            du_id = re.search(r"gnb_du_id=(\d+)", line)
            mean = re.search(r"mean_nof_rrc_connections=([\d.]+)", line)
            mx = re.search(r"max_nof_rrc_connections=(\d+)", line)
            cu["rrc"][du_id.group(1) if du_id else "0"] = {
                "mean": float(mean.group(1)) if mean else 0.0,
                "max": int(mx.group(1)) if mx else 0,
                "attempted": sum_group(line, "attempted_rrc_connection_establishments"),
                "successful": sum_group(line, "successful_rrc_connection_establishments"),
                "ts": ts,
            }
        elif "E1AP metrics" in line:
            cu["e1ap"] = {
                "ctx_setup": int((re.search(r"num_success_ctx_setup=(\d+)", line) or [0, 0])[1]),
                "ctx_modification": int((re.search(r"num_success_ctx_modification=(\d+)", line) or [0, 0])[1]),
                "ctx_releases": int((re.search(r"num_ctx_releases=(\d+)", line) or [0, 0])[1]),
                "ts": ts,
            }
        elif "PDCP Metrics" in line:
            m = re.search(r"ue=(\d+) rb=(\S+) tx=\[(.*?)\] rx=\[(.*?)\]", line)
            if m:
                rates = {}
                for direction, body in (("tx", m.group(3)), ("rx", m.group(4))):
                    r = re.search(r"sdu_rate=\s*([\d.]+\s*[kKMG]?bps)", body)
                    rates[direction] = parse_rate(r.group(1)) if r else 0.0
                cu["pdcp"][(m.group(1), m.group(2))] = dict(rates, ts=ts)
        else:
            return
        cu["last"] = ts


def cu_loop():
    args = state["args"]
    while True:
        try:
            proc = subprocess.Popen(
                ["docker", "logs", "-f", "--since", "1s", args.cu_container],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="replace",
            )
            for line in proc.stdout:
                handle_cu_line(line)
            proc.wait()
        except OSError:
            pass
        time.sleep(2)


# ------------------------------------------------------------------ docker --
def docker_loop():
    args = state["args"]
    while True:
        for component, name in (("cu", args.cu_container), ("du", args.du_container)):
            info = {"running": 0, "started": 0.0, "restarts": 0}
            try:
                out = subprocess.run(
                    ["docker", "inspect", "--format",
                     "{{.State.Running}} {{.State.StartedAt}} {{.RestartCount}}", name],
                    capture_output=True, text=True, timeout=10,
                )
                if out.returncode == 0:
                    running, started, restarts = out.stdout.split()
                    info["running"] = 1 if running == "true" else 0
                    info["restarts"] = int(restarts)
                    stamp = started.split(".")[0].rstrip("Z")
                    info["started"] = float(calendar.timegm(time.strptime(stamp, "%Y-%m-%dT%H:%M:%S")))
            except (OSError, ValueError, subprocess.SubprocessError):
                pass
            with lock:
                state["docker"][component] = info
        time.sleep(5)


# ----------------------------------------------------------------- render ---
def escape(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


class Output:
    def __init__(self):
        self.families = {}

    def add(self, name, mtype, help_text, value, **labels):
        family = self.families.setdefault(name, [mtype, help_text, []])
        family[2].append((labels, value))

    def render(self):
        lines = []
        for name, (mtype, help_text, samples) in self.families.items():
            lines.append("# HELP %s %s" % (name, help_text))
            lines.append("# TYPE %s %s" % (name, mtype))
            for labels, value in samples:
                lab = ",".join('%s="%s"' % (k, escape(v)) for k, v in labels.items())
                lines.append("%s%s %s" % (name, "{%s}" % lab if lab else "", repr(float(value))))
        return "\n".join(lines) + "\n"


def build_metrics():
    out = Output()
    t = now()
    with lock:
        dock, du, cu = state["docker"], state["du"], state["cu"]

        for component in ("cu", "du"):
            info = dock.get(component, {"running": 0, "started": 0.0, "restarts": 0})
            out.add("ocudu_container_up", "gauge", "Container is running", info["running"], component=component)
            out.add("ocudu_container_start_timestamp_seconds", "gauge", "Container start time", info["started"], component=component)
            out.add("ocudu_container_restarts", "gauge", "Docker restart count", info["restarts"], component=component)

        cu_running = dock.get("cu", {}).get("running", 0)
        du_running = dock.get("du", {}).get("running", 0)
        cu_fresh = t - cu["last"] < STALE_SECONDS
        cu_up = 1 if cu_running and cu_fresh else 0
        du_up = 1 if du_running and du["ws_up"] else 0
        out.add("ocudu_cu_up", "gauge", "O-CU running and reporting metrics", cu_up)
        out.add("ocudu_du_up", "gauge", "O-DU running and remote control reachable", du_up)
        out.add("ocudu_cu_last_report_timestamp_seconds", "gauge", "Last O-CU metrics line", cu["last"])
        out.add("ocudu_du_last_report_timestamp_seconds", "gauge", "Last O-DU metrics message", du["last"])

        for (amf, slice_label), v in cu["ngap"].items():
            if t - v["ts"] >= STALE_SECONDS:
                continue
            out.add("ocudu_cu_ngap_connected", "gauge", "NGAP association with the AMF", v["connected"], amf_name=amf, slice=slice_label)
            out.add("ocudu_cu_ngap_pdu_sessions_requested_total", "counter", "PDU sessions requested to setup", v["requested"], amf_name=amf, slice=slice_label)
            out.add("ocudu_cu_ngap_pdu_sessions_setup_total", "counter", "PDU sessions successfully set up", v["setup"], amf_name=amf, slice=slice_label)
            out.add("ocudu_cu_ngap_pdu_sessions_failed_total", "counter", "PDU sessions failed to setup", v["failed"], amf_name=amf, slice=slice_label)

        for du_id, v in cu["rrc"].items():
            if t - v["ts"] >= STALE_SECONDS:
                continue
            out.add("ocudu_f1_du_connected", "gauge", "O-DU known by the O-CU over F1 (and O-DU up)", du_up, du_id=du_id)
            out.add("ocudu_cu_rrc_connections_mean", "gauge", "Mean RRC connections", v["mean"], du_id=du_id)
            out.add("ocudu_cu_rrc_connections_max", "gauge", "Max RRC connections", v["max"], du_id=du_id)
            out.add("ocudu_cu_rrc_establishments_attempted_total", "counter", "RRC establishments attempted", v["attempted"], du_id=du_id)
            out.add("ocudu_cu_rrc_establishments_successful_total", "counter", "RRC establishments successful", v["successful"], du_id=du_id)
        if not any(t - v["ts"] < STALE_SECONDS for v in cu["rrc"].values()):
            out.add("ocudu_f1_du_connected", "gauge", "O-DU known by the O-CU over F1 (and O-DU up)", 0, du_id="0")

        e1 = cu["e1ap"]
        if e1 and t - e1["ts"] < STALE_SECONDS:
            out.add("ocudu_cu_e1ap_ctx_setup_total", "counter", "E1AP bearer context setups", e1["ctx_setup"])
            out.add("ocudu_cu_e1ap_ctx_modification_total", "counter", "E1AP bearer context modifications", e1["ctx_modification"])
            out.add("ocudu_cu_e1ap_ctx_releases_total", "counter", "E1AP bearer context releases", e1["ctx_releases"])

        for (ue, rb), v in cu["pdcp"].items():
            if t - v["ts"] >= STALE_SECONDS:
                continue
            out.add("ocudu_cu_pdcp_sdu_rate_bps", "gauge", "PDCP SDU rate", v["tx"], ue=ue, rb=rb, direction="tx")
            out.add("ocudu_cu_pdcp_sdu_rate_bps", "gauge", "PDCP SDU rate", v["rx"], ue=ue, rb=rb, direction="rx")

        ues = 0
        if t - du["cells_ts"] < STALE_SECONDS:
            for cell in du["cells"]:
                cm = cell.get("cell_metrics", {})
                pci = str(cm.get("pci", 0))
                out.add("ocudu_du_cell_scheduler_latency_avg_us", "gauge", "Scheduler average latency", cm.get("average_latency", 0), pci=pci)
                out.add("ocudu_du_cell_scheduler_latency_max_us", "gauge", "Scheduler max latency", cm.get("max_latency", 0), pci=pci)
                out.add("ocudu_du_cell_pucch_rb_usage", "gauge", "Average PUCCH RB usage", cm.get("pucch_tot_rb_usage_avg", 0), pci=pci)
                for ue in cell.get("ue_list", []):
                    ues += 1
                    labels = {"pci": pci, "ue": str(ue.get("ue", 0)), "rnti": "0x%04x" % ue.get("rnti", 0)}
                    for name, key, help_text in (
                        ("ocudu_du_ue_dl_bitrate_bps", "dl_brate", "UE downlink bitrate"),
                        ("ocudu_du_ue_ul_bitrate_bps", "ul_brate", "UE uplink bitrate"),
                        ("ocudu_du_ue_cqi", "cqi", "UE reported CQI"),
                        ("ocudu_du_ue_dl_mcs", "dl_mcs", "UE downlink MCS"),
                        ("ocudu_du_ue_ul_mcs", "ul_mcs", "UE uplink MCS"),
                        ("ocudu_du_ue_pusch_snr_db", "pusch_snr_db", "UE PUSCH SNR"),
                        ("ocudu_du_ue_pucch_snr_db", "pucch_snr_db", "UE PUCCH SNR"),
                        ("ocudu_du_ue_timing_advance_ns", "ta_ns", "UE timing advance"),
                        ("ocudu_du_ue_bsr_bytes", "bsr", "UE buffer status report"),
                    ):
                        if key in ue:
                            out.add(name, "gauge", help_text, ue[key], **labels)
        out.add("ocudu_du_connected_ues", "gauge", "UEs reported by the O-DU scheduler", ues)

        if t - du["mac_ts"] < STALE_SECONDS:
            for item in du["mac"]:
                pci = str(item.get("pci", 0))
                out.add("ocudu_du_mac_dl_latency_avg_us", "gauge", "MAC DL average latency", item.get("average_latency_us", 0), pci=pci)
                out.add("ocudu_du_mac_dl_cpu_usage_percent", "gauge", "MAC DL CPU usage", item.get("cpu_usage_percent", 0), pci=pci)

        for (name, labels), value in state["counters"].items():
            out.add(name, "counter", name.replace("_", " "), value, **dict(labels))
    return out.render()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] == "/metrics":
            body = build_metrics().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        elif self.path == "/healthz":
            body = b"ok\n"
            self.send_response(200)
        else:
            body = b"not found\n"
            self.send_response(404)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--listen", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9110)
    parser.add_argument("--cu-container", default="ocudu-cu")
    parser.add_argument("--du-container", default="ocudu-du")
    parser.add_argument("--du-ws-host", default="127.0.0.1")
    parser.add_argument("--du-ws-port", type=int, default=8002)
    state["args"] = parser.parse_args()
    for target in (du_loop, cu_loop, docker_loop):
        threading.Thread(target=target, daemon=True).start()
    ThreadingHTTPServer((state["args"].listen, state["args"].port), Handler).serve_forever()


if __name__ == "__main__":
    main()
