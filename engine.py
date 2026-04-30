
import os
import re
import asyncio
import aiohttp
from google.colab import userdata

UDP_PROTOCOLS = ["hy2://", "tuic://", "hysteria2://"]
TCP_PROTOCOLS = ["vmess://", "vless://", "trojan://", "ss://", "ssr://", "warp://", "wireguard://"]
ALL_PROTOCOLS = TCP_PROTOCOLS + UDP_PROTOCOLS

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

async def fetch(session, url):
    try:
        async with session.get(url, timeout=20) as r:
            return await r.text() if r.status == 200 else ""
    except: return ""

async def get_goida_files(session, token):
    api_url = "https://api.github.com/repos/AvenCores/goida-vpn-configs/contents/githubmirror"
    headers = {'Authorization': f'token {token}'} if token else {}
    try:
        async with session.get(api_url, headers=headers) as r:
            if r.status == 200:
                resp = await r.json()
                return [item['download_url'] for item in resp if item['name'].endswith('.txt')]
    except: pass
    return []

async def main():
    try: token = userdata.get('WORKFLOW_TOKEN')
    except: token = None
    print("📡 Stella Engine v2.0: Сбор данных...")
    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
        tasks = [fetch(session, url) for url in SOURCES.values()]
        g_urls = await get_goida_files(session, token)
        tasks.extend([fetch(session, url) for url in g_urls])
        all_results = await asyncio.gather(*tasks)
    
    tcp_unique, udp_unique = set(), set()
    regex = r"(" + "|".join(map(re.escape, ALL_PROTOCOLS)) + r")[^\\s\"'<>]+"
    for block in all_results:
        for match in re.finditer(regex, block, flags=re.IGNORECASE):
            link = match.group(0).strip()
            if any(link.startswith(p) for p in UDP_PROTOCOLS): udp_unique.add(link)
            else: tcp_unique.add(link)
    
    with open("raw_configs.txt", "w", encoding="utf-8") as f:
        for l in sorted(tcp_unique): f.write(l + "\n")
    with open("raw_udp.txt", "w", encoding="utf-8") as f:
        for l in sorted(udp_unique): f.write(l + "\n")
    print(f"🏁 Собрано: TCP {len(tcp_unique)}, UDP {len(udp_unique)}")

if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    if loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.gather(main())
    else:
        asyncio.run(main())
