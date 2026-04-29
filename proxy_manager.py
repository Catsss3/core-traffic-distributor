
import subprocess
import os
import shutil

def run_china_engine():
    print("🚀 ВНИМАНИЕ: Запуск двигателя на ПОЛНУЮ мощность!")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    checker_dir = os.path.join(base_dir, "XrayChecker")
    input_source = os.path.join(base_dir, "tcp_checker/alive_tcp_full.txt")
    
    if not os.path.exists(checker_dir):
        print("❌ Папка XrayChecker не найдена!")
        return

    # 1. Забираем ВООБЩЕ ВСЕ ссылки из TCP-чекера без исключения
    with open(input_source, 'r') as f:
        links = f.readlines()
    
    print(f"📥 Загружено {len(links)} ссылок. Начинаю тотальную проверку...")
    
    with open(os.path.join(checker_dir, "links.txt"), 'w') as f:
        f.writelines(links)

    # 2. Авто-ввод для китайского скрипта
    cmd = "1\nlinks.txt\nn\n"
    
    try:
        process = subprocess.Popen(
            ['python3', 'v2rayChecker.py'],
            cwd=checker_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        # Увеличиваем таймаут до 2 часов (7200 сек), чтобы он успел всё проверить
        stdout, _ = process.communicate(input=cmd, timeout=7200)
        print(stdout)
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")

    # 3. Перенос результата
    result_file = os.path.join(checker_dir, "sortedProxy.txt")
    if os.path.exists(result_file):
        shutil.copy(result_file, os.path.join(base_dir, "distributor.txt"))
        print(f"✅ ФИНИШ! Все живые прокси сохранены.")
    else:
        print("❌ Файл результатов не найден.")

if __name__ == "__main__":
    run_china_engine()
