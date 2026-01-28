
import os
import json
import subprocess
import time
import concurrent.futures
from urllib.parse import urlparse, parse_qs, unquote

TEST_URL = "http://www.gstatic.com/generate_204"
TIMEOUT = 5
THREADS = 30  # Оптимально, чтобы не забить процессор Гитхаба

def install_xray():
    if not os.path.exists("./xray"):
        print("📥 Загрузка Xray...")
        os.system("curl -L https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip -o xray.zip")
        os.system("unzip -o xray.zip xray && chmod +x xray")

def parse_vless(link):
    try:
        url = urlparse(link)
        params = parse_qs(url.query)
        return {
            "id": url.username,
            "address": url.hostname,
            "port": url.port,
            "sni": params.get("sni", [""])[0],
            "security": params.get("security", ["none"])[0],
            "type": params.get("type", ["tcp"])[0],
            "fp": params.get("fp", [""])[0],
            "pbk": params.get("pbk", [""])[0],
            "sid": params.get("sid", [""])[0],
            "flow": params.get("flow", [""])[0]
        }
    except: return None

def test_worker(vless_link, thread_id):
    listen_port = 10000 + thread_id
    data = parse_vless(vless_link)
    if not data: return None

    # Создаем конфиг для Xray
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

    with open(f"config_{thread_id}.json", "w") as f:
        json.dump(config, f)

    # Запускаем Xray
    proc = subprocess.Popen(["./xray", "-c", f"config_{thread_id}.json"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5) # Даем время подняться

    try:
        # Проверяем через curl
        res = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--proxy", f"socks5://127.0.0.1:{listen_port}", TEST_URL, "--max-time", str(TIMEOUT)],
            capture_output=True, text=True
        )
        if res.stdout.strip() in ["200", "204"]:
            return vless_link
    except: pass
    finally:
        proc.terminate()
        if os.path.exists(f"config_{thread_id}.json"): os.remove(f"config_{thread_id}.json")
    return None

def main():
    install_xray()
    with open("distributor.txt", "r") as f:
        proxies = list(set([l.strip() for l in f.readlines() if l.strip()]))
    
    print(f"🚀 Начинаю прожарку {len(proxies)} прокси в {THREADS} потоков...")
    valid = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(test_worker, proxies[i], i % THREADS): i for i in range(len(proxies))}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res: valid.append(res)
    
    with open("distributor.txt", "w") as f:
        f.write("\n".join(valid))
    print(f"💎 Фильтр пройден! Из {len(proxies)} выжило {len(valid)}. Стелла гордится тобой! 🥂")

if __name__ == "__main__":
    main()
