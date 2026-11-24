"""Акт 3. Тайная тропа: искажённые комнаты, подсказки в файлах, постановочные краши,
save.txt, исчезающий дуб и финалы (два обычных и один секретный)."""
import random
import sys
import time

from . import art, state, ui
from .state import FAKE_SAVE, HINTS
from .ui import C, paint

WORDS = [("КО", "ЛЬ", "ЦО"), ("ПЕ", "ПЕ", "Л"), ("СМ", "О", "ЛА"), ("КО", "РЕ", "НЬ"), ("ЗА", "РУБ", "КА")]


def staged_crash(st, next_stage, lines):
    """Игра «падает»: состояние сохранено, при запуске продолжится нужная сцена."""
    st["stage"] = next_stage
    st.set("crashed")
    st.save()
    print()
    for l in lines:
        print(paint(l, C.RED))
        time.sleep(0.05 if ui.TTY and not ui.FAST else 0)
    print()
    print(paint("  [процесс завершён. запусти игру снова]", C.GRY))
    sys.exit(1)


def helped_list(st):
    """Кому ты помог за игру. Нужно для секретного финала."""
    out = []
    if st.has("helped"):
        out.append(("себе", "ты сам, тот, что внизу в ущелье"))
    if st.has("q_efim"):
        out.append(("Ефим", "Ефим, со своим котелком"))
    if st.has("boss_peace"):
        out.append(("Гриша", "Гриша, без плаща, в одном свитере"))
    if st.has("pencil_returned"):
        out.append(("Варвара", "Варвара, с карандашом за ухом"))
    if st.has("cub_freed"):
        out.append(("щенок", "хромой шорох, уже совсем большой"))
    if st.has("canary_home") or st.has("canary_alive"):
        out.append(("канарейка", "жёлтая птичка, орёт на весь лес"))
    if st.get("names"):
        out.append(("имена", "люди с табличек: " + ", ".join(st["names"])))
    return out


# --------------------------------------------------------------------- вход

def a3_enter(st):
    ui.transition("mine", "glitch", "Шагаешь в трещину...")
    ui.header("???", "тропа, которой нет на карте", C.MAG)
    ui.narr("За стеной не штольня. За стеной лес. Только неправильный какой-то: снег падает вверх, "
            "а у берёз по два ствола. Один настоящий, а второй как будто нарисован поверх, карандашом.")
    ui.glitch_say("Где-то рядом голос Варвары: «...никто не выходит той дорогой, какой пришёл...» "
                  "Голос отовсюду сразу.", 0.04)
    ui.pause()
    return "a3_old_stump"


def a3_old_stump(st):
    ui.header(ui.glitch("Старый пень", 0.2, 3), "у вх░да в лес", C.MAG)
    art.show(art.STUMP, C.MAG)
    ui.narr("Пень. Тот самый, с самого начала.")
    ui.say("Зарубок на нём сорок. Пятьдесят. Идут по кругу, как годовые кольца, и все косые, твоей рукой.", C.MAG)
    ui.say(ui.glitch("Опята на берёзе: семь шляпок. Одна кривая как ухо. Семь шляпок. Одна кривая. Семь.", 0.08, 5),
           C.MAG)
    if st.get("sits", 0) >= 3:
        ui.say("На пне вмятина. Твоя. Ты тут явно сидел дольше, чем помнишь.", C.MAG)
    ui.ask([("go", "Идти дальше, не оглядываться")], hidden={"сесть": "go", "оглянуться": "go"})
    return "a3_empty"


def a3_empty(st):
    ui.header("", "", C.MAG)
    for i in range(6):
        print(paint("  " + "░" * random.randint(10, 60), C.GRY))
    print()
    ui.say("Тут ничего нет. Ни деревьев, ни снега, ни тебя.", C.GRY)
    ui.say("[ОШИБКА] scene_id=None  ring_depth=-1  player.position=(?, ?)", C.RED)
    ui.pause()
    w = random.Random(st["seed"]).choice(WORDS)
    st["password"] = "".join(w)
    names = ["обрывок_А.txt", "обрывок_Б.txt", "обрывок_В.txt"]
    layers = ["КОРНИ", "КОРА", "КРОНА"]
    order = random.Random(st["seed"] + 1).sample(range(3), 3)
    state.write_hint("0_ПОРЯДОК.txt",
                     "слова в лесу пишутся от земли к небу.\n\n"
                     "   КОРНИ  ->  КОРА  ->  КРОНА\n\n"
                     "собери буквы из обрывков в таком порядке. дверь откроется на голос.\n"
                     "(обрывки чуть побились при падении, но буквы видно)\n")
    for fi, li in enumerate(order):
        state.write_hint(names[fi],
                         f"▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒\nслой: {layers[li]}\n▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒\n\n"
                         f"        {w[li]}\n\n▒▒░░▒▒░░ данные повреждены ░░▒▒░░▒▒\n")
    st["hints_written"] = time.time()
    staged_crash(st, "a3_door", [
        "Traceback (most recent call last):",
        '  File "les/forest.py", line 404, in render_room',
        "    room = self.rings[depth]",
        "IndexError: ring index out of range: -1",
        "",
        "  [лес] при падении часть данных выпала в папку «подсказки»",
        f"  [лес] {HINTS}",
    ])


def a3_door(st):
    if st.has("crashed"):
        st.unset("crashed")
        ui.clear()
        ui.thought("...моргаешь. Перед глазами серые точки, как после вспышки. Стоишь. Где-то.")
        ui.pause()
    ui.header("Дверь из коры", "", C.MAG)
    ui.narr("Посреди пустоты дверь. Без стены, без петель, просто дверь, вырезанная из живой коры. "
            "Ручки нет. Только надпись: «СКАЖИ».")
    pw = st.get("password", "КОЛЬЦО")
    tries = 0
    eggs = {"СЕЗАМ": "Не та сказка.", "ОТКРОЙСЯ": "Вежливее надо. И вообще не то.",
            "ПОЖАЛУЙСТА": "Вежливо. Но нет.", "ДРУГ": "Это вообще из другой книжки.",
            "ДУБ": "Дверь хмыкает. Двери не умеют хмыкать. Эта умеет."}
    while True:
        k = ui.ask([("say", "Сказать слово"), ("hint", "Не могу найти обрывки")])
        if k == "hint":
            st.set("used_ingame_hint")
            ui.say(f"Обрывки выпали в папку: {HINTS}", C.GRY)
            ui.voice("Лес", "Мог бы и сам папку открыть. Ладно уж. На.", C.MAG)
            for p in sorted(HINTS.glob("*.txt")) if HINTS.exists() else []:
                if p.name.startswith("для_"):
                    continue
                print(paint(f"  ── {p.name}", C.GRY))
                for line in p.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        print(paint("     " + line, C.WHT))
            continue
        s = ui.raw_input("сказать> ").upper().replace(" ", "").replace("Ё", "Е")
        if s == pw.replace("Ё", "Е"):
            break
        if s in eggs:
            ui.say(eggs[s], C.MAG)
            continue
        tries += 1
        ui.say("Дверь молчит." if tries < 3 else "Дверь молчит. Обрывки лежат в папке «подсказки». "
               "Порядок: КОРНИ, КОРА, КРОНА.", C.GRY)
    if state.hints_peeked(st.get("hints_written", 0)) and not st.has("used_ingame_hint"):
        ui.voice("Лес", "В папку лазил? Я видел. Я вообще вижу всё, что во мне лежит.", C.MAG)
    ui.say("Дверь открывается внутрь. В серый снег.", C.GRY)
    ui.pause()
    return "a3_ash_self"


def a3_ash_self(st):
    ui.transition("glitch", "ash", "...")
    ui.header("Пепелище", "наоборот", C.MAG)
    ui.narr("Стоишь на вершине завала. Камни, корни, стволы крест-накрест. Ты на нём разве стоял? "
            "Нет. Ты стоял внизу.")
    ui.say("А внизу, у подножия, стоит человек и смотрит на тебя снизу вверх. Куртка как у тебя. "
           "Глаза ещё не красные. Он ещё не знает ничего.", C.CYN)
    ui.thought("Это я. Тот я, который в завал упёрся. Он не знает про Штольню.")
    ui.say("Что скажешь ему?", C.GRY)
    opts = [("right", "«Назад. Штольня. Пять раз.»"), ("run", "«Беги отсюда!»"),
            ("oak", "«Не трогай дуб!»"), ("own", "Сказать своё")]
    k = ui.ask(opts)
    if k != "right":
        if k == "own":
            ui.raw_input("сказать> ")
        ui.say("Слова застревают в горле. Пытаешься, и не можешь. Ты уже знаешь, что ты сказал. "
               "Ты это слышал. Оттуда, снизу.", C.MAG)
        ui.pause()
    ui.type_out("     «Назад. Штольня. Пять раз.»", C.CYN + C.B, delay=0.06)
    st["memory"]["пепелище"] = "голос"
    ui.say("Человек внизу бледнеет. Видно, как он оборачивается, и мир вокруг тебя "
           "перестаёт быть. Ты не уходишь. Тебя просто тут больше нет.", C.GRY)
    ui.thought("Так вот почему он пропал. Вот почему я пропал.")
    ui.pause()
    return "a3_birch_glitch"


def a3_birch_glitch(st):
    ui.transition("ash", "glitch", "...")
    ui.header("Березняк", ui.glitch("та же дорога. снова. снова.", 0.15, 9), C.MAG)
    ui.narr("Берёзы стоят рядами, как таблички на Пепелище. У каждой медная табличка.")
    plates = ["...раньше это была Вера", "...раньше это был Сторож", "...раньше это была Варвара",
              "...раньше это был Ефим", "...раньше это был кот Пепел"]
    for p in plates:
        ui.say("  " + p, C.WHT)
    for n in st.get("names", []):
        ui.say(f"  ...раньше человек: {n}   (буквы стёрлись, будто кого-то уже вспомнили)", C.GRY)
    ui.say("  ...её звали Саша   (буквы недописаны, последняя ещё блестит)", C.RED)
    ui.say(f"  ...раньше человек: {st['name']}", C.RED + C.B)
    ui.say("Медь новая, чистая. Буквы ещё блестят. Тебя ждали.", C.MAG)
    ui.thought("Саша. Её табличка ещё не дописана. Значит, ещё не поздно. Если я дойду. Если не сдамся.")
    ui.pause()
    ui.header("", "", C.MAG)
    ui.say("[ОШИБКА] room 'birch:2:1' not found", C.RED)
    ui.say("[ОШИБКА] room 'birch:2:1' not found", C.RED)
    ui.say("[ОШИБКА] room 'birch:2:1' найдено в сохранении. Восстанавливаю...", C.YEL)
    ui.pause()
    return "a3_gate"


# --------------------------------------------------------------------- петля и save.txt

def a3_gate(st):
    st.set("gate_reached")
    if st.has("recurse_off_early"):
        return "a3_free"
    ui.transition("glitch", "snow", "Тропа выводит из леса...")
    ui.header("Опушка", "ноябрь, первый снег")
    ui.narr("Мы пришли в лес на прогулку. В глубине чащи растёт наш любимый дуб. "
            "Последний раз мы были у него летом...")
    ui.sleep(1.0)
    ui.say("Широкий пень у тропы. Тропа. Следы. В рюкзаке фонарь, верёвка, нож.", C.GRY)
    ui.sleep(1.0)
    print()
    ui.thought("Так стоп...")
    ui.sleep(0.8)
    ui.thought("Я тут уже был.")
    ui.sleep(0.8)
    ui.thought("Это не прогулка. Это круг, и он где-то записан. Где-то записано, что я должен "
               "по кругу ходить. Надо что-то сделать, чтобы выбраться...")
    ui.thought("Надо поменять файл сохранения.")
    state.write_fake_save(True)
    state.write_hint("для_казуалов.txt",
                     "если совсем непонятно что делать:\n\n"
                     f"1. открой папку игры:\n   {state.BASE}\n"
                     "2. открой файл save.txt любым редактором (блокнот подойдёт)\n"
                     "3. найди строчку  recurse=true\n"
                     "4. поменяй true на false, чтоб было  recurse=false\n"
                     "5. сохрани файл и запусти игру снова\n\n"
                     "лес будет недоволен. это нормально.\n"
                     "p.s. остальное в файле не трогай, там ничего интересного. ну почти.\n")
    st["hints_written"] = time.time()
    ui.pause()
    staged_crash(st, "a3_gate_check", [
        "  [лес] recurse=true",
        "  [лес] петля замкнута. сохранение записано в save.txt",
        f"  [лес] {FAKE_SAVE}",
    ])


def a3_gate_check(st):
    st.unset("crashed")
    r = state.read_recurse()
    if r is False:
        if state.hints_peeked(st.get("hints_written", 0)):
            ui.voice("Лес", "Инструкцию для казуалов читал? Ничего. Все читают.", C.MAG)
            ui.pause()
        return "a3_free"
    st["gate_loops"] = st.get("gate_loops", 0) + 1
    ui.clear()
    if r is None:
        ui.say("save.txt поломан или пропал. Лес записывает его заново. Лес не любит, когда его ломают.", C.RED)
        state.write_fake_save(True)
    ui.header("Опушка", "ноябрь, первый снег. " + "снова. " * min(5, st["gate_loops"]))
    montage = ["Пень.", "Папоротники.", "Ручей.", "Ефим: «Опять ты?»", "Ущелье.", "Дерево.",
               "Березняк.", "Штольня. Пять раз.", "Пепелище.", "Дверь.", "Пень."]
    for m in montage:
        ui.type_out("  " + m, C.GRY, delay=0.01)
        ui.sleep(0.25)
    ui.thought("Круг. Опять круг. Пока в save.txt написано recurse=true, лес будет меня крутить.")
    if st["gate_loops"] >= 2:
        ui.say("(Подробно: папка «подсказки», файл для_казуалов.txt)", C.GRY)
    ui.pause()
    staged_crash(st, "a3_gate_check", ["  [лес] recurse=true", "  [лес] петля замкнута."])


# --------------------------------------------------------------------- последняя уловка

def a3_free(st):
    ui.clear()
    ui.say("recurse=false", C.GRN + C.B)
    ui.sleep(0.8)
    ui.header("Опушка", "")
    ui.narr("Пень. Тропа. Но в этот раз ты не идёшь по тропе. Сходишь с неё, в снег по колено, "
            "туда где никогда дороги не было.")
    ui.say("Лес молчит. Первый раз как-то растерянно.", C.GRY)
    ui.pause()
    ui.transition("snow", "oak", "Идёшь напрямик, без тропы...")
    ui.header("Долина", "")
    art.show(art.OAK, C.GRN)
    ui.narr("Дуб. Совсем рядом, шагов двадцать.")
    ui.ask([("go", "Подойти")])
    ui.header("Долина", "")
    art.show(art.OAK_FADED, C.GRY)
    ui.say("Дуб тает. Как в прошлый раз. Ветка за веткой.", C.MAG)
    ui.sleep(1.2)
    ui.thought("Нет. Только не снова. Пожалуйста.")
    ui.pause()
    return "a3_empty_map"


def empty_map(highlight):
    ui.header("Карта", "")
    print()
    for _ in range(3):
        print(paint("        ·                                 ·", C.GRY))
        print()
    print("                         " + paint("[@]", C.B, C.WHT))
    print()
    print(paint("        Ни точек. Ни троп. Ни выхода.", C.GRY))
    print()
    fwd = paint(" ↑ Вперёд ", C.INV, C.YEL, C.B) if highlight else paint("↑ Вперёд", C.GRY)
    return [("look", "Оглядеться"), ("back", "← Назад"), ("fwd", fwd)]


def empty_opts(opts, no_back):
    return [o for o in opts if not (no_back and o[0] == "back")]


def a3_empty_map(st):
    looked = 0
    while True:
        first = not st.has("map_wait")
        opts = empty_map(not first or looked > 0)
        if first:
            st.set("map_wait")
            ui.sleep(3.0)
        k = ui.ask(empty_opts(opts, st.has("tried_back")))
        if k == "look":
            looked += 1
            ui.say(["Пусто. Снег до горизонта. Ни следа.",
                    "Тишина. Только где-то совсем рядом как будто листья шелестят. Зимой.",
                    "Шелест. Прямо перед тобой."][min(looked - 1, 2)], C.GRY)
            ui.sleep(1.5)
        elif k == "back":
            ui.say("Назад больше нет. Ты сам так сделал.", C.GRY)
            st.set("tried_back")
            ui.sleep(1.2)
        else:
            break
    ui.header("", "")
    ui.say("Делаешь шаг туда, где ничего нет.", C.GRY)
    ui.sleep(0.8)
    ui.say("Под ногой корень.", C.WHT)
    ui.sleep(0.6)
    ui.say("Шелест над головой. Ветки, которых не видно. Протягиваешь руку и упираешься в кору.", C.WHT)
    ui.sleep(0.6)
    ui.say("Он никуда не исчезал. Он прятался. Последний фокус, и ты сквозь него прошёл.", C.YEL)
    ui.pause()
    return "a3_oak"


def a3_oak(st):
    ui.header("Дуб", "ядро")
    art.show(art.OAK, C.GRN)
    ui.narr("Дуб проступает из воздуха, как картинка на мокрой фотографии. От коры идёт тепло, как от печки, "
            "а ветки чуть-чуть шевелятся без ветра, не в такт друг другу. Кольца на срезе сучка "
            "закручиваются внутрь. Бесконечно.")
    ui.ask([("touch", "Дотронуться")])
    ui.say("Ты дотрагиваешься, и теперь ТЫ становишься новым дубом...", C.MAG)
    ui.sleep(1.0)
    ui.say("Корни прорастают сквозь ботинки. Пальцы становятся ветками. Ты чувствуешь весь лес сразу: "
           "Ефима у костра, Варвару с картой, гряду, бесконечную тропу от пня до дерева и обратно. "
           "Ты стал с дубом одним целым...", C.MAG)
    ui.sleep(1.0)
    print()
    ui.type_out("  Сопротивляться?  Да / Нет", C.B + C.WHT, delay=0.05)
    tried_call = False
    while True:
        s = ui.raw_input("> ").lower().strip(" .!")
        if s in ("да", "1", "д", "yes", "y"):
            return "a3_rings"
        if s in ("нет", "2", "н", "no", "n"):
            return "end_sad"
        if s in ("позвать", "позвать на помощь", "помогите", "помощь", "на помощь", "крикнуть", "звать"):
            if len(helped_list(st)) >= 4:
                return "end_together"
            if not tried_call:
                tried_call = True
                ui.say("Ты зовёшь. Голоса нет, вместо голоса шелест. Никто не слышит. "
                       "Может, просто некому.", C.GRY)
                continue
        print(paint("  Да или Нет.", C.GRY))


# --------------------------------------------------------------------- финальная мини-игра

def build_rings(st):
    m = st["memory"]
    rings = []
    if m.get("пень") == "нож":
        rings.append(("Пень", "Пень у входа. Ты оставил там что-то на память.", {"нож"}))
    else:
        rings.append(("Пень", "Пень у входа. Ты так и не оставил там ничего на память. Ещё не поздно.", {"нож"}))
    if m.get("ручей") == "верёвка":
        tools = {"верёвка"}
        if m.get("ручей_камень"):
            tools.add("камень")
        rings.append(("Ручей", "Ручей. Ты выбрался на тот берег, оставив Шороха позади.", tools))
    else:
        rings.append(("Ручей", "Ручей. Шорох роется в стороне и никак не успокоится.", {"камень"}))
    rings.append(("Ущелье", "Ущелье. Снизу корни казались сплошной стеной.", {"фонарь", "голос"}))
    rings.append(("Штольня", "Штольня. Стена отвечает тем же ритмом.", {"камень"}))
    rings.append(("Пепелище", "Пепелище. Тот, внизу, ещё ничего не знает.", {"голос"}))
    return rings


TOOLS = [("камень", "Камень"), ("верёвка", "Верёвка"), ("фонарь", "Фонарь"), ("нож", "Нож"), ("голос", "Голос")]


def a3_rings(st, rng=None):
    rng = rng if rng is not None else random.Random()
    rings = build_rings(st)
    tight = {r[0]: rng.choice([0, 1]) for r in rings}
    freed, lost = set(), set()
    ui.header("Кольца", "сопротивление")
    ui.narr("Ты внутри дуба. Вокруг годовые кольца, и каждое кольцо это место, где ты был. "
            "Корни затягивают их одно за другим, превращают в дерево. Затянется кольцо, "
            "и это место станет лесом навсегда. И ты вместе с ним.")
    ui.box(["Каждый ход корни затягивают одно кольцо. Какое - видно заранее.",
            "Освободить кольцо можно тем, что ты там когда-то сделал.",
            "Три затяжки - кольцо потеряно. Потеряешь два - лес победил."], "Как сопротивляться", C.GRY)
    ui.pause()
    target = max((r for r in rings), key=lambda r: tight[r[0]])[0]
    while True:
        active = [r for r in rings if r[0] not in freed and r[0] not in lost]
        if not active or len(lost) >= 2:
            break
        if target not in [r[0] for r in active]:
            target = rng.choice(active)[0]
        ui.header("Кольца", f"освобождено {len(freed)}/5   потеряно {len(lost)}/2")
        for r in rings:
            name = r[0]
            if name in freed:
                print("   " + paint(f"◯ {name:<10} свободно", C.GRN))
            elif name in lost:
                print("   " + paint(f"● {name:<10} стало деревом", C.GRY))
            else:
                bar = paint("▰" * tight[name], C.RED) + paint("▱" * (3 - tight[name]), C.GRY)
                arrow = paint("  ← корни тянутся сюда", C.RED, C.B) if name == target else ""
                print(f"   ◎ {name:<10} {bar}{arrow}")
                print(paint(f"       {r[1]}", C.GRY))
        k = ui.ask([(r[0], r[0]) for r in active], title="Какое кольцо освободить?")
        ring = next(r for r in active if r[0] == k)
        tool = ui.ask(TOOLS, title=f"{ring[0]}: что тебе там помогло?")
        if tool in ring[2]:
            freed.add(ring[0])
            ui.good(f"Кольцо «{ring[0]}» разжимается. Ты снова узнаёшь это место: ты здесь был, и оно твоё.")
        else:
            ui.danger("Не то. Корни смеются. Шелестом.")
        if target not in freed and target not in lost:
            tight[target] += 1
            if tight[target] >= 3:
                names = st.get("names", [])
                if len(names) >= 2 and not st.has("names_used"):
                    st.set("names_used")
                    tight[target] = 1
                    ui.say("Кольцо «" + target + "» уже почти дерево, и тут ты вспоминаешь край карты. "
                           "Читаешь вслух: " + ", ".join(names) + ".", C.YEL)
                    ui.say("Корни замирают. Они не знают, что делать с теми, кого помнят по имени. "
                           "Кольцо чуть отпускает.", C.YEL)
                else:
                    lost.add(target)
                    ui.danger(f"Кольцо «{target}» затянулось. Это место теперь дерево.")
        active = [r for r in rings if r[0] not in freed and r[0] not in lost]
        if active:
            target = max(active, key=lambda r: (tight[r[0]], rng.random()))[0]
        ui.pause()
    if len(lost) >= 2:
        ui.header("Кольца", "")
        ui.danger("Корни смыкаются. Уже непонятно, где кончаешься ты и начинается кора.")
        k = ui.ask([("retry", "Нет. Ещё раз. Сопротивляться!"), ("give", "Сдаться")])
        return "a3_rings" if k == "retry" else "end_sad"
    return "end_good"


# --------------------------------------------------------------------- финалы

def epilogue_people(st):
    if st.has("boss_peace"):
        ui.say("Ефим гасит костёр и тянет санки к опушке. Рядом идёт Гриша, несёт термос, "
               "и они спорят, кто его тогда с крыльца уронил. Кот Пепел едет на санках, как король.", C.WHT)
    elif st.has("boss_fought"):
        ui.say("Ефим гасит костёр и тянет санки к опушке. Всё оглядывается на гряду. "
               "Гриша не приходит. Там, на гребне, под снегом, он так и не встал.", C.WHT)
    else:
        ui.say("Ефим гасит костёр и тянет санки к опушке. Всё оглядывается на гряду, ждёт кого-то. "
               "Кот Пепел едет на санках.", C.WHT)
    if st.n("письмо"):
        st.take("письмо")
        st.set("letter_delivered")
        ui.say("Ты протягиваешь Ефиму письмо, найденное у дерева Веры. Он читает его до конца и складывает "
               "по старым сгибам. «Донёс, значит. Спасибо». Убирает за пазуху.", C.WHT)
    if st.has("boss_fought") and st.has("letter_delivered"):
        ui.say("Ефим несёт письмо Веры с собой. Несколько раз останавливается, но на гряду не возвращается.", C.WHT)
    elif st.has("boss_peace") and st.has("letter_delivered"):
        ui.say("У самой опушки Ефим отдаёт письмо Грише. Тот разворачивает его и надолго отстаёт от остальных.", C.WHT)
    elif st.has("grisha_letter"):
        ui.say("Письмо Веры Гриша несёт в нагрудном кармане. Иногда трогает его, проверяет, на месте ли.", C.WHT)
    if st.has("pencil_returned"):
        ui.say("Варвара сворачивает карту, больше не нужна. Карандаш суёт за ухо, на память.", C.WHT)
    else:
        ui.say("Варвара бредёт к опушке и рисует пальцем по воздуху. Карандаша у неё так и нет.", C.WHT)
    names = st.get("names", [])
    if len(names) == 1:
        ui.say(f"Из-за деревьев выходит {names[0]}. Ты видел только табличку, но узнаёшь сразу.", C.WHT)
    elif names:
        ui.say("Из-за деревьев выходят те, кого ты знаешь только по табличкам: "
               + ", ".join(names[:-1]) + " и " + names[-1] + ". Ты узнаёшь каждого. Не знаешь как, но узнаёшь.", C.WHT)
    if st.has("canary_home"):
        ui.say("Над головой пролетает жёлтая птичка. Где-то сзади ворчит Пётр Савельич, крепильщик.", C.WHT)
    elif st.has("canary_alive"):
        ui.say("Канарейка за пазухой поёт всю дорогу. Громко, на весь лес.", C.WHT)
    if st.has("cub_freed"):
        ui.say("На опушке сидит хромой шорох, уже большой. Провожает. Дальше не идёт.", C.WHT)
    if st.has("hugged_tree"):
        ui.say("Далеко-далеко серое дерево с той поляны машет веткой. Ну или ветер. Но ты-то знаешь.", C.WHT)


def end_good(st):
    state.mark_ending("Оттепель")
    ui.header("Оттепель", "финал")
    ui.narr("Последнее кольцо разжимается, и дуб выдыхает. Весь, от корней до кроны.")
    ui.say("Где-то трескается лёд на ручье. С гряды съезжает снег. По всему лесу падают медные таблички, "
           "одна за другой, тихо, в мягкий снег. Из-за деревьев выходят люди: заспанные, растерянные, "
           "в летней одежде.", C.WHT)
    epilogue_people(st)
    print()
    art.show(art.OAK, C.GRN)
    ui.narr("Ты стоишь у дуба. Просто у дуба, у того самого, с развилкой и дуплом. "
            "Под ним сидит Саша, нос красный, шапка набекрень.")
    ui.voice("Саша", "Ты где ходишь? Я тут сто лет жду. Я тебе записку написала, на всякий случай.", C.RED)
    ui.say("В дупле записка. Почерк Сашин, буквы скачут.", C.GRY)
    ui.type_out("     «Приходи ещё. Только не один.»", C.YEL + C.B, delay=0.05)
    ui.say("Идёшь домой. Тропа ведёт прямо, как ей и положено. Ни одного круга.", C.GRY)
    return finish(st, "Оттепель")


def end_together(st):
    state.mark_ending("Вместе")
    ui.header("Вместе", "секретный финал")
    ui.narr("Ты не сопротивляешься. И не сдаёшься. Ты зовёшь.")
    ui.say("Голоса нет, вместо голоса шелест. Но шелест расходится по корням, по всему лесу, "
           "до каждого, кого ты тут встретил.", C.GRY)
    ui.sleep(1.0)
    for _, who in helped_list(st):
        ui.say("  ...и приходит " + who + ".", C.YEL)
        ui.sleep(0.4)
    print()
    ui.say("И первой, конечно, прибегает Саша. Хватает тебя за рукав обеими руками, упирается ногами.", C.RED)
    ui.say("Они берутся за кору. За корни. За тебя. И тянут. Никто не знает как правильно, "
           "все тянут кто куда, Ефим ругается, щенок тявкает. И дуб... отпускает. Сам. "
           "Как будто ему тоже надоело.", C.WHT)
    ui.say("Лес не может удержать того, кого держат за руку. Это было единственное правило, "
           "которое он от всех прятал.", C.CYN)
    print()
    art.show(art.OAK, C.GRN)
    ui.narr("В дупле записка. Сашин почерк, буквы скачут.")
    ui.type_out("     «Приходи ещё. Только не один.»", C.YEL + C.B, delay=0.05)
    ui.thought("Не один. Ну да. Так и пришёл.")
    epilogue_people(st)
    return finish(st, "Вместе")


def end_sad(st):
    state.mark_ending("Табличка")
    ui.header("Табличка", "финал")
    ui.narr("Ты перестаёшь сопротивляться. Это оказывается легко. Так легко, что даже не страшно.")
    ui.say("Лес вздыхает и снова замыкается в круг. Снег ложится гуще, ели темнеют. "
           "А у старого пня девочка в красной шапке зовёт тебя по имени. Долго. Пока не стемнеет.", C.GRY)
    print()
    for line in art.PLAQUE.format(name=st["name"][:22]).strip("\n").split("\n"):
        print(paint(line, C.YEL))
    print()
    ui.say("От тебя осталась только эта табличка у дуба. Аккуратная, медная, как на памятнике.", C.GRY)
    if st.get("names"):
        ui.say("Иногда новый путник проходит мимо и переписывает твоё имя на край карты. Зачем, сам не знает.", C.GRY)
    return finish(st, "Табличка")


def finish(st, name):
    seen = state.endings_seen()
    regular = [e for e in seen if e != "Вместе"]
    lines = [f"Финал: «{name}».",
             f"Открыто финалов: {len(regular)} из 2" + ("  + секретный" if "Вместе" in seen else ""),
             f"Кругов в первом акте: {st['loop']}.  Имён записано: {len(st.get('names', []))}.",
             f"Помог: {len(helped_list(st))} (" + ", ".join(h[0] for h in helped_list(st)) + ")"]
    if "Вместе" not in seen and len(regular) >= 2:
        lines.append("Говорят, у дуба можно ответить не только «да» и «нет».")
    ui.box(lines, "Конец", C.GRN)
    k = ui.ask([("oak", "Вернуться к дубу и решить иначе"), ("new", "Начать заново"), ("quit", "Выйти")])
    if k == "oak":
        return "a3_oak"
    if k == "new":
        return "__reset__"
    st["stage"] = "a3_oak"
    st.save()
    sys.exit(0)


STAGES = {
    "a3_enter": a3_enter,
    "a3_old_stump": a3_old_stump,
    "a3_empty": a3_empty,
    "a3_door": a3_door,
    "a3_ash_self": a3_ash_self,
    "a3_birch_glitch": a3_birch_glitch,
    "a3_gate": a3_gate,
    "a3_gate_check": a3_gate_check,
    "a3_free": a3_free,
    "a3_empty_map": a3_empty_map,
    "a3_oak": a3_oak,
    "a3_rings": a3_rings,
    "end_good": end_good,
    "end_together": end_together,
    "end_sad": end_sad,
}
