import argparse, asyncio, json, os, sys, tempfile
from pathlib import Path

async def check_one(link, xray_path, socks_port, debug=False):
    cfg_path = None
    proc = None
    try:
        protocol = "hysteria2" if link.startswith("hy2://") else "tuic"
        cfg = {
            "log": {"loglevel": "info" if debug else "none"},
            "inbounds": [{"port": socks_port, "listen": "127.0.0.1", "protocol": "socks", "settings": {"udp": True}}],
            "outbounds": [{"protocol": protocol, "tag": "proxy", "streamSettings": {"network": "udp"}, "overrideDestination": link}]
        }
        fd, p = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        cfg_path = Path(p)
        cfg_path.write_text(json.dumps(cfg))

        # Включаем вывод ошибок для дебага
        proc = await asyncio.create_subprocess_exec(
            str(xray_path), "-c", str(cfg_path), 
            stdout=asyncio.subprocess.PIPE if debug else asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE if debug else asyncio.subprocess.DEVNULL
        )
        
        await asyncio.sleep(3) # Даем больше времени на старт

        if debug:
            print(f"--- DEBUG XRAY LOG FOR {protocol} ---")
        
        curl = await asyncio.create_subprocess_exec(
            "curl", "-v", "-s", "-k", "-o", "/dev/null", "--max-time", "12", 
            "--proxy", f"socks5h://127.0.0.1:{socks_port}", "https://1.1.1.1/cdn-cgi/trace",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(curl.communicate(), timeout=15)
            if debug and curl.returncode != 0:
                print(f"CURL ERROR LOG:\n{stderr.decode()}")
        except:
            if debug: print("CURL TIMEOUT")
            return False

        return curl.returncode == 0
    except Exception as e:
        if debug: print(f"CRITICAL ERROR: {e}")
        return False
    finally:
        if proc: 
            try: proc.terminate(); await proc.wait()
            except: pass
        if cfg_path: cfg_path.unlink(missing_ok=True)

async def worker(q, xray_path, out_path, worker_id):
    my_port = 17000 + worker_id
    first = True
    while True:
        link = await q.get()
        if link is None: break
        
        # Дебажим только самую первую ссылку в первом воркере
        is_debug = (worker_id == 0 and first)
        if await check_one(link, xray_path, my_port, debug=is_debug):
            print(f"✅ [W{worker_id}] LIVE")
            with open(out_path, "a") as f: f.write(link + "\n")
        first = False
        q.task_done()

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", default="raw_udp.txt")
    parser.add_argument("-o", "--output", default="distributor.txt")
    parser.add_argument("-x", "--xray", default="./XrayChecker/bin/xray")
    parser.add_argument("-w", "--workers", type=int, default=15)
    args = parser.parse_args()
    
    if not Path(args.input).exists(): return
    links = [l.strip() for l in Path(args.input).read_text().splitlines() if "://" in l]
    print(f"📡 Stella UDP Debug Mode: Checking {len(links)} links...")
    
    q = asyncio.Queue()
    for l in links: await q.put(l)
    for _ in range(args.workers): await q.put(None)
    
    x_path = Path(args.xray).absolute()
    await asyncio.gather(*[asyncio.create_task(worker(q, x_path, args.output, i)) for i in range(args.workers)])

if __name__ == "__main__":
    asyncio.run(main())
