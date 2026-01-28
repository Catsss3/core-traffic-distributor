
import requests
import socket
import urllib.parse
import concurrent.futures

sources = {'assets-distributor': 'https://raw.githubusercontent.com/Catsss3/assets-distributor/main/distributor.txt', 'sys-cache-storage': 'https://raw.githubusercontent.com/Catsss3/sys-cache-storage/main/live_configs.txt', 'web-resource-assets': 'https://raw.githubusercontent.com/Catsss3/web-resource-assets/main/core-parser-ts/category/protocols/vless.txt'}

def check_tcp(proxy_link):
    try:
        # Убираем лишние пробелы и мусор
        link = proxy_link.strip()
        if not link: return None
        
        # Парсим адрес
        base_part = link.split('#')[0]
        parsed = urllib.parse.urlparse(base_part)
        netloc = parsed.netloc
        
        if '@' in netloc:
            address = netloc.split('@')[1]
        else:
            address = netloc
        
        if ':' not in address: return None
        
        host, port = address.split(':')
        
        # Тот самый жесткий TCP тест
        with socket.create_connection((host, int(port)), timeout=3):
            return link
    except:
        return None

def main():
    total_list = []
    print("--- 🕵️‍♀️ Стелла начинает глубокую проверку ---")
    
    for name, url in sources.items():
        try:
            res = requests.get(url, timeout=20)
            if res.status_code == 200:
                total_list.extend(res.text.splitlines())
        except: continue
    
    unique_links = list(set([l.strip() for l in total_list if l.strip()]))
    print(f"📡 Всего уникальных для теста: {len(unique_links)}")

    valid_links = []
    # Используем больше потоков для скорости (100 вместо 50)
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        results = list(executor.map(check_tcp, unique_links))
        valid_links = [r for r in results if r is not None]

    print(f"🔥 Проверку прошли: {len(valid_links)}")
    
    # КРИТИЧЕСКИ ВАЖНО: Сохраняем результат!
    with open('distributor.txt', 'w') as f:
        f.write('\n'.join(valid_links))
    print("💾 Файл distributor.txt успешно записан!")

if __name__ == "__main__":
    main()
