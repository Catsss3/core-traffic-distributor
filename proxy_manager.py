
import subprocess
import os
import shutil

def run_china_engine():
    print("🚀 Запуск тяжелого двигателя (XrayChecker)...")
    
    # Пути
    base_dir = os.path.dirname(os.path.abspath(__file__))
    checker_dir = os.path.join(base_dir, "XrayChecker")
    input_source = os.path.join(base_dir, "tcp_checker/alive_tcp_full.txt")
    
    if not os.path.exists(checker_dir):
        print("❌ Папка XrayChecker не найдена!")
        return

    # 1. Подготовка: копируем наши 26к ссылок в их папку под именем 'links.txt'
    # Ограничим до 500 штук для теста (чтобы не сжечь минуты прямо сейчас)
    with open(input_source, 'r') as f:
        links = f.readlines()[:500] 
    
    with open(os.path.join(checker_dir, "links.txt"), 'w') as f:
        f.writelines(links)

    # 2. Магия: запускаем их 1847 строк и СРАЗУ кормим ответами
    # Команда '1\nlinks.txt\nn\n' означает: 
    # 1 - начать проверку, links.txt - файл, n - не использовать прокси для скачивания xray
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
        stdout, _ = process.communicate(input=cmd, timeout=300)
        print(stdout) # Увидим, что он там напроверял
    except Exception as e:
        print(f"⚠️ Ошибка при работе двигателя: {e}")

    # 3. Забираем результат
    result_file = os.path.join(checker_dir, "sortedProxy.txt")
    if os.path.exists(result_file):
        shutil.copy(result_file, os.path.join(base_dir, "distributor.txt"))
        print(f"✅ УСПЕХ! Результаты перенесены в основной файл.")
    else:
        print("❌ Китаец ничего не нашел или упал.")

if __name__ == "__main__":
    run_china_engine()
