import argparse
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

# Попытка подружить с Jupyter/Colab
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

TEST_URL = "https://1.1.1.1/cdn-cgi/trace"
TIMEOUT = 25  # UDP требует терпения
WORKERS = 10 

def build_xray_config(link, socks_port):
    protocol = "hysteria2" if link.startswith("hy2://") else "tuic"
    return {
        "log": {"loglevel": "none"},
        "inbounds": [{
            "port": socks_port,
            "listen": "127.0.0.1",
            "protocol": "socks",
            "settings": {"udp": True}
        }],
        "outbounds": [{
            "protocol": protocol,
            "tag": "proxy",
            "streamSettings": {"network": "udp"},
            "overrideDestination": link
        }]
    }

async def check_one(link, xray_path, socks_port):
    cfg_path = None
    proc = None
    try:
        cfg = build_xray_config(link, socks_port)
        fd, p = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        cfg_path = Path(p)
        cfg_path.write_text(json.dumps(cfg))

        proc = await asyncio.create_subprocess_exec(
            str(xray_path), "-c", str(cfg_path),
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await asyncio.sleep(2) # Время на прогрев QUIC

        curl = await asyncio.create_subprocess_exec(
            "curl", "-s", "-o", "/dev/null", "--max-time", str(TIMEOUT),
            "--proxy", f"socks5h://127.0.0.1:{socks_port}", TEST_URL
        )
        await asyncio.wait_for(curl.wait(), timeout=TIMEOUT+5)
        return curl.returncode == 0
    except:
        return False
    finally:
        if proc:
            try:
                proc.terminate()
                await proc.wait()
            except: pass
        if cfg_path: cfg_path.unlink(missing_ok=True)

async def worker(q, xray_path, out_path, worker_id):
    my_port = 11000 + worker_id # Уникальный порт для каждого воркера
    while True:
        link = await q.get()
        if link is None: break
        
        if await check_one(link, xray_path, my_port):
            print(f"✅ [W{worker_id}] LIVE: {link[:40]}...")
            with open(out_path, "a", encoding="utf-8") as f:
                f.write(link + "\n")
        else:
            print(f"❌ [W{worker_id}] DEAD")
        q.task_done()

async def main_async():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", default="raw_udp.txt")
    parser.add_argument("-o", "--output", default="distributor.txt")
    parser.add_argument("-x", "--xray", default="./XrayChecker/bin/xray")
    args = parser.parse_args()

    xray_p = Path(args.xray)
    if not xray_p.exists():
        print(f"❌ Бинарник Xray не найден по пути: {xray_p}")
        return

    os.chmod(xray_p, 0o755)

    if not Path(args.input).exists():
        print(f"❌ Файл {args.input} не найден!")
        return

    links = [l.strip() for l in Path(args.input).read_text().splitlines() if "://" in l]
    print(f"📡 Stella UDP Pro: Проверяем {len(links)} ссылок на 10 потоках...")

    queue = asyncio.Queue()
    for l in links: await queue.put(l)
    for _ in range(WORKERS): await queue.put(None)

    tasks = [asyncio.create_task(worker(queue, xray_p, args.output, i)) for i in range(WORKERS)]
    await asyncio.gather(*tasks)
    print("🏁 Проверка UDP завершена!")

if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except RuntimeError: # Если уже запущен цикл (как в Colab)
        loop = asyncio.get_event_loop()
        loop.create_task(main_async())
