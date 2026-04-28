import os
import re
import base64
import requests
import time
from google.colab import userdata

GITHUB_USER = "Catsss3"
GITHUB_REPO = "core-traffic-distributor"
PROTOCOLS = ["vmess://", "vless://", "trojan://", "ss://", "ssr://", "hy2://", "tuic://", "hysteria2://", "warp://", "wireguard://"]

SOURCES = {
    "cat-hy2": "https://raw.githubusercontent.com/Catsss3/web-assets-static/main/providers/hy2_list.txt",
    "cat-distributor": "https://raw.githubusercontent.com/Catsss3/assets-distributor/main/distributor.txt",
    "cat-cache": "https://raw.githubusercontent.com/Catsss3/sys-cache-storage/main/live_configs.txt",
    "cat-vless": "https://raw.githubusercontent.com/Catsss3/web-resource-assets/main/core-parser-ts/category/protocols/vless.txt",
    "yitong-mining": "https://raw.githubusercontent.com/yitong2333/proxy-minging/main/v2ray.txt",
    "tg-collector": "https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/main/category/vless.txt",
    "mheidari-proxy": "https://raw.githubusercontent.com/mheidari98/.proxy/main/vless",
    "v2ray-dumper": "https://raw.githubusercontent.com/miladtahanian/V2RayCFGDumper/main/sub.txt",
    "lalatina-nodes": "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/nodes",
    "surfboard-mixed": "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/splitted/mixed"
}

def fetch(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        return r.text if r.status_code == 200 else ""
    except: return ""

def get_goida_files(token):
    api_url = "https://api.github.com/repos/AvenCores/goida-vpn-configs/contents/githubmirror"
    files = []
    try:
        headers = {'Authorization': f'token {token}'} if token else {}
        resp = requests.get(api_url, headers=headers).json()
        for item in resp:
            if item['name'].endswith('.txt'):
                files.append(item['download_url'])
    except: pass
    return files

def main():
    token = userdata.get('WORKFLOW_TOKEN')
    all_data = []
    print("📡 Синхронизация...")
    for name, url in SOURCES.items():
        res = fetch(url)
        if res: all_data.append(res)
    
    g_urls = get_goida_files(token)
    for url in g_urls:
        all_data.append(fetch(url))
        time.sleep(0.1)

    # Исправленная регулярка без SyntaxWarning
    regex = r"(" + "|".join(map(re.escape, PROTOCOLS)) + r")[^\s\"']+"
    unique = set()
    for block in all_data:
        for match in re.finditer(regex, block, flags=re.IGNORECASE):
            unique.add(match.group(0).strip())

    with open("raw_configs.txt", "w", encoding="utf-8") as f:
        for l in unique: f.write(l + "\n")
    print(f"🏁 Успех: {len(unique)} конфигов.")

if __name__ == '__main__':
    main()
