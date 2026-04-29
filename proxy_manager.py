import subprocess
import os
import shutil

INPUT_FILE = "tcp_checker/alive_tcp_full.txt"
OUTPUT_FILE = "distributor.txt"
CHECKER_DIR = "XrayChecker"

def run_check():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Файл {INPUT_FILE} не найден")
        return

    with open(INPUT_FILE, 'r') as f:
        lines = f.readlines()

    final_results = []
    for i in range(0, len(lines), 1000):
        chunk = lines[i:i+1000]
        with open(os.path.join(CHECKER_DIR, "links.txt"), 'w') as f:
            f.writelines(chunk)
        
        cmd = "1\nlinks.txt\nn\n"
        p = subprocess.Popen(['python3', 'v2rayChecker.py'], 
                             cwd=CHECKER_DIR, stdin=subprocess.PIPE, 
                             stdout=subprocess.DEVNULL, text=True)
        p.communicate(input=cmd)

        res_path = os.path.join(CHECKER_DIR, "sortedProxy.txt")
        if os.path.exists(res_path):
            with open(res_path, 'r') as f:
                final_results.extend(f.readlines())
            os.remove(res_path)

    with open(OUTPUT_FILE, 'w') as f:
        f.writelines(list(set(final_results)))
    print(f"✅ Проверка окончена. Найдено: {len(final_results)}")

if __name__ == "__main__":
    run_check()