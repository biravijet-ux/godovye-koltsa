"""Сцена-тропа: короткая тактическая головоломка с существами.

Тропа — ряд клеток 0..L-1, выход в последней. У некоторых клеток есть кусты
(карман сбоку), некоторые клетки — промоины. Ход существ виден заранее.
"""
import random

from . import ui
from .ui import C, paint

CREATURES = {
    "шорох": dict(glyph="Ш", name="Шорох", harmful=True,
                  rule="Слепой. Услышав шум, идёт к этому месту по 2 клетки за ход, пока не дойдёт. "
                       "Новый шум сбивает его на новое место. В тишине чует тебя только вплотную."),
    "теплоед": dict(glyph="Т", name="Теплоед", harmful=True,
                    rule="Ползёт к свету. Без света чует тепло на 2 клетки. У оставленного фонаря засыпает. "
                         "Боится ножа: после удара уползает в кусты, если они в двух шагах, и дремлет пару ходов. "
                         "Кустов рядом нет — отлетает на клетку и 2 хода приходит в себя."),
    "пересмешник": dict(glyph="П", name="Пересмешник", harmful=False,
                        rule="Безвреден. На следующий ход повторяет у себя любой шум, который услышал."),
    "сторож": dict(glyph="С", name="Сторож", harmful=True,
                   rule="Медленно идёт к тебе. Нож ранит его."),
}


RULES = ("Как это работает. Ты идёшь по тропе слева направо к выходу ⌂. После каждого твоего действия "
         "ходят звери, и что они сделают, написано заранее под тропой. Шаг тихий, бег шумный. "
         "Брошенный камень шумит там, куда упал: в кустах ♣ зверь застрянет на пару ходов. "
         "~ полынья: верёвка или холодная вода. # хворост хрустит под ногой. о камень можно подобрать. "
         "Если зверь налетит, потеряешь тепло.")


class Encounter:
    def __init__(self, st, title, length, creatures, bushes=(), gaps=(), dark=False,
                 hard=False, intro="", place="", start=0, keep_rope=False, tutor=None,
                 items=(), brush=()):
        self.st = st
        self.tutor = tutor
        self.items = set(items)      # клетки, где лежит камень (подобрать, наступив)
        self.brush = set(brush)      # хворост: хрустит под ногой, даже если идёшь тихо
        self.turn = 0
        self.keep_rope = keep_rope
        self.title = title
        self.place = place
        self.intro = intro
        self.L = length
        self.p = start
        self.cr = []
        for t, pos, *rest in creatures:
            self.cr.append(dict(type=t, pos=pos, bush=bool(rest and rest[0]), linger=0, stun=0,
                                warming=False, hp=3, gone=False))
        self.bushes = set(bushes)
        self.gaps = set(gaps)
        self.roped = set()
        self.lights = []
        self.lamp_on = False
        self.lamp_left = False
        self.echo_pending = []
        self.marks = []           # шум прошлого хода (для отрисовки)
        self.log = []
        self.dark = dark
        self.hard = hard
        self.dmg = 1
        self.used = {"камень": 0, "нож": 0, "верёвка": 0, "фонарь": 0}

    # ------------------------------------------------------------------ helpers
    def passable(self, cell):
        return cell not in self.gaps or cell in self.roped

    def active(self):
        return [c for c in self.cr if not c["gone"]]

    def visible(self, c):
        if not self.dark or self.lamp_on or self.st.has("canary_alive"):
            return True
        if any(abs(l - c["pos"]) <= 1 for l in self.lights):
            return True
        return abs(c["pos"] - self.p) <= 1

    def harmful(self, c):
        return CREATURES[c["type"]]["harmful"] and not c["warming"] and not c["gone"]

    def blocker_at(self, cell):
        for c in self.active():
            if c["pos"] == cell and not c["bush"] and self.harmful(c) and c["stun"] == 0:
                return c
        return None

    # ---------------------------------------------------------------- AI
    def decide(self, c, noises):
        t = c["type"]
        if c["gone"]:
            return ("idle", None, "")
        if c["stun"] > 0:
            return ("stun", None, "оглушён, пропускает ход")
        if t == "шорох":
            if c["linger"] > 0:
                return ("linger", None, "роется в кустах" if c["bush"] else "обнюхивает место шума")
            if noises:
                cell, bush, _ = noises[-1]
                where = f"кусты у {cell}" if bush else f"клетка {cell}"
                return ("go", (cell, bush), f"идёт на шум → {where}")
            if c.get("target"):
                cell, bush = c["target"]
                where = f"кусты у {cell}" if bush else f"клетка {cell}"
                return ("go", (cell, bush), f"всё ещё идёт к месту шума → {where}")
            if abs(c["pos"] - self.p) <= 1 and not c["bush"]:
                return ("go", (self.p, False), "чует тебя вплотную!")
            return ("idle", None, "слушает тишину")
        if t == "теплоед":
            if c["linger"] > 0:
                return ("linger", None, "дремлет в кустах" if c["bush"] else "приходит в себя")
            if c["warming"]:
                return ("idle", None, "спит у фонаря")
            srcs = [(l, "фонарь") for l in self.lights]
            if self.lamp_on:
                srcs.append((self.p, "тебя"))
            if srcs:
                cell, what = min(srcs, key=lambda s: abs(s[0] - c["pos"]))
                return ("go", (cell, False), f"ползёт к свету ({what})")
            if abs(c["pos"] - self.p) <= 2:
                return ("go", (self.p, False), "чует твоё тепло!")
            return ("idle", None, "дремлет")
        if t == "пересмешник":
            heard = [n for n in noises if n[2] != "эхо"]
            return ("echo" if heard else "idle", None,
                    "повторит услышанный шум" if heard else "молчит, слушает")
        if t == "сторож":
            if c["linger"] > 0:
                return ("linger", None, "переводит дух")
            return ("go", (self.p, False), "идёт к тебе, не торопясь")
        return ("idle", None, "")

    def speed(self, c):
        return {"шорох": 2, "теплоед": 2 if self.hard else 1, "сторож": 1}.get(c["type"], 0)

    def move_creature(self, c, target):
        cell, bush = target
        name = CREATURES[c["type"]]["name"]
        if c["bush"]:
            c["bush"] = False
            if cell == c["pos"] and bush:
                c["bush"] = True
                c["linger"] = 1
                return
        steps = self.speed(c)
        while steps > 0 and c["pos"] != cell:
            c["pos"] += 1 if cell > c["pos"] else -1
            steps -= 1
            if c["pos"] == self.p and self.harmful(c):
                self.contact(c)
                return
        if c["pos"] == cell:
            c.pop("target", None)
            if bush and cell in self.bushes:
                c["bush"] = True
                c["linger"] = 1 if self.hard else 2
                self.log.append(paint(f"{name} ныряет в кусты у {cell} и роется там.", C.GRY))
            elif c["type"] == "теплоед" and cell in self.lights:
                c["warming"] = True
                self.log.append(paint("Теплоед обвивается вокруг фонаря и затихает.", C.GRN))
            elif cell == self.p and self.harmful(c):
                self.contact(c)
            elif c["type"] == "шорох":
                c["linger"] = 1

    def contact(self, c):
        name = CREATURES[c["type"]]["name"]
        self.st.hurt(self.dmg)
        c.pop("target", None)
        self.log.append(paint(f"{name} налетает на тебя! Больно и холодно. −{self.dmg} тепла.", C.RED, C.B))
        back = self.p - 1
        if back >= 0 and self.passable(back):
            self.p = back
        c["linger"] = 1

    def creatures_turn(self, noises_now):
        noises = self.echo_pending + noises_now
        self.echo_pending = []
        for c in self.active():
            kind, target, _ = self.decide(c, noises)
            if kind == "stun":
                c["stun"] -= 1
            elif kind == "linger":
                c["linger"] -= 1
                if c["linger"] == 0 and c["bush"] and c["type"] == "шорох":
                    pass  # вылезет на следующем ходу, если что-то услышит
            elif kind == "go":
                if c["type"] == "шорох" and noises:
                    c["target"] = (noises[-1][0], noises[-1][1])
                self.move_creature(c, target)
            elif kind == "echo":
                self.echo_pending.append((c["pos"], c["bush"], "эхо"))
                self.log.append(paint("Пересмешник запомнил звук. Повторит его на следующем ходу.", C.MAG))
        self.marks = [(n[0], n[1]) for n in noises]

    # ---------------------------------------------------------------- render
    def render(self):
        ui.header(self.title, self.place)
        if self.intro:
            ui.dim(self.intro)
        cells, bushrow = [], []
        for i in range(self.L):
            ch, st = "·", C.GRY
            if i in self.gaps:
                ch, st = ("=", C.YEL) if i in self.roped else ("~", C.BLU)
            if i in self.brush:
                ch, st = "#", C.YEL
            if i in self.items:
                ch, st = "о", C.WHT
            if i in self.lights:
                ch, st = "☼", C.YEL
            if i == self.L - 1:
                ch, st = "⌂", C.GRN
            in_path = [c for c in self.active() if c["pos"] == i and not c["bush"]]
            in_bush = [c for c in self.active() if c["pos"] == i and c["bush"]]
            for c in in_path:
                if self.visible(c):
                    ch = CREATURES[c["type"]]["glyph"] if len(in_path) == 1 else "2"
                    st = C.RED if self.harmful(c) else (C.GRN if c["warming"] else C.MAG)
                else:
                    ch, st = "?", C.GRY
            if i == self.p:
                ch, st = "@", (C.YEL + C.B) if self.lamp_on else (C.WHT + C.B)
            if (i, False) in self.marks and ch == "·":
                ch, st = "!", C.YEL
            cells.append(paint(f"[{ch}]", st))
            if i in self.bushes:
                b, bs = "♣", C.GRN
                for c in in_bush:
                    if self.visible(c):
                        b, bs = CREATURES[c["type"]]["glyph"], C.RED if CREATURES[c["type"]]["harmful"] else C.MAG
                    else:
                        b, bs = "?", C.GRY
                if (i, True) in self.marks and b == "♣":
                    b, bs = "!", C.YEL
                bushrow.append(paint(f" {b} ", bs))
            else:
                bushrow.append("   ")
        nums = "".join(f" {i} " if i < 10 else f"{i} " for i in range(self.L))
        stacked = []
        for i in range(self.L):
            for in_bush in (False, True):
                here = [c for c in self.active() if c["pos"] == i and c["bush"] == in_bush and self.visible(c)]
                if len(here) > 1:
                    where = f"в кустах у {i}" if in_bush else f"клетка {i}"
                    stacked.append(f"{where}: " + " и ".join(CREATURES[c["type"]]["name"] for c in here))
        print()
        print("  " + paint("кусты ", C.GRY) + "".join(bushrow))
        print("  " + paint("тропа ", C.GRY) + "".join(cells))
        print("  " + "      " + paint(nums, C.GRY))
        legend = ["@ ты", "⌂ выход"]
        if self.gaps:
            legend.append("~ полынья")
        if self.roped:
            legend.append("= верёвка")
        if self.brush:
            legend.append("# хворост (хрустит)")
        if self.items:
            legend.append("о камень")
        legend += ["♣ кусты", "! шум"]
        print(paint("  " + "   ".join(legend), C.GRY))
        for line in stacked:
            print(paint("  ! Двое в одном месте, " + line, C.RED))
        print()
        lamp = "горит" if self.lamp_on else ("оставлен" if self.lamp_left else ("выключен" if self.st.n("фонарь") else "нет"))
        print("  " + paint(f"Тепло {'♥' * self.st['warmth']}{'·' * (self.st['max_warmth'] - self.st['warmth'])}", C.RED)
              + paint(f"   камни: {self.st.n('камень')}   верёвка: {self.st.n('верёвка')}   фонарь: {lamp}", C.GRY))
        print()
        print(paint("  Следующий ход (если будешь тихо):", C.GRY))
        for c in self.active():
            info = CREATURES[c["type"]]
            if not self.visible(c):
                print(paint("   ? — что-то шевелится в темноте", C.GRY))
                continue
            _, _, desc = self.decide(c, list(self.echo_pending))
            where = f"кусты у {c['pos']}" if c["bush"] else f"клетка {c['pos']}"
            print(f"   {paint(info['glyph'], C.B, C.RED if info['harmful'] else C.MAG)} {info['name']} ({where}): {desc}")
        if self.log:
            print()
            for line in self.log:
                print("  " + line)
        self.log = []
        if self.tutor:
            hint = self.tutor(self)
            if hint:
                print()
                ui.box([hint], "Подсказка", C.CYN)
        else:
            print(paint("  (? — напомнить правила)", C.GRY))

    def bestiary(self):
        seen = self.st.setdefault("bestiary", [])
        new = [c["type"] for c in self.cr if c["type"] not in seen]
        new = list(dict.fromkeys(new))
        if not new:
            return
        ui.header(self.title, self.place)
        lines = []
        for t in new:
            info = CREATURES[t]
            lines.append(f"{info['glyph']} — {info['name']}. {info['rule']}")
            seen.append(t)
        ui.box(lines, "Новое существо", C.MAG)
        ui.dim(RULES)
        ui.pause()

    # ---------------------------------------------------------------- input
    def actions(self):
        acts = []
        nxt = self.p + 1
        if self.passable(nxt) or nxt >= self.L:
            acts.append(("step", "Шаг вперёд (тихо)"))
            if self.passable(nxt + 1) or nxt + 1 >= self.L:
                acts.append(("run", "Бежать на 2 клетки (шумно)"))
        else:
            if self.st.n("верёвка"):
                acts.append(("rope", "Закрепить переход верёвкой"))
            acts.append(("wade", "Перейти полынью по льду, с киркой (шумно)" if self.st.n("кирка")
                         else "Перелезть полынью по воде (−1 тепло, шумно)"))
        if self.st.n("камень"):
            acts.append(("stone", f"Бросить камень (осталось {self.st.n('камень')})"))
        warm_eater = any(c["type"] == "теплоед" and not c["warming"] for c in self.active())
        if self.st.n("фонарь") and not self.lamp_left and (self.dark or warm_eater):
            if self.dark:
                acts.append(("lamp", "Выключить фонарь" if self.lamp_on else "Включить фонарь (видно зверей)"))
            if warm_eater:
                acts.append(("drop", "Оставить фонарь здесь (приманка для теплоеда)"))
        near = [c for c in self.active() if abs(c["pos"] - self.p) <= 1 and not c["bush"] and self.harmful(c)]
        if self.st.n("нож") and near:
            acts.append(("knife", "Ударить ножом (теплоед уйдёт в близкие кусты, остальные отшатнутся)"))
        acts.append(("wait", "Затаиться"))
        return acts

    def ask_stone_target(self):
        bl = ", ".join(str(b) for b in sorted(self.bushes)) or "нет"
        print(paint(f"  Куда бросить? Номер клетки 0–{self.L - 1}. Добавь «к», чтобы в кусты (кусты у: {bl}).", C.GRY))
        while True:
            s = ui.raw_input("камень> ").lower().replace(" ", "")
            if s in ("", "отмена", "назад"):
                return None
            bush = s.endswith("к")
            s = s.rstrip("к")
            if s.isdigit() and 0 <= int(s) < self.L:
                cell = int(s)
                if bush and cell not in self.bushes:
                    print(paint("  Там нет кустов.", C.GRY))
                    continue
                return (cell, bush)
            print(paint("  Например: 5 или 3к. Пусто — отмена.", C.GRY))

    def player_turn(self):
        """Возвращает список шумов этого хода, или None если ход не потрачен."""
        aliases = {"шаг": "step", "бег": "run", "бежать": "run", "камень": "stone",
                   "нож": "knife", "ждать": "wait", "затаиться": "wait",
                   "фонарь": "lamp", "оставить фонарь": "drop", "верёвка": "rope",
                   "вода": "wade"}
        available = {a[0] for a in self.actions()}
        hidden = {word: key for word, key in aliases.items() if key in available}
        hidden.update({"?": "help", "правила": "help"})
        key = ui.ask(self.actions(), hidden=hidden)
        noise = []
        if key == "help":
            ui.box([RULES], "Правила", C.GRY)
            ui.pause()
            return None
        if key in ("step", "run"):
            n = 1 if key == "step" else 2
            for _ in range(n):
                nxt = self.p + 1
                if nxt < self.L and not self.passable(nxt):
                    break
                b = self.blocker_at(nxt) if nxt < self.L - 1 else None
                if b:
                    self.contact(b)
                    break
                self.p = nxt
                if self.p in self.items:
                    self.items.discard(self.p)
                    self.st.add("камень")
                    self.log.append(paint("Подбираешь камень. (+1)", C.YEL))
                if self.p in self.brush and key == "step":
                    noise.append((self.p, False, "хруст"))
                    self.log.append(paint("Хворост под ногой хрустит на весь лес.", C.YEL))
                for c in self.active():
                    if c["type"] == "пересмешник" and c["pos"] == self.p and not c["bush"]:
                        self.log.append(paint("Пересмешник вспархивает из-под ног с криком!", C.MAG))
                        noise.append((self.p, False, "крик"))
                if self.p >= self.L - 1:
                    break
            if key == "run":
                noise.append((self.p, False, "бег"))
        elif key == "rope":
            self.st.take("верёвка")
            self.roped.add(self.p + 1)
            self.used["верёвка"] += 1
            self.log.append(paint("Ты закрепляешь верёвку. Переход надёжный.", C.YEL))
        elif key == "wade":
            self.p = min(self.L - 1, self.p + 2)
            noise.append((self.p, False, "плеск"))
            if self.st.n("кирка"):
                self.log.append(paint("Ты бьёшь киркой лёд у края и переходишь по нему. Громко, зато сухо.", C.YEL))
            else:
                self.st.hurt(1)
                self.log.append(paint("Ледяная вода по колено. −1 тепло.", C.BLU))
        elif key == "stone":
            t = self.ask_stone_target()
            if t is None:
                return None
            self.st.take("камень")
            self.used["камень"] += 1
            noise.append((t[0], t[1], "камень"))
            self.log.append(paint(f"Камень стучит {'в кустах у ' + str(t[0]) if t[1] else 'в клетке ' + str(t[0])}.", C.YEL))
        elif key == "lamp":
            self.lamp_on = not self.lamp_on
            self.used["фонарь"] += 1
        elif key == "drop":
            self.lamp_on = False
            self.lamp_left = True
            self.lights.append(self.p)
            self.used["фонарь"] += 1
            self.log.append(paint("Фонарь светит на снегу.", C.YEL))
        elif key == "knife":
            near = [c for c in self.active() if abs(c["pos"] - self.p) <= 1 and not c["bush"] and self.harmful(c)]
            self.used["нож"] += 1
            if near:
                c = near[0]
                d = 1 if c["pos"] >= self.p else -1
                name = CREATURES[c["type"]]["name"]
                if c["type"] == "теплоед":
                    near_b = [b for b in self.bushes if abs(b - c["pos"]) <= 2]
                    if near_b:
                        b = min(near_b, key=lambda x: (abs(x - c["pos"]), -x))
                        c["pos"], c["bush"], c["linger"] = b, True, 2
                        c.pop("target", None)
                        self.log.append(paint(f"Теплоед шипит от удара и уползает в кусты у {b}. "
                                              "Пару ходов он будет там дремать.", C.YEL))
                        return noise
                newpos = c["pos"] + 1 * d
                if c["type"] != "сторож" and (newpos >= self.L - 1 or newpos < 0):
                    c["gone"] = True
                    self.log.append(paint(f"Ты отмахиваешься ножом — {name} скулит и удирает с тропы в лес.", C.YEL))
                    return noise
                c["pos"] = max(0, min(self.L - 2, newpos))
                if c["pos"] == self.p:
                    c["pos"] = min(self.L - 2, self.p + 1)
                c["stun"] = 2 if c["type"] == "теплоед" else 1
                if c["type"] == "сторож":
                    c["hp"] -= 1
                    if c["hp"] <= 0:
                        c["gone"] = True
                        self.log.append(paint("Сторож оседает в снег.", C.GRN, C.B))
                    else:
                        wound = "держится за бок" if c["hp"] == 2 else "едва стоит на ногах"
                        self.log.append(paint(f"Сторож отшатывается и {wound}.", C.YEL))
                else:
                    self.log.append(paint(f"Ты отмахиваешься ножом — {name} отлетает назад.", C.YEL))
            else:
                noise.append((self.p, False, "взмах"))
                self.log.append(paint("Нож рассекает воздух. Мимо, и громко.", C.GRY))
        return noise

    # ---------------------------------------------------------------- loop
    def thermos_save(self):
        if self.st["warmth"] <= 0 and self.st.n("термос") and self.st.get("thermos_charges", 0) > 0:
            self.st["thermos_charges"] -= 1
            self.st["warmth"] = self.st["max_warmth"] // 2 + 1
            self.log.append(paint("Руки уже не слушаются, но ты откручиваешь термос Ефима. Горячо! "
                                  f"(тепло {self.st['warmth']}, глотков осталось {self.st['thermos_charges']})",
                                  C.YEL, C.B))
            return True
        return False

    def run(self):
        self.bestiary()
        while True:
            self.thermos_save()
            self.render()
            if self.st["warmth"] <= 0:
                return self.result(False)
            noise = self.player_turn()
            if noise is None:
                continue
            self.turn += 1
            if self.p >= self.L - 1:
                self.render()
                ui.good("Ты выбрался.")
                ui.pause()
                return self.result(True)
            if self.st["warmth"] <= 0 and not self.thermos_save():
                self.render()
                return self.result(False)
            if any(c["type"] == "сторож" for c in self.cr) and not any(
                    c["type"] == "сторож" and not c["gone"] for c in self.cr):
                self.render()
                ui.pause()
                return self.result(True)
            self.creatures_turn(noise)
            if self.path_clear():
                self.render()
                ui.good("Впереди никого. Дальше тропа свободна, и ты спокойно доходишь до выхода.")
                ui.pause()
                return self.result(True)

    def path_clear(self):
        if any(g > self.p and g not in self.roped for g in self.gaps):
            return False
        for c in self.active():
            if not self.harmful(c):
                continue
            if c["pos"] >= self.p - 1:
                return False
        return True

    def result(self, win):
        if not win:
            ui.danger("Холод лезет под куртку. Садишься в снег, просто на минутку... и всё темнеет.")
            ui.pause()
        if self.lamp_left:
            self.lamp_on = False
            if win:
                n_sleep = sum(1 for c in self.cr if c["warming"])
                who = "Оба теплоеда спят" if n_sleep >= 2 else "Теплоед спит"
                ending = "не просыпаются" if n_sleep >= 2 else "не просыпается"
                ui.dim("Пара шагов назад в пределах одной поляны лес ещё позволяет. Возвращаешься за фонарём. "
                       f"{who}, обвившись вокруг тёплого места, и {ending}.")
        if self.roped and not self.keep_rope:
            self.st.add("верёвка", len(self.roped))
            if win:
                ui.dim("Ты отвязываешь верёвку и сматываешь её.")
        return dict(win=win, roped=bool(self.roped), used=self.used)


def play(st, *args, can_skip=True, **kw):
    """Играет сцену до победы. Поражение — просыпаешься у начала сцены с частью тепла.
    После второго поражения можно обойти участок (без награды)."""
    losses = 0
    inv0 = dict(st["inv"])
    charges0 = st.get("thermos_charges", 0)
    while True:
        enc = Encounter(st, *args, **kw)
        ui.IN_ENCOUNTER = True
        try:
            res = enc.run()
        finally:
            ui.IN_ENCOUNTER = False
        if res["win"]:
            res["skipped"] = False
            return res
        losses += 1
        st["inv"] = dict(inv0)            # всё, что потратил в этой попытке, возвращается
        st["thermos_charges"] = charges0
        st["warmth"] = max(st["warmth"], st["max_warmth"] // 2 + 1)
        ui.header(args[0] if args else "", "")
        ui.thought("...Открываешь глаза. Тот же снег, та же тропа. Тепло вернулось. Чуть-чуть.")
        ui.say("Вещи при тебе, как в начале этого места: верёвка, камни, всё что было.", C.GRY)
        if st.n("камень") < 2:
            st.add("камень", 2)
            ui.say("Под рукой в снегу пара камней. (+2 камня)", C.GRY)
        if losses >= 2 and can_skip:
            k = ui.ask([("retry", "Попробовать ещё раз"),
                        ("skip", "Отступить и обойти это место лесом (без награды)")])
            if k == "skip":
                ui.say("Ты делаешь крюк по сугробам. Долго, холодно, но живой.", C.GRY)
                ui.pause()
                return dict(win=True, roped=False, used=res["used"], skipped=True)
        else:
            ui.pause()


def random_encounter(st, rng, region, hard=False, title="Тропа", place="", weather="ясно", fewer=False):
    pools = {
        "birch": ["шорох", "шорох", "теплоед"],
        "mine": ["шорох", "теплоед"],
        "bog": ["теплоед", "шорох", "пересмешник"],
        "spruce": ["шорох", "теплоед", "пересмешник"],
        "ash": ["теплоед", "шорох"],
        "ridge": ["шорох", "теплоед"],
    }
    L = rng.randint(7, 9)
    bushes = sorted(rng.sample(range(1, L - 1), rng.randint(2, 3)))
    free = [i for i in range(2, L - 2) if i not in bushes]
    gap_p = 0.5 if region in ("bog", "ridge") else 0.3
    if weather == "оттепель":
        gap_p = 0.9
    gaps = [rng.choice(free)] if free and rng.random() < gap_p else []
    rest = [i for i in range(1, L - 1) if i not in gaps]
    brush = rng.sample(rest, rng.randint(0, 2)) if rest else []
    rest = [i for i in rest if i not in brush]
    items = rng.sample(rest, rng.randint(0, 1)) if rest else []
    k = 2 if hard else 1
    kinds = [rng.choice(pools.get(region, ["шорох"])) for _ in range(k)]
    if "пересмешник" in kinds and "шорох" not in kinds:
        kinds.append("шорох")
    if all(x == "пересмешник" for x in kinds):
        kinds.append("шорох")
    if fewer and len(kinds) > 1:
        kinds = kinds[1:]
    creatures = []
    used = set(gaps)
    for t in kinds:
        if t == "пересмешник" and bushes:
            creatures.append((t, rng.choice(bushes), True))
            continue
        lo = max(2, L // 2 - 1) - (1 if weather == "туман" else 0)
        cand = [i for i in range(max(2, lo), L - 1) if i not in used]
        pos = rng.choice(cand) if cand else L - 2
        used.add(pos)
        creatures.append((t, pos))
    return play(st, title, L, creatures, bushes=bushes, gaps=gaps, brush=brush, items=items,
                dark=(region == "spruce" or weather == "метель"), hard=hard,
                place=(place + ", " + weather) if weather != "ясно" else place)
