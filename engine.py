
import requests

sources = {'assets-distributor': 'https://raw.githubusercontent.com/Catsss3/assets-distributor/main/distributor.txt', 'sys-cache-storage': 'https://raw.githubusercontent.com/Catsss3/sys-cache-storage/main/distributor.txt', 'web-resource-assets': 'https://raw.githubusercontent.com/Catsss3/web-resource-assets/main/distributor.txt'}

def main():
    total_raw_list = []
    
    print("--- 🕵️‍♀️ Стелла ведет пересчет всех ссылок: ---")
    
    for name, url in sources.items():
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                links = [line.strip() for line in res.text.splitlines() if line.strip()]
                print(f"📦 {name}: {len(links)} строк")
                total_raw_list.extend(links)
            else:
                print(f"⚠️ {name} ответил кодом {res.status_code}")
        except Exception as e:
            print(f"❌ Ошибка в {name}: {e}")
    
    raw_count = len(total_raw_list)
    # Удаляем только дубликаты, сохраняя порядок (насколько это возможно)
    unique_links = []
    seen = set()
    for link in total_raw_list:
        if link not in seen:
            unique_links.append(link)
            seen.add(link)
    
    print(f"\n📊 ВСЕГО В СУММЕ: {raw_count}")
    print(f"💎 ОСТАЛОСЬ ПОСЛЕ УДАЛЕНИЯ ДУБЛЕЙ: {len(unique_links)}")
    
    with open('distributor.txt', 'w') as f:
        f.write('\n'.join(unique_links))
    
    print("\n✅ Работа завершена. Лишнее выбросили! 🥂")

if __name__ == "__main__":
    main()
