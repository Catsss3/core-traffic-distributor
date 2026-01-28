
import requests
sources = ['https://raw.githubusercontent.com/Catsss3/assets-distributor/main/distributor.txt', 'https://raw.githubusercontent.com/Catsss3/sys-cache-storage/main/distributor.txt', 'https://raw.githubusercontent.com/Catsss3/web-resource-assets/main/distributor.txt']
def main():
    all_links = set()
    for src in sources:
        try:
            res = requests.get(src, timeout=10)
            if res.status_code == 200:
                all_links.update(res.text.splitlines())
        except: continue
    # Глубокая очистка и лимит для Nekobox
    valid = [l for l in all_links if any(s in l for s in ['vless://', 'vmess://', 'ss://', 'trojan://'])]
    elite = valid[:1000] # Берем 1000 лучших
    with open('distributor.txt', 'w') as f: f.write('\n'.join(elite))
if __name__ == "__main__":
    main()
