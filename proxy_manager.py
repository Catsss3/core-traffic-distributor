import subprocess
import os
import shutil

# Используем абсолютные пути, чтобы не зависеть от того, откуда запущен скрипт
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "tcp_checker/alive_tcp_full.txt")
OUTPUT_FILE = os.path.join(BASE_DIR, "distributor.txt")
CHECKER_DIR = os.path.join(BASE_DIR, "XrayChecker")

def run_check():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Файл {INPUT_FILE} не найден")
        return

    if not os.path.exists(CHECKER_DIR):
        print(f"❌ Папка чекера {CHECKER_DIR} не найдена")
        return

    with open(INPUT_FILE, 'r') as f:
        lines = f.readlines()

    final_results = []
    # Берем кусками по 1000
    for i in range(0, len(lines), 1000):
        chunk = lines[i:i+1000]
        links_path = os.path.join(CHECKER_DIR, "links.txt")
        
        with open(links_path, 'w') as f:
            f.writelines(chunk)
        
        print(f"⏳ Проверяю пачку {i//1000 + 1}...")
        
        # Запуск чекера
        cmd = "1\nlinks.txt\nn\n"
        p = subprocess.Popen(['python3', 'v2rayChecker.py'], 
                             cwd=CHECKER_DIR, stdin=subprocess.PIPE, 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
        p.communicate(input=cmd)

        res_path = os.path.join(CHECKER_DIR, "sortedProxy.txt")
        if os.path.exists(res_path):
            with open(res_path, 'r') as f:
                content = f.readlines()
                final_results.extend(content)
            os.remove(res_path)

    # Убираем дубликаты и сохраняем
    with open(OUTPUT_FILE, 'w') as f:
        f.writelines(list(set(final_results)))
    
    print(f"✅ Проверка окончена. Сохранено в distributor.txt: {len(final_results)}")

if __name__ == "__main__":
    run_check()