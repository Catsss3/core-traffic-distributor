import subprocess
import os
import shutil

def run_china_engine():
    print("🚀 ВНИМАНИЕ: Запуск двигателя на ПОЛНУЮ мощность через аргументы!")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    checker_dir = os.path.join(base_dir, "XrayChecker")
    input_source = os.path.join(base_dir, "tcp_checker/alive_tcp_full.txt")
    output_target = os.path.join(base_dir, "distributor.txt")
    
    if not os.path.exists(checker_dir):
        print("❌ Папка XrayChecker не найдена!")
        return

    # Обеспечиваем права на выполнение ядра Xray
    xray_bin = os.path.join(checker_dir, "bin/xray")
    if os.path.exists(xray_bin):
        os.chmod(xray_bin, 0o755)

    # Используем проверенную в Colab команду (без stdin)
    command = [
        "python3", "v2rayChecker.py",
        "-f", input_source,
        "-T", "100",        # 100 потоков для скорости
        "-t", "15",         # Таймаут для URL-теста
        "-o", "sortedProxy.txt",
        "-d", "http://cp.cloudflare.com/generate_204"
    ]
    
    print(f"📥 Начинаю проверку...")
    
    try:
        # Запускаем чекер напрямую. Аргументы исключают зависание меню.
        process = subprocess.Popen(
            command,
            cwd=checker_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Вывод логов в консоль GitHub Actions в реальном времени
        for line in iter(process.stdout.readline, ''):
            print(line.strip())
            
        process.wait(timeout=7200) 
        
    except Exception as e:
        print(f"⚠️ Ошибка в процессе работы: {e}")

    # Перенос результата в distributor.txt
    result_file = os.path.join(checker_dir, "sortedProxy.txt")
    if os.path.exists(result_file):
        shutil.copy(result_file, output_target)
        with open(output_target, 'r') as f:
            count = len(f.readlines())
        print(f"✅ ФИНИШ! {count} прокси сохранены в distributor.txt")
    else:
        print("❌ Файл результатов не найден. Проверьте логи чекера выше.")

if __name__ == "__main__":
    run_china_engine()
