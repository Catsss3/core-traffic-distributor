import argparse, asyncio, json, os, sys, tempfile
from pathlib import Path

async def check_one(link, xray_path, socks_port):
    cfg_path = None
    proc = None
    try:
        protocol = "hysteria2" if link.startswith("hy2://") else "tuic"
        cfg = {
            "log": {"loglevel": "none"},
            "inbounds": [{"port": socks_port, "listen": "127.0.0.1", "protocol": "socks", "settings": {"udp": True}}],
            "outbounds": [{"protocol": protocol, "tag": "proxy", "streamSettings": {"network": "udp"}, "overrideDestination": link}]
        }
        fd, p = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        cfg_path = Path(p)
        cfg_path.write_text(json.dumps(cfg))

        proc = await asyncio.create_subprocess_exec(
            str(xray_path), "-c", str(cfg_path), 
            stdout=asyncio.subprocess.DEVNULL, 
            stderr=asyncio.subprocess.DEVNULL
        )
        await asyncio.sleep(2) # Время на установку QUIC-сессии

        # Проверка через curl: -k (ignore certs), -L (follow redirects), -s (silent)
        curl = await asyncio.create_subprocess_exec(
            "curl", "-s", "-k", "-L", "-o", "/dev/null", "--max-time", "15", 
            "--proxy", f"socks5h://127.0.0.1:{socks_port}", "https://1.1.1.1/cdn-cgi/trace"
        )
        await asyncio.wait_for(curl.wait(), timeout=20)
        return curl.returncode == 0
    except: return False
    finally:
        if proc: 
            try: proc.terminate(); await proc.wait()
            except: pass
        if cfg_path: cfg_path.unlink(missing_ok=True)

async def worker(q, xray_path, out_path, worker_id):
    my_port = 16000 + worker_id # Смещаем порты выше
    while True:
        link = await q.get()
        if link is None: break
        if await check_one(link, xray_path, my_port):
            print(f"✅ [W{worker_id}] LIVE")
            with open(out_path, "a", encoding="utf-8") as f: 
                f.write(link + "\n")
        q.task_done()

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", default="raw_udp.txt")
    parser.add_argument("-o", "--output", default="distributor.txt")
    parser.add_argument("-x", "--xray", default="./XrayChecker/bin/xray")
    parser.add_argument("-w", "--workers", type=int, default=15)
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        print("❌ Input file not found!")
        return

    links = [l.strip() for l in Path(args.input).read_text().splitlines() if "://" in l]
    print(f"📡 Stella UDP Pro: Checking {len(links)} links with {args.workers} workers...")
    
    q = asyncio.Queue()
    for l in links: await q.put(l)
    for _ in range(args.workers): await q.put(None)
    
    x_path = Path(args.xray).absolute()
    if not x_path.exists():
        print(f"❌ Xray bin not found at {x_path}")
        return
        
    os.chmod(x_path, 0o755)
    
    try:
        await asyncio.gather(*[asyncio.create_task(worker(q, x_path, args.output, i)) for i in range(args.workers)])
    except Exception as e:
        print(f"⚠️ Error during check: {e}")
    finally:
        print("🏁 UDP Check Finished!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
