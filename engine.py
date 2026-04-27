import requests, re, os

# ОБЪЕДИНЕННЫЙ СПИСОК: Твои оригинальные + Новые мощные источники
SOURCES = {
    # Твои оригинальные репозитории (Catsss3 и др.)
    "cat-hy2": "https://raw.githubusercontent.com/Catsss3/web-assets-static/main/providers/hy2_list.txt",
    "cat-distributor": "https://raw.githubusercontent.com/Catsss3/assets-distributor/main/distributor.txt",
    "cat-cache": "https://raw.githubusercontent.com/Catsss3/sys-cache-storage/main/live_configs.txt",
    "cat-vless": "https://raw.githubusercontent.com/Catsss3/web-resource-assets/main/core-parser-ts/category/protocols/vless.txt",
    "yitong-mining": "https://raw.githubusercontent.com/yitong2333/proxy-minging/main/v2ray.txt",
    "tg-collector": "https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/main/category/vless.txt",
    "mheidari-proxy": "https://raw.githubusercontent.com/mheidari98/.proxy/main/vless",
    "v2ray-dumper": "https://raw.githubusercontent.com/miladtahanian/V2RayCFGDumper/main/sub.txt",
    "lalatina-nodes": "https://raw.githubusercontent.com/LalatinaHub/Mineral/master/result/nodes",
    
    # Новые источники + замена (Mheidari-collector, vfarid и др.)
    "mheidari-coll-vless": "https://raw.githubusercontent.com/Mheidari98/vless-collector/main/sub/vless",
    "mheidari-coll-trojan": "https://raw.githubusercontent.com/Mheidari98/vless-collector/main/sub/trojan",
    "coldwater-vless": "https://raw.githubusercontent.com/coldwater-10/m-vless/main/vless",
    "yebekhe-tvc": "https://raw.githubusercontent.com/yebekhe/TVC/main/api/full/vless",
    "vfarid-all": "https://raw.githubusercontent.com/vfarid/v2ray-share/main/all.txt",
    "xs-vless-new": "https://raw.githubusercontent.com/XS-Official/v2ray-collector/main/vless.txt",
    "yitong-rules": "https://raw.githubusercontent.com/yitong2333/v2ray-rules-dat/master/vless.txt",
    "sadegh-vless": "https://raw.githubusercontent.com/SadeghHoseini/v2ray-configs/master/Vless_Sub.txt"
}

def fetch():
    all_proxies = []
    print("--- 🚀 СТЕЛЛА: Запуск МЕГА-сбора (16 источников) ---")
    headers = {'User-Agent': 'Mozilla/5.0'}
    for name, url in SOURCES.items():
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                # Ищем vless и trojan (и hy2 если есть в твоих списках)
                found = re.findall(r'(vless|trojan|hy2)://[^\s]+', res.text)
                proxies = [f"{p[0]}://{p[1]}" if isinstance(p, tuple) else p for p in found]
                print(f"✅ {name}: получено {len(proxies)} строк")
                all_proxies.extend(proxies)
            else:
                print(f"❌ {name}: ошибка {res.status_code}")
        except:
            print(f"⚠️ {name}: таймаут/ошибка")
    
    unique = list(set(all_proxies))
    with open("distributor.txt", "w") as f:
        f.write('\n'.join(unique))
    print(f"📡 Сбор окончен. Всего уникальных: {len(unique)}")

if __name__ == "__main__":
    fetch()