import json
import subprocess
import sys
import time
import urllib.request
import re
import os
import base64
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
from typing import Tuple
from queue import SimpleQueue
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_PORT    = 30001
PORTS_NUM    = 40  
THREADS      = PORTS_NUM
TIMEOUT      = 3   
URL          = "http://www.google.com/generate_204"

SOURCES = {
    "cat-hy2": "https://raw.githubusercontent.com/Catsss3/web-assets-static/main/providers/hy2_list.txt",
    "cat-distributor": "https://raw.githubusercontent.com/Catsss3/assets-distributor/main/distributor.txt",
    "cat-cache": "https://raw.githubusercontent.com/Catsss3/sys-cache-storage/main/live_configs.txt",
    "yitong-mining": "https://raw.githubusercontent.com/yitong2333/proxy-minging/main/v2ray.txt",
    "tg-collector": "https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/main/category/vless.txt",
    "mheidari-proxy": "https://raw.githubusercontent.com/mheidari98/.proxy/main/vless",
    "v2ray-dumper": "https://raw.githubusercontent.com/miladtahanian/V2RayCFGDumper/main/sub.txt",
    "lalatina-nodes": "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/nodes",
    "surfboard-mixed": "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/splitted/mixed"
}

REPO_DIR     = Path(__file__).parent.resolve()
BIN_DIR      = REPO_DIR / "bin"
SING_BOX     = str(BIN_DIR / "sing-box")
SOURCES_DIR  = REPO_DIR / "sources"

def safe_int(val, default: int) -> int:
    try: return int(val) if val else default
    except Exception: return default

def build_vless_outbound(u, q) -> dict:
    try:
        uid, address, port = u.username or "", u.hostname or "", safe_int(u.port, 443)
        if not address or not uid: return {}
        net, sec = str(q.get("type", "tcp")), str(q.get("security", "none"))
        outbound = {"type": "vless", "tag": "proxy", "server": address, "server_port": port, "uuid": uid, "flow": str(q.get("flow", "")), "packet_encoding": "xudp"}
        tls_settings = {}
        if sec in ("tls", "xtls", "reality"):
            tls_settings["enabled"] = True
            tls_settings["server_name"] = str(q.get("sni", address))
            if q.get("alpn"): tls_settings["alpn"] = str(q["alpn"]).split(",")
            if q.get("fp"): tls_settings["utls"] = {"enabled": True, "fingerprint": str(q["fp"])}
        if sec == "reality": tls_settings["reality"] = {"enabled": True, "public_key": str(q.get("pbk", "")), "short_id": str(q.get("sid", ""))}
        if tls_settings: outbound["tls"] = tls_settings
        transport = {}
        if net == "ws":
            transport["type"] = "ws"; transport["path"] = unquote(str(q.get("path", "/")))
            if q.get("host"): transport["headers"] = {"Host": str(q["host"])}
        elif net == "grpc": transport["type"] = "grpc"; transport["service_name"] = str(q.get("serviceName", "grpc"))
        elif net == "h2":
            transport["type"] = "http"; transport["path"] = unquote(str(q.get("path", "/")))
            if q.get("host"): transport["host"] = [str(q["host"])]
        if transport: outbound["transport"] = transport
        return outbound
    except Exception: return {}

def build_hy2_outbound(u, q) -> dict:
    try:
        password, address, port = u.username or "", u.hostname or "", safe_int(u.port, 443)
        if not address or not password: return {}
        outbound = {"type": "hysteria2", "tag": "proxy", "server": address, "server_port": port, "password": password}
        outbound["tls"] = {"enabled": True, "server_name": str(q.get("sni", address)), "insecure": str(q.get("skip-cert-verify", "0")) == "1"}
        if q.get("obfs"): outbound["obfs"] = {"type": str(q["obfs"]), "password": str(q.get("obfs-password", ""))}
        return outbound
    except Exception: return {}

def build_tuic_outbound(u, q) -> dict:
    try:
        token, address, port = u.username or "", u.hostname or "", safe_int(u.port, 443)
        if not address or not token: return {}
        outbound = {"type": "tuic", "tag": "proxy", "server": address, "server_port": port, "uuid": token, "congestion_control": str(q.get("congestion_control", "cubic")), "udp_relay_mode": "native"}
        tls_settings = {"enabled": True, "server_name": str(q.get("sni", address)), "insecure": str(q.get("skip-cert-verify", "0")) == "1"}
        if q.get("alpn"): tls_settings["alpn"] = str(q["alpn"]).split(",")
        outbound["tls"] = tls_settings
        return outbound
    except Exception: return {}

def parse_to_singbox(link: str) -> dict:
    try:
        u = urlparse(link.strip())
        scheme = u.scheme.lower()
        q = {k: v[0] for k, v in parse_qs(u.query).items() if v}
        if scheme == "vless": return build_vless_outbound(u, q)
        elif scheme in ("hysteria2", "hy2"): return build_hy2_outbound(u, q)
        elif scheme == "tuic": return build_tuic_outbound(u, q)
    except Exception: pass
    return {}

def create_config_file(outbound_cfg: dict, port: int) -> Path:
    singbox_json = {
        "log": {"level": "panic"},
        "inbounds": [{"type": "socks", "tag": "socks-in", "listen": "127.0.0.1", "listen_port": port}],
        "outbounds": [outbound_cfg, {"type": "direct", "tag": "direct-out"}]
    }
    p = REPO_DIR / f"tmp_{port}.json"
    p.write_text(json.dumps(singbox_json), encoding="utf-8")
    return p

def curl_test(port: int) -> bool:
    cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--socks5-hostname", f"127.0.0.1:{port}", "--connect-timeout", "2", "--max-time", str(TIMEOUT), URL]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return r.stdout.strip() in ("200", "204")

def test_single_proxy(link: str, port_queue: SimpleQueue) -> Tuple[bool, str]:
    cfg_path = None; proc = None
    try:
        outbound = parse_to_singbox(link)
        if not outbound or "type" not in outbound: return False, link
        port = port_queue.get()
        ok = False
        try:
            cfg_path = create_config_file(outbound, port)
            proc = subprocess.Popen([SING_BOX, "run", "-c", str(cfg_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.2)  
            ok = curl_test(port)
        finally:
            if proc:
                proc.terminate()
                try: proc.wait(timeout=0.5)
                except Exception: proc.kill()
            if cfg_path and cfg_path.exists(): cfg_path.unlink(missing_ok=True)
            port_queue.put(port)
        return ok, link
    except Exception: return False, link

def main():
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    print("📥 Загрузка sing-box...")
    sb_url = "https://github.com/SagerNet/sing-box/releases/download/v1.11.3/sing-box-1.11.3-linux-amd64.tar.gz"
    tar_path = REPO_DIR / "sing-box.tar.gz"
    urllib.request.urlretrieve(sb_url, tar_path)
    subprocess.run(["tar", "-xzf", str(tar_path), "--strip-components=1", "sing-box-1.11.3-linux-amd64/sing-box"], cwd=str(BIN_DIR))
    if os.path.exists(SING_BOX):
        os.chmod(SING_BOX, 0o755)
        tar_path.unlink(missing_ok=True)
    else:
        sys.exit("❌ Ошибка установки ядра sing-box")

    raw_links = []
    pattern = re.compile(r'(vless://|hysteria2://|hy2://|tuic://)[^\s`"\']+', re.IGNORECASE)

    for name, url in SOURCES.items():
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8', errors='ignore')
                (SOURCES_DIR / f"{name}.txt").write_text(content, encoding="utf-8")
                found = [m.group(0) for m in pattern.finditer(content)]
                raw_links.extend(found)
        except Exception as e:
            print(f"⚠️ Ошибка источника [{name}]: {e}")

    unique_links = list(set(raw_links))
    if not unique_links:
        sys.exit("❌ Список уникальных прокси пуст.")

    port_q = SimpleQueue()
    for i in range(BASE_PORT, BASE_PORT + PORTS_NUM): port_q.put(i)

    live = []
    with ThreadPoolExecutor(max_workers=THREADS) as pool:
        futures = [pool.submit(test_single_proxy, ln, port_q) for ln in unique_links]
        for f in as_completed(futures):
            ok, ln = f.result()
            if ok: live.append(ln)

    distributor_path = REPO_DIR / "distributor.txt"
    subscribe_path = REPO_DIR / "subscribe.txt"

    live_content = "\n".join(live)
    distributor_path.write_text(live_content, encoding="utf-8")

    b64_content = base64.b64encode(live_content.encode("utf-8")).decode("utf-8")
    subscribe_path.write_text(b64_content, encoding="utf-8")
    print(f"✅ Успешно проверено. Найдено живых: {len(live)}")

if __name__ == '__main__':
    main()
