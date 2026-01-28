
import requests

sources = {'assets-distributor': 'https://raw.githubusercontent.com/Catsss3/assets-distributor/main/distributor.txt', 'sys-cache-storage': 'https://raw.githubusercontent.com/Catsss3/sys-cache-storage/main/live_configs.txt', 'web-resource-assets': 'https://raw.githubusercontent.com/Catsss3/web-resource-assets/main/core-parser-ts/category/protocols/vless.txt'}

def main():
    total_raw_list = []
    print("--- 🕵️‍♀️ Стелла идет по правильным адресам: ---")
    
    for name, url in sources.items():
        try:
            res = requests.get(url, timeout=20)
            if res.status_code == 200:
                links = [line.strip() for line in res.text.splitlines() if line.strip()]
                print(f"✅ {name}: нашла {len(links)} строк")
                total_raw_list.extend(links)
            else:
                print(f"❌ {name} не открыл дверь (код {res.status_code}). Путь: {url}")
        except Exception as e:
            print(f"⚠️ Ошибка на объекте {name}: {e}")
    
    unique_links = []
    seen = set()
    for link in total_raw_list:
        if link not in seen:
            unique_links.append(link)
            seen.add(link)
    
    print(f"\n📊 ОБЩИЙ УЛОВ: {len(total_raw_list)}")
    print(f"💎 ЧИСТЫЙ ВЕС (без дублей): {len(unique_links)}")
    
    with open('distributor.txt', 'w') as f:
        f.write('\n'.join(unique_links))
    
    print("\n✅ База данных синхронизирована! 🥂")

if __name__ == "__main__":
    main()
