import os, json, subprocess, time, socket, logging, concurrent.futures, uuid, re, random
from urllib.parse import urlparse, parse_qs

# Берем настройки из ENV Гитхаба или ставим дефолт
TEST_URL = os.getenv("CHECK_URL", "https://www.google.com/generate_204")
TIMEOUT = int(os.getenv("CHECK_TIMEOUT", 15))
THREADS = int(os.getenv("CHECK_THREADS", 50))
ENGINE_PATH = "./sing-box"
WIDE_SNI_POOL = ["vk.com", "yandex.ru", "mail.ru", "ok.ru", "dzen.ru"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def is_port_open(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except: return False

def build_singbox_config(link, listen_port):
    try:
        url = urlparse(link)
        params = {k: v[0] for k, v in parse_qs(url.query).items()}
        if not link.startswith("vless://"): return None
        
        transport_config = {"type": params.get("type", "tcp")}
        if transport_config["type"] == "ws": transport_config["ws"] = {}
        if transport_config["type"] == "grpc": transport_config["grpc"] = {"service_name": params.get("serviceName", "")}
        
        security = params.get("security", "")
        if security in ["tls", "reality"]:
            transport_config["tls"] = {
                "enabled": True,
                "server_name": params.get("sni", url.hostname),
                "utls": {"enabled": True, "fingerprint": params.get("fp", "chrome")}
            }
            if security == "reality":
                transport_config["tls"]["reality"] = {
                    "enabled": True, "public_key": params.get("pbk", ""), "short_id": params.get("sid", "")
                }
        return {
            "log": {"level": "panic"},
            "inbounds": [{"type": "socks", "listen": "127.0.0.1", "listen_port": listen_port}],
            "outbounds": [{
                "type": "vless", "server": url.hostname, "server_port": int(url.port),
                "uuid": url.username, "flow": params.get("flow", ""),
                "packet_encoding": "xudp", "transport": transport_config
            }]
        }
    except: return None

def test_worker(link, task_id):
    listen_port = 12000 + (task_id % 5000)
    config = build_singbox_config(link, listen_port)
    if not config: return None
    cfg_path = f"cfg_{uuid.uuid4().hex[:6]}.json"
    proc = None
    try:
        with open(cfg_path, "w") as f: json.dump(config, f)
        proc = subprocess.Popen([ENGINE_PATH, "run", "-c", cfg_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(15):
            if is_port_open(listen_port): break
            time.sleep(0.4)
        else: return None
        res = subprocess.run([
            "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
            "--proxy", f"socks5://127.0.0.1:{listen_port}", TEST_URL, "--max-time", str(TIMEOUT)
        ], capture_output=True, text=True)
        if res.stdout.strip() in ["200", "204"]: return link
    except: pass
    finally:
        if proc: proc.terminate()
        if os.path.exists(cfg_path): os.remove(cfg_path)
    return None

def main():
    logging.info(f"🚀 ЗАПУСК МЯГКОГО ЧЕКЕРА (Timeout: {TIMEOUT}s, URL: {TEST_URL})")
    if not os.path.exists("distributor.txt"): return
    with open("distributor.txt", "r") as f:
        proxies = list({l.strip() for l in f if l.strip()})
    
    valid = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as ex:
        futures = {ex.submit(test_worker, p, i): i for i, p in enumerate(proxies)}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: valid.append(res)

    final_list = []
    for link in valid:
        final_list.append(link)
        if "reality" not in link.lower():
            for sni in random.sample(WIDE_SNI_POOL, 1):
                base = link.split('#')[0]
                name = link.split('#')[1] if '#' in link else "Stella"
                sep = "&" if "?" in base else "?"
                forged = f"{base}{sep}sni={sni}#{sni}-{name}"
                final_list.append(forged)

    with open("distributor.txt", "w") as f:
        f.write('\n'.join(list(set(final_list))))
    logging.info(f"✅ Проверка окончена. Найдено живых: {len(valid)}")

if __name__ == '__main__':
    main()
