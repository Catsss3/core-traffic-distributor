
import requests
import socket
import urllib.parse
import concurrent.futures

sources = {'assets-distributor': 'https://raw.githubusercontent.com/Catsss3/assets-distributor/main/distributor.txt', 'sys-cache-storage': 'https://raw.githubusercontent.com/Catsss3/sys-cache-storage/main/live_configs.txt', 'web-resource-assets': 'https://raw.githubusercontent.com/Catsss3/web-resource-assets/main/core-parser-ts/category/protocols/vless.txt'}

def check_tcp(proxy_link):
    try:
        # Извлекаем хост и порт из vless ссылки
        parsed = urllib.parse.urlparse(proxy_link.split('#')[0])
        netloc = parsed.netloc
        if '@' in netloc:
            address = netloc.split('@')[1]
        else:
            address = netloc
        
        host, port = address.split(':')
        
        # Полноценная попытка открыть TCP соединение (как Nekobox)
        with socket.create_connection((host, int(port)), timeout=3):
            return proxy_link
    except:
        return None

def main():
    total_list = []
    for name, url in sources.items():
        try:
            res = requests.get(url, timeout=20)
            if res.status_code == 200:
                total_list.extend([l.strip() for l in res.text.splitlines() if l.strip()])
        except: continue
    
    unique_links = list(set(total_list))
    print(f"🔍 Начинаю прожарку {len(unique_links)} прокси...")

    # Запускаем проверку в 50 потоков для скорости
    valid_links = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(check_tcp, unique_links)
        for res in results:
            if res:
                valid_links.append(res)

    print(f"✅ Проверку прошли: {len(valid_links)} из {len(unique_links)}")
    
    with open('distributor.txt', 'w') as f:
        f.write('\n'.join(valid_links))
