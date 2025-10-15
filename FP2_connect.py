#!/usr/bin/env python3
# version 1.6
# Connects to FacePay server (SSH tunnel), keeps interactive console active
# after connection for local commands (e.g. snake.exe, exit, etc.)

import subprocess
import ipaddress
import socket
import time
import webbrowser
import pandas as pd
import os
import re
import glob
from collections import defaultdict
import sys

try:
    import curses
    CURSES_AVAILABLE = True
except Exception:
    CURSES_AVAILABLE = False

PASSWORD = "yourpass"
SEARCH_PATTERNS = ["*FP2*.csv", "*fp2*.csv", "FP2.csv", "fp2.csv"]

# ---------------------------------------------------
# File search
# ---------------------------------------------------
def find_csv_in_folder():
    import sys as _sys
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cwd = os.getcwd()
    search_dirs = [script_dir] + ([cwd] if cwd != script_dir else [])

    candidates = []
    for directory in search_dirs:
        for patt in SEARCH_PATTERNS:
            candidates.extend(glob.glob(os.path.join(directory, patt)))

    candidates = [os.path.abspath(p) for p in candidates if os.path.isfile(p)]
    candidates = sorted(set(candidates), key=os.path.getmtime, reverse=True)

    if not candidates:
        print("❌ Не найдено ни одного CSV файла с шаблоном '*FP2*.csv'.")
        print(f"📂 Проверенные папки: {', '.join(search_dirs)}")
        input("\nНажмите Enter для выхода...")
        _sys.exit(1)

    return candidates[0]

# ---------------------------------------------------
# Load hosts
# ---------------------------------------------------
def load_hosts(csv_path):
    try:
        df = pd.read_csv(csv_path, header=1)
        df.columns = df.columns.str.strip()

        df = df[["Линия", "Вестибюль", "ip сервера", "Название камеры турникета"]].dropna()
        df["Линия"] = df["Линия"].str.strip()
        df["Вестибюль"] = df["Вестибюль"].str.strip()
        df["ip сервера"] = df["ip сервера"].astype(str).str.strip()

        ip_to_tnums = defaultdict(list)
        for _, row in df.iterrows():
            ip = row["ip сервера"]
            nums = re.findall(r"\d+", str(row["Название камеры турникета"]))
            ip_to_tnums[ip].extend(map(int, nums))

        df = df.drop_duplicates(subset=["Линия", "Вестибюль", "ip сервера"]).copy()

        def format_display(row):
            ip = row["ip сервера"]
            if ip_to_tnums[ip]:
                numbers = sorted(set(ip_to_tnums[ip]))
                return f"{row['Линия']} {row['Вестибюль']} | Турникеты: {numbers[0]}–{numbers[-1]} → {ip}"
            return f"{row['Линия']} {row['Вестибюль']} → {ip}"

        df["display_name"] = df.apply(format_display, axis=1)
        return df[["display_name", "ip сервера"]]

    except Exception as e:
        print(f"❌ Ошибка загрузки CSV '{csv_path}': {e}")
        return pd.DataFrame(columns=["display_name", "ip сервера"])

# ---------------------------------------------------
# Helpers
# ---------------------------------------------------
def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def is_port_open(host, port):
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except (OSError, ConnectionRefusedError):
        return False

def wait_for_ports(ports, host="127.0.0.1", timeout=30):
    print("⏳ Ожидаем подключение туннеля...")
    start = time.time()
    while time.time() - start < timeout:
        if all(is_port_open(host, p) for p in ports):
            print("✅ Туннель готов!")
            return True
        time.sleep(0.5)
    print("❌ Не удалось дождаться открытия портов.")
    return False

# ---------------------------------------------------
# Fun stuff
# ---------------------------------------------------
def show_penis():
    """Funny ASCII art."""
    art = r"""
⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠛⢉⢉⠉⠉⠻⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⠟⠠⡰⣕⣗⣷⣧⣀⣅⠘⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⠃⣠⣳⣟⣿⣿⣷⣿⡿⣜⠄⣿⣿⣿⣿⣿
⣿⣿⣿⣿⡿⠁⠄⣳⢷⣿⣿⣿⣿⡿⣝⠖⠄⣿⣿⣿⣿⣿
⣿⣿⣿⣿⠃⠄⢢⡹⣿⢷⣯⢿⢷⡫⣗⠍⢰⣿⣿⣿⣿⣿
⣿⣿⣿⡏⢀⢄⠤⣁⠋⠿⣗⣟⡯⡏⢎⠁⢸⣿⣿⣿⣿⣿
⣿⣿⣿⠄⢔⢕⣯⣿⣿⡲⡤⡄⡤⠄⡀⢠⣿⣿⣿⣿⣿⣿
⣿⣿⠇⠠⡳⣯⣿⣿⣾⢵⣫⢎⢎⠆⢀⣿⣿⣿⣿⣿⣿⣿
⣿⣿⠄⢨⣫⣿⣿⡿⣿⣻⢎⡗⡕⡅⢸⣿⣿⣿⣿⣿⣿⣿
⣿⣿⠄⢜⢾⣾⣿⣿⣟⣗⢯⡪⡳⡀⢸⣿⣿⣿⣿⣿⣿⣿
⣿⣿⠄⢸⢽⣿⣷⣿⣻⡮⡧⡳⡱⡁⢸⣿⣿⣿⣿⣿⣿⣿
⣿⣿⡄⢨⣻⣽⣿⣟⣿⣞⣗⡽⡸⡐⢸⣿⣿⣿⣿⣿⣿⣿
⣿⣿⡇⢀⢗⣿⣿⣿⣿⡿⣞⡵⡣⣊⢸⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⡀⡣⣗⣿⣿⣿⣿⣯⡯⡺⣼⠎⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣧⠐⡵⣻⣟⣯⣿⣷⣟⣝⢞⡿⢹⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⡆⢘⡺⣽⢿⣻⣿⣗⡷⣹⢩⢃⢿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣷⠄⠪⣯⣟⣿⢯⣿⣻⣜⢎⢆⠜⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⡆⠄⢣⣻⣽⣿⣿⣟⣾⡮⡺⡸⠸⣿⣿⣿⣿
⣿⣿⡿⠛⠉⠁⠄⢕⡳⣽⡾⣿⢽⣯⡿⣮⢚⣅⠹⣿⣿⣿
⡿⠋⠄⠄⠄⠄⢀⠒⠝⣞⢿⡿⣿⣽⢿⡽⣧⣳⡅⠌⠻⣿
⠁⠄⠄⠄⠄⠄⠐⡐⠱⡱⣻⡻⣝⣮⣟⣿⣻⣟⣻⡺⣊
"""
    print(art)
    time.sleep(1.5)



def play_snake():
    if not CURSES_AVAILABLE:
        print("⚠️ Модуль curses недоступен. Snake не может быть запущен.")
        input("Нажмите Enter для продолжения...")
        return

    import random, curses
    def _game(stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.keypad(True)
        sh, sw = stdscr.getmaxyx()
        win = curses.newwin(sh - 2, sw - 2, 1, 1)
        win.keypad(True)
        win.nodelay(True)
        win.border()
        
        snake = [(sh // 2, sw // 2 + i) for i in range(3)]
        direction = curses.KEY_LEFT
        food = (sh // 3, sw // 3)
        score = 0
        
        while True:
            win.addstr(0, 2, f" Score: {score} ")
            win.addch(food[0], food[1], ord("*"))
            key = win.getch()
            if key in [ord("q"), ord("Q")]:
                break
            moves = {
                curses.KEY_UP: (-1, 0),
                curses.KEY_DOWN: (1, 0),
                curses.KEY_LEFT: (0, -1),
                curses.KEY_RIGHT: (0, 1),
            }
            if key in moves and (direction, key) not in [
                (curses.KEY_UP, curses.KEY_DOWN),
                (curses.KEY_DOWN, curses.KEY_UP),
                (curses.KEY_LEFT, curses.KEY_RIGHT),
                (curses.KEY_RIGHT, curses.KEY_LEFT),
            ]:
                direction = key
            head_y, head_x = snake[0]
            dy, dx = moves.get(direction, (0, 0))
            new_head = (head_y + dy, head_x + dx)
            if (
                new_head in snake
                or new_head[0] in [0, sh - 3]
                or new_head[1] in [0, sw - 3]
            ):
                win.addstr(sh // 2, sw // 3, f"GAME OVER! SCORE: {score}")
                win.nodelay(False)
                win.getch()
                break
            snake.insert(0, new_head)
            if new_head == food:
                score += 1
                food = (random.randint(1, sh - 4), random.randint(1, sw - 4))
            else:
                tail = snake.pop()
                win.addch(tail[0], tail[1], ord(" "))
            win.addch(new_head[0], new_head[1], ord("#"))
            time.sleep(0.1)
            
    curses.wrapper(_game)

# ---------------------------------------------------
# Connection + interactive local commands
# ---------------------------------------------------
def interactive_console(proc):
    print("\n🟢 Подключение успешно! Вы можете вводить команды:")
    print("  - exit / quit / сtrl+C → закрыть соединение и выйти\n")

    while True:
        try:
            cmd = input("🧩 > ").strip().lower()
            if cmd in ("exit", "quit"):
                print("❌ Отключаюсь...")
                proc.terminate()
                proc.wait()
                print("Соединение завершено.")
                break
            elif cmd in ("snake.exe", "snake"):
                play_snake()
        except KeyboardInterrupt:
            print("\n⛔ Прервано пользователем.")
            proc.terminate()
            break

# ---------------------------------------------------
# Main
# ---------------------------------------------------
def main():
    csv_file = find_csv_in_folder()
    hosts_df = load_hosts(csv_file)
    if hosts_df.empty:
        print("❌ Таблица хостов пуста или недоступна.")
        return

    # Choose station - loop so we can re-prompt on clown trigger
    while True:
        user_input = input("Введите IP или часть названия станции: ").strip()

        # Clown easter egg: user types the prompt itself
        if user_input.lower() in {"ip или часть названия станции", "ip или часть названия станции:"}:
            print("Начинаю форматирование каталога /home/..")
            time.sleep(0.8)
            for i in [3, 2, 1]:
                print(f"{i}...")
                time.sleep(0.6)
            print("🤡\nХа-ха, очень смешно, клоуняра!\n")
            continue
        # Penis easter egg            
        if user_input.lower() in {"пенис", "penis", "Пенис"}:
#            show_penis()
            print("нет.")
            continue
            
        # Проблем нет!            
        if user_input.lower() in {"проблем нет!", "Проблем нет!", "проблем нет", "Проблем нет"}:
            print("✅ Проблем нет! ✅")
            continue      
            
        # Когда вебка?            
        if user_input.lower() in {"Когда вебка?", "Когда вебка", "когда вебка", "когда вебка?"}:
            print("@@ddddori25")
            continue
        # 42           
        if user_input.lower() in {"Главный вопрос жизни, вселенной и вообще", "главный вопрос жизни, вселенной и вообще", "главный вопрос жизни вселенной и вообще", "Главный вопрос жизни вселенной и вообще"}:
            print("42")
            continue
                                      
        # If it's a valid IP, use it
        if is_valid_ip(user_input):
            ip = user_input
            break

        # Otherwise try to match against station list
        mask = hosts_df["display_name"].str.contains(user_input, case=False, na=False)
        if mask.any():
            ip = hosts_df[mask].iloc[0]["ip сервера"]
            break
        else:
            print("⛔ Станция не найдена. Попробуйте ещё раз.\n")
            # loop again to re-prompt

    ssh_command = [
        "sshpass", "-p", PASSWORD,
        "ssh", "proxyhost@10.250.10.15",
        "-N",
        f"-L5160:{ip}:5160",
        f"-L7280:{ip}:7280",
    ]

    print("Подключаюсь...\n")
    proc = subprocess.Popen(ssh_command)

    if wait_for_ports([5160, 7280]):
        print("✅ Подключение успешно!")
        print("VL: http://127.0.0.1:5160")
        print("TV: http://127.0.0.1:7280")
        print("Конфиг TV: http://127.0.0.1:7280/api/camera/nnn\n")
        webbrowser.open("http://127.0.0.1:5160")
        webbrowser.open("http://127.0.0.1:7280")
        interactive_console(proc)
    else:
        print("❌ Подключение неуспешно, завершаю процесс.")
        proc.terminate()


if __name__ == "__main__":
    main()

