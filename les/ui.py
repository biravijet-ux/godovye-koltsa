"""Вывод в терминал: цвета, рамки, печать по буквам, выбор вариантов, переходы."""
import os
import random
import shutil
import sys
import textwrap
import time

TITLE = "ГОДОВЫЕ КОЛЬЦА"

WIN = os.name == "nt"
if WIN:
    import msvcrt
    # Не запускаем cmd.exe ради цветов: у фонового пульта это мигает окном.
    import ctypes
    _console = ctypes.windll.kernel32
    _handle = _console.GetStdHandle(-11)
    _mode = ctypes.c_ulong()
    if _console.GetConsoleMode(_handle, ctypes.byref(_mode)):
        _console.SetConsoleMode(_handle, _mode.value | 0x0004)

for _s in (sys.stdout, sys.stdin):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

FAST = False          # без печати по буквам и анимаций (--fast)
TTY = sys.stdin.isatty() and sys.stdout.isatty()

# Режим для тестировщика-нейросети: ввод из файла, вывод в файл (см. agent.py)
AGENT_DIR = os.environ.get("LES_AGENT")
_agent_seq = [0]
SCREEN_BREAK = "═════════════ новый экран ═════════════"


def agent_input(prompt):
    from pathlib import Path
    d = Path(AGENT_DIR)
    sys.stdout.write(prompt + "\n")
    sys.stdout.flush()
    _agent_seq[0] += 1
    n = _agent_seq[0]
    (d / "wait.txt").write_text(str(n), encoding="utf-8")
    start = time.time()
    while time.time() - start < 3600:
        f = d / "in.txt"
        if f.exists():
            try:
                data = f.read_text(encoding="utf-8")
            except OSError:
                data = ""
            head, _, text = data.partition("\t")
            if head == str(n):
                text = text.rstrip("\n")
                sys.stdout.write(f"[ввод: {text}]\n")
                return text
        time.sleep(0.05)
    sys.exit(0)
GLOBAL_HANDLER = None  # функция(cmd) -> bool, ставится из main.py
IN_ENCOUNTER = False


class C:
    R = "\033[0m"
    B = "\033[1m"
    DIM = "\033[2m"
    IT = "\033[3m"
    RED = "\033[31m"
    GRN = "\033[32m"
    YEL = "\033[33m"
    BLU = "\033[34m"
    MAG = "\033[35m"
    CYN = "\033[36m"
    WHT = "\033[97m"
    GRY = "\033[90m"
    INV = "\033[7m"


def paint(text, *styles):
    return "".join(styles) + str(text) + C.R


def width():
    return max(50, min(shutil.get_terminal_size((80, 24)).columns - 2, 78))


def clear():
    if TTY:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()
    else:
        print("\n" + SCREEN_BREAK)


def _key_pressed():
    if not TTY or not WIN:
        return False
    hit = False
    while msvcrt.kbhit():
        msvcrt.getwch()
        hit = True
    return hit


def sleep(sec):
    if FAST or not TTY:
        return
    end = time.time() + sec
    while time.time() < end:
        if _key_pressed():
            return
        time.sleep(0.02)


def type_out(text, style="", delay=0.016, end="\n"):
    """Печатает текст по буквам. Любая клавиша — допечатать сразу."""
    if FAST or not TTY:
        sys.stdout.write(style + text + (C.R if style else "") + end)
        sys.stdout.flush()
        return
    sys.stdout.write(style)
    for i, ch in enumerate(text):
        if _key_pressed():
            sys.stdout.write(text[i:])
            break
        sys.stdout.write(ch)
        sys.stdout.flush()
        if ch in ".!?…":
            time.sleep(delay * 8)
        elif ch in ",;:—":
            time.sleep(delay * 4)
        else:
            time.sleep(delay)
    sys.stdout.write((C.R if style else "") + end)
    sys.stdout.flush()


def say(text, style="", delay=0.016, indent="  "):
    """Абзацы через пустую строку, перенос по ширине терминала."""
    for para in text.strip("\n").split("\n"):
        if not para.strip():
            print()
            continue
        wrapped = textwrap.fill(para.strip(), width() - len(indent),
                                initial_indent=indent, subsequent_indent=indent)
        type_out(wrapped, style, delay)


def narr(text):
    say(text, C.WHT)


def thought(text):
    say(text, C.IT + C.GRY)


def voice(who, text, style=C.YEL):
    """Реплика персонажа, перенос строк с отступом."""
    lines = textwrap.wrap(f"{who}: {text}", width() - 4)
    first = lines[0][len(who) + 1:] if lines else ""
    type_out(f"  {paint(who + ':', C.B, style)}", end="")
    type_out(first, style)
    for line in lines[1:]:
        type_out("  " + line, style)


def danger(text):
    say(text, C.RED)


def good(text):
    say(text, C.GRN)


def dim(text):
    say(text, C.GRY, delay=0.008)


def box(lines, title="", style=C.GRN, w=None):
    w = w or width()
    inner = w - 4
    out = []
    head = f" {title} " if title else ""
    out.append(paint("╭─" + head + "─" * max(0, inner - len(head)) + "─╮", style))
    for line in lines:
        for part in (textwrap.wrap(line, inner) or [""]):
            out.append(paint("│ ", style) + part.ljust(inner) + paint(" │", style))
    out.append(paint("╰" + "─" * (inner + 2) + "╯", style))
    print("\n".join(out))


def header(place, sub="", style=C.GRN):
    clear()
    print()
    print(paint(f"  ❧ {place}", C.B, style) + (paint(f"   {sub}", C.GRY) if sub else ""))
    print(paint("  " + "─" * (width() - 4), C.GRY))


def pause(msg="Enter — дальше"):
    if AGENT_DIR:
        agent_input(f"  [{msg}]")
        return
    if not TTY:
        try:
            input()
        except EOFError:
            sys.exit(0)
        return
    try:
        input(paint(f"  [{msg}] ", C.GRY))
    except EOFError:
        sys.exit(0)


def _raw_input(prompt="> "):
    if AGENT_DIR:
        return agent_input("  " + prompt).strip()
    try:
        return input(paint("  " + prompt, C.B, C.GRN)).strip()
    except EOFError:
        print()
        sys.exit(0)
    except KeyboardInterrupt:
        print()
        sys.exit(0)


def raw_input(prompt="> "):
    from . import project_info
    while True:
        value = _raw_input(prompt)
        if value.strip() != project_info.CODE:
            return value
        project_info.show()


def plural(n, one, few, many):
    """1 опёнок, 2 опёнка, 5 опят."""
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def ask(options, prompt="> ", hidden=None, title=None):
    """options: список (ключ, текст) или (ключ, текст, стиль).
    hidden: словарь {введённое слово: ключ} — скрытые команды.
    Возвращает ключ выбранного варианта."""
    hidden = hidden or {}
    print()
    if len(options) == 1 and not title:
        # один вариант: не меню, а просто «Enter — дальше» (свои слова всё равно работают)
        key, label = options[0][0], options[0][1]
        while True:
            s = raw_input(f"[Enter — {label}] ").lower()
            if s in ("", "1") or s == label.lower():
                return key
            if s in hidden:
                return hidden[s]
            if GLOBAL_HANDLER and GLOBAL_HANDLER(s):
                continue
            print(paint("  Не понимаю. Просто нажми Enter.", C.GRY))
    if title:
        print(paint("  " + title, C.GRY))
    for i, opt in enumerate(options, 1):
        key, label = opt[0], opt[1]
        st = opt[2] if len(opt) > 2 else ""
        print(f"   {paint(str(i), C.B, C.YEL)}) {paint(label, st) if st else label}")
    while True:
        s = raw_input(prompt)
        low = s.lower()
        if low.isdigit() and 1 <= int(low) <= len(options):
            return options[int(low) - 1][0]
        for opt in options:
            if low and low == opt[1].lower():
                return opt[0]
        if low in hidden:
            return hidden[low]
        if GLOBAL_HANDLER and low and GLOBAL_HANDLER(low):
            continue
        if low:
            print(paint("  Не понимаю. Введи номер варианта (или «помощь»).", C.GRY))


# ---------- переходы между местами -------------------------------------------

BIOMES = {
    "snow":   ("  ^   ", " .  . "),
    "birch":  (" | |  ", " .  ."),
    "spruce": (" ▲ ▲▲ ", "  ..  "),
    "bog":    ("  ⸙   ", " ~~ ~ "),
    "mine":   (" ▓▒  ", " ‗‗‗ "),
    "ash":    (" ¦  ' ", " ░ .░ "),
    "ridge":  (" ⌂ ▲  ", " ▒▒ ▒ "),
    "glitch": (" █▓▒░ ", " ░▒▓█ "),
    "oak":    (" ♣ ♣  ", " ⁂ ⁂  "),
}


def transition(a="snow", b="snow", text=""):
    """Короткий переход без прокрутки и шагающего персонажа."""
    if text:
        dim(text)


GLITCH_CH = "█▓▒░#%&@¤§"


def glitch(text, p=0.12, seed=None):
    rng = random.Random(seed)
    return "".join(ch if (ch == " " or rng.random() > p) else rng.choice(GLITCH_CH) for ch in text)


def glitch_say(text, p=0.1):
    say(glitch(text, p), C.MAG)
