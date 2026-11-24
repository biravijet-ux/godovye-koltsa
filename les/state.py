"""Состояние прохождения и файлы игры.

Настоящее сохранение — .lesdata/state.json.
save.txt в папке игры — «болванка»: в ней хранится только флаг управления петлёй
(recurse) и мусор. В акте 3 игрок правит его руками.
"""
import json
import os
import random
import sys
import time
from pathlib import Path

BASE = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
DATA = BASE / ".lesdata"
SAVE = DATA / "state.json"
ENDINGS = DATA / "endings.json"
FAKE_SAVE = BASE / "save.txt"
HINTS = BASE / "подсказки"

ITEM_NAMES = {
    "фонарь": "Фонарь",
    "верёвка": "Верёвка",
    "нож": "Нож",
    "камень": "Камни",
    "грибы": "Опята",
    "сахар": "Кусочки сахара",
}


def new_state():
    return {
        "name": "",
        "stage": "intro",
        "loop": 1,
        "warmth": 6,
        "max_warmth": 6,
        "inv": {"фонарь": 1, "верёвка": 1, "нож": 1, "камень": 0, "грибы": 0},
        "flags": [],
        "seed": random.randint(1, 10 ** 9),
        "nodes": {},       # состояние точек карты акта 2
        "history": [],     # пройденные точки (для «назад» в 2.1)
        "region_path": [],
        "pos": None,       # текущая точка карты
        "region": None,
        "ritual": 0,
        "memory": {},      # что игрок сделал в важных местах (для финала)
        "hints_written": 0.0,
        "started": time.time(),
    }


class State(dict):
    # --- флаги
    def has(self, f):
        return f in self["flags"]

    def set(self, f):
        if f not in self["flags"]:
            self["flags"].append(f)

    def unset(self, f):
        if f in self["flags"]:
            self["flags"].remove(f)

    # --- предметы
    def n(self, item):
        return self["inv"].get(item, 0)

    def add(self, item, k=1):
        self["inv"][item] = max(0, self["inv"].get(item, 0) + k)

    def take(self, item, k=1):
        if self.n(item) >= k:
            self["inv"][item] -= k
            return True
        return False

    # --- тепло
    def hurt(self, k=1):
        self["warmth"] = max(0, self["warmth"] - k)

    def heal(self, k=1):
        self["warmth"] = min(self["max_warmth"], self["warmth"] + k)

    # --- файлы
    def save(self):
        DATA.mkdir(exist_ok=True)
        tmp = SAVE.with_suffix(".tmp")
        tmp.write_text(json.dumps(self, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, SAVE)
        try:  # прячем служебную папку на Windows
            if os.name == "nt":
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(str(DATA), 0x2)
        except Exception:
            pass


def load():
    if SAVE.exists():
        try:
            d = json.loads(SAVE.read_text(encoding="utf-8"))
            base = new_state()
            base.update(d)
            return State(base)
        except Exception:
            pass
    return None


def reset():
    if SAVE.exists():
        SAVE.unlink()
    write_fake_save(True)


# ---------- болванка save.txt ------------------------------------------------

def write_fake_save(recurse=True, note=""):
    junk = random.Random(7)
    lines = [
        "# ГОДОВЫЕ КОЛЬЦА — файл сохранения",
        "# не редактировать вручную",
        f"ver=0.{junk.randint(10, 99)}.{junk.randint(100, 999)}",
        "ring_count=" + str(junk.randint(100, 400)),
        "snow_depth=0.42",
        "last_tree=massive",
        f"recurse={'true' if recurse else 'false'}",
        "lantern_trust=low",
        "echo_buffer=" + "".join(junk.choice("0123456789abcdef") for _ in range(32)),
        "player_is_awake=???",
        "cat_name=Пепел",
        "efim_tea_temperature=горячий",
        "# если ты это читаешь, значит ты полез в файлы. лес это видит.",
        "# привет от Ефима. он не знает что такое файл, но привет передаёт",
        "mushrooms_crooked=1",
        "summer_note=\"приходи ещё\"",
    ]
    if note:
        lines.append("# " + note)
    FAKE_SAVE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_recurse():
    """True / False / None (файл сломан или удалён)."""
    if not FAKE_SAVE.exists():
        return None
    try:
        for line in FAKE_SAVE.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip().lower().replace(" ", "")
            if line.startswith("recurse="):
                v = line.split("=", 1)[1]
                if v in ("false", "0", "no", "нет"):
                    return False
                if v in ("true", "1", "yes", "да"):
                    return True
                return None
    except Exception:
        return None
    return None


# ---------- финалы -----------------------------------------------------------

def endings_seen():
    try:
        return json.loads(ENDINGS.read_text(encoding="utf-8"))
    except Exception:
        return []


def mark_ending(name):
    DATA.mkdir(exist_ok=True)
    seen = endings_seen()
    if name not in seen:
        seen.append(name)
    ENDINGS.write_text(json.dumps(seen, ensure_ascii=False), encoding="utf-8")


# ---------- подсказки в папке ------------------------------------------------

def write_hint(fname, text):
    HINTS.mkdir(exist_ok=True)
    p = HINTS / fname
    p.write_text(text, encoding="utf-8")
    return p


def hints_peeked(since):
    """Пытается понять по времени доступа, открывал ли игрок файлы подсказок.
    Ненадёжно (зависит от ОС), поэтому используется только для шуток."""
    if not HINTS.exists():
        return False
    for p in HINTS.iterdir():
        try:
            st = p.stat()
            if st.st_atime > max(st.st_mtime, since) + 3:
                return True
        except Exception:
            pass
    return False
