import requests
import socket
import urllib.parse
import concurrent.futures

sources = {
    'my-main-hy2-3k': 'https://raw.githubusercontent.com/Catsss3/web-assets-static/main/providers/hy2_list.txt',
    'assets-distributor': 'https://raw.githubusercontent.com/Catsss3/assets-distributor/main/distributor.txt',
    'sys-cache-storage': 'https://raw.githubusercontent.com/Catsss3/sys-cache-storage/main/live_configs.txt',
    'web-resource-assets': 'https://raw.githubusercontent.com/Catsss3/web-resource-assets/main/core-parser-ts/category/protocols/vless.txt',
    'yitong2333': 'https://raw.githubusercontent.com/yitong2333/proxy-minging/main/v2ray.txt',
    'vless-collector': 'https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/main/category/vless.txt',
    'mheidari98': 'https://raw.githubusercontent.com/mheidari98/.proxy/main/vless',
    'v2ray-worker': 'https://raw.githubusercontent.com/miladtahanian/V2RayCFGDumper/main/sub.txt',
    'xs-vless': 'https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/nodes'
}

def check_tcp(proxy_link):
    try:
        link = proxy_link.strip()
        allowed = ('vless://', 'hysteria2://', 'hy2://', 'tuic://', 'vmess://', 'trojan://', 'ss://')
        if not link or not link.lower().startswith(allowed): return None
        base_part = link.split('#')[0]
        parsed = urllib.parse.urlparse(base_part)
        netloc = parsed.netloc
        address = netloc.split('@')[1] if '@' in netloc else netloc
        if ':' not in address: return None
        host, port = address.split(':')
        with socket.create_connection((host, int(port)), timeout=3):
            return link
    except: return None

def main():
    total_list = []
    print(f"--- 🕵️‍♀️ Стелла собирает базу из {len(sources)} источников ---")
    for name, url in sources.items():
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                lines = [l.strip() for l in res.text.splitlines() if '://' in l]
                total_list.extend(lines)
                print(f"✅ {name}: получено {len(lines)} строк")
        except: continue
    unique_links = list(set(total_list))
    print(f"📡 Всего уникальных для TCP-теста: {len(unique_links)}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        results = list(executor.map(check_tcp, unique_links))
        valid_links = [r for r in results if r is not None]
    print(f"🔥 Прошли TCP-фильтр: {len(valid_links)}")
    with open('distributor.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(valid_links))
    print("💾 Файл distributor.txt обновлен!")

if __name__ == '__main__': main()
