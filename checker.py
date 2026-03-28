import os, json, subprocess, time, socket, logging, concurrent.futures, uuid, re, random
from urllib.parse import urlparse, parse_qs

# ------------------- Конфигурация -------------------
TEST_URL = "http://cp.cloudflare.com/"
TIMEOUT = 5
THREADS = 40
ENGINE_PATH = "./sing-box"

WIDE_SNI_POOL = [
    "vk.com", "gosuslugi.ru", "ads.x5.ru", "ozon.ru", "tass.ru",
    "ya.ru", "mail.ru", "avito.ru", "sberbank.ru", "wildberries.ru",
    "edu.ru", "nalog.gov.ru", "rt.ru", "rbc.ru", "mos.ru",
    "mvideo.ru", "dzen.ru", "ok.ru", "hh.ru", "cian.ru"
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ------------------- Вспомогательные функции -------------------
def is_port_open(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except: return False

def build_singbox_config(link, listen_port):
    try:
        url = urlparse(link)
        params = {k: v[0] for k, v in parse_qs(url.query).items()}
        
        if not link.startswith("vless://"): return None

        # Формируем транспорт динамически, чтобы не было лишних null в JSON
        transport_type = params.get("type", "tcp")
        transport_config = {"type": transport_type}
        
        if transport_type == "ws": transport_config["ws"] = {}
        if transport_type == "grpc": transport_config["grpc"] = {"service_name": params.get("serviceName", "")}

        # TLS / Reality настройки
        if params.get("security") in ["tls", "reality"]:
            transport_config["tls"] = {
                "enabled": True,
                "server_name": params.get("sni", url.hostname),
                "utls": {"enabled": True, "fingerprint": params.get("fp", "chrome")}
            }
            if params.get("security") == "reality":
                transport_config["tls"]["reality"] = {
                    "enabled": True,
                    "public_key": params.get("pbk", ""),
                    "short_id": params.get("sid", "")
                }

        return {
            "log": {"level": "panic"},
            "inbounds": [{
                "type": "socks",
                "listen": "127.0.0.1",
                "listen_port": listen_port
            }],
            "outbounds": [{
                "type": "vless",
                "tag": "proxy-out",
                "server": url.hostname,
                "server_port": url.port,
                "uuid": url.username,
                "flow": params.get("flow", ""),
                "packet_encoding": "xudp",
                "transport": transport_config
            }]
        }
    except: return None

# ------------------- Тестовый воркер -------------------
def test_worker(link, task_id):
    listen_port = 10000 + (task_id % 15000)
    config = build_singbox_config(link, listen_port)
    if not config: return None
    
    cfg_path = f"cfg_{uuid.uuid4().hex[:6]}.json"
    proc = None
    try:
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False)
        
        proc = subprocess.Popen([ENGINE_PATH, "run", "-c", cfg_path], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        for _ in range(15):
            if is_port_open(listen_port): break
            time.sleep(0.2)
        else: return None

        res = subprocess.run([
            "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
            "--proxy", f"socks5://127.0.0.1:{listen_port}",
            TEST_URL, "--max-time", str(TIMEOUT)
        ], capture_output=True, text=True)
        
        if res.stdout.strip() in ["200", "204"]:
            return link
    except: pass
    finally:
        if proc:
            proc.terminate()
            try: proc.wait(timeout=1)
            except: proc.kill()
        if os.path.exists(cfg_path): os.remove(cfg_path)
    return None

# ------------------- Основная часть (Кузница) -------------------
def main():
    if not os.path.exists("distributor.txt"): return
    with open("distributor.txt", "r", encoding="utf-8") as f:
        proxies = list({l.strip() for l in f if l.strip()})
    
    logging.info(f"💎 Проверка {len(proxies)} прокси через Sing-box...")
    valid = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as ex:
        futures = {ex.submit(test_worker, proxies[i], i): i for i in range(len(proxies))}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: valid.append(res)

    logging.info(f"✨ Найдено {len(valid)} живых. Начинаю ротацию SNI...")
    
    random.shuffle(valid)
    diverse_valid = valid[:1500]
    final_forged = []

    for link in diverse_valid:
        final_forged.append(link)
        base = re.sub(r"sni=[^&?#]+", "", link).replace("&&", "&").replace("?&", "?").rstrip("&?")
        
        # Генерируем по 3 дополнительных варианта на каждый живой конфиг
        for domain in random.sample(WIDE_SNI_POOL, 3):
            sep = "&" if "?" in base else "?"
            forged = f"{base}{sep}sni={domain}&fp=chrome"
            final_forged.append(forged.replace("?&", "?").replace("&&", "&"))

    with open("distributor.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(list(set(final_forged))))
    
    logging.info(f"🚀 Кузница завершена! В базе {len(final_forged)} конфигов.")

if __name__ == '__main__':
    main()
