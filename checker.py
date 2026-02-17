import os, json, subprocess, time, socket, logging, concurrent.futures, uuid
from typing import Optional
from urllib.parse import urlparse, parse_qs

TEST_URL = "http://cp.cloudflare.com/"
TIMEOUT = 5
THREADS = 40 
XRAY_PATH = "./xray"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def is_port_open(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except OSError: return False

def parse_vless(link: str) -> Optional[dict]:
    try:
        url = urlparse(link)
        params = parse_qs(url.query)
        return {
            "id": url.username, "address": url.hostname, "port": url.port,
            "sni": params.get("sni", [""])[0], "security": params.get("security", ["none"])[0],
            "type": params.get("type", ["tcp"])[0], "fp": params.get("fp", [""])[0],
            "pbk": params.get("pbk", [""])[0], "sid": params.get("sid", [""])[0],
            "flow": params.get("flow", [""])[0]
        }
    except: return None

def test_worker(vless_link: str, task_id: int) -> Optional[str]:
    unique_id = f"{task_id}_{uuid.uuid4().hex[:6]}"
    listen_port = 10000 + (task_id % 15000)
    data = parse_vless(vless_link)
    if not data: return None

    config = {
        "log": {"loglevel": "none"},
        "inbounds": [{"port": listen_port, "protocol": "socks", "settings": {"udp": True}}],
        "outbounds": [{
            "protocol": "vless",
            "settings": {"vnext": [{"address": data["address"], "port": int(data["port"]), "users": [{"id": data["id"], "encryption": "none", "flow": data["flow"]}]}]},
            "streamSettings": {
                "network": data["type"], "security": data["security"],
                "tlsSettings": {"serverName": data["sni"], "fingerprint": data["fp"]} if data["security"] == "tls" else {},
                "realitySettings": {"serverName": data["sni"], "fingerprint": data["fp"], "publicKey": data["pbk"], "shortId": data["sid"]} if data["security"] == "reality" else {}
            }
        }]
    }

    cfg_path = f"config_{unique_id}.json"
    proc = None
    try:
        with open(cfg_path, "w") as f: json.dump(config, f)
        proc = subprocess.Popen([XRAY_PATH, "-c", cfg_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(10):
            if is_port_open(listen_port): break
            time.sleep(0.1)
        else: return None
        res = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--proxy", f"socks5://127.0.0.1:{listen_port}", TEST_URL, "--max-time", str(TIMEOUT)], capture_output=True, text=True)
        if res.stdout.strip() in ["200", "204"]:
            logging.info(f"OK: {data['address']}")
            return vless_link
    except: pass
    finally:
        if proc:
            proc.terminate()
            try: proc.wait(timeout=1)
            except: proc.kill()
        if os.path.exists(cfg_path): os.remove(cfg_path)
    return None

def main():
    if not os.path.exists("distributor.txt"): return
    with open("distributor.txt", "r") as f:
        proxies = list(set([l.strip() for l in f.readlines() if l.strip()]))
    logging.info(f"🚀 Стелла исправляет гонку и тестит {len(proxies)} прокси...")
    valid = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(test_worker, proxies[i], i): i for i in range(len(proxies))}
        for future in concurrent.futures.as_completed(futures):
            try:
                res = future.result()
                if res: valid.append(res)
            except: pass
    with open("distributor.txt", "w") as f: f.write("\n".join(valid))
    logging.info(f"💎 Финал: {len(valid)} живых.")

if __name__ == '__main__':
    main()
