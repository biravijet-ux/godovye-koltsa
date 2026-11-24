"""Акт 2 и 2.1. Лес с картой, области со своими правилами, Сторож, исчезающий дуб,
та же дорога ещё раз — и Штольня."""
import random

from . import art, encounter, map_view, puzzles, threads, ui
from .act1 import trade
from .ui import C, paint

REGIONS = {
    "birch": dict(name="Березняк", biome="birch",
                  desc="Белые стволы, светло, видно далеко. После ущелья здесь легко дышится.",
                  rule="Хорошая видимость: на карте видно, что ждёт во всех точках."),
    "mine": dict(name="Старый рудник", biome="mine",
                 desc="Ржавые рельсы уходят под снег. Из-под земли тянет теплом, и пахнет железом.",
                 rule="Камней много. В конце Штольня, и мимо неё не пройти."),
    "bog": dict(name="Топь", biome="bog",
                desc="Кочки, туман, чёрная вода под тонким льдом. Ноги чавкают.",
                rule="После каждого шага одну из соседних точек затягивает водой. Передумать не выйдет."),
    "spruce": dict(name="Ельник", biome="spruce",
                   desc="Ели чёрные, смыкаются над головой. Темно, хотя день.",
                   rule="Темно, не видно что впереди. Фонарём посветить можно, но звери свет тоже видят."),
    "ash": dict(name="Пепелище", biome="ash",
                desc="Тут когда-то был пожар. Стволы чёрные, снег серый, пахнет старым дымом.",
                rule="На каждом обгоревшем стволе медная табличка. Чем дальше, тем они новее."),
    "ridge": dict(name="Каменная гряда", biome="ridge",
                  desc="Голые камни и ветер. От него лицо деревенеет за минуту.",
                  rule="Ветер: каждый шаг по карте −1 тепло. Не задерживайся."),
}
NEXT = {"birch": ["mine"], "mine": ["bog", "spruce"], "bog": ["ash"], "spruce": ["ash"],
        "ash": ["ridge"], "ridge": []}
EXIT_KIND = {"mine": "shaft", "ridge": "boss"}

GLYPH = {"fight": ("Б", C.RED), "puzzle": ("З", C.CYN), "event": ("С", C.WHT), "trader": ("Т", C.YEL),
         "camp": ("К", C.YEL), "cache": ("Х", C.MAG), "shaft": ("◆", C.GRY), "boss": ("◆", C.RED),
         "pass": ("◆", C.GRN)}
NAMES = {"fight": "бой", "puzzle": "загадка", "event": "событие", "trader": "торговец", "camp": "костёр",
         "cache": "тайник", "shaft": "Штольня", "boss": "?", "pass": "выход из области"}
SIGNS = {"fight": ["тянет мокрой шерстью", "снег взрыт когтями", "кто-то сопит за деревьями",
                   "клочья шерсти на кустах"],
         "puzzle": ["странные зарубки на стволах", "кто-то насвистывает", "на снегу выложен узор из шишек",
                    "следы, много следов"],
         "event": ["тропа уходит в туман", "что-то темнеет на снегу", "слышен скрип", "кто-то тихо говорит"],
         "trader": ["слышен стук котелка", "пахнет чаем", "мяукает кто-то"],
         "camp": ["видна струйка дыма", "пахнет костром"],
         "cache": ["у корней что-то блестит", "под ёлкой бугорок, слишком ровный"],
         "shaft": ["чёрный зев штольни"], "boss": ["на гребне кто-то стоит"], "pass": ["тропа идёт дальше"]}
DIRS = {0: "Верхняя тропа", 1: "Средняя тропа", 2: "Нижняя тропа"}


def phase21(st):
    return st.has("act21")


# --------------------------------------------------------------------- погода
# Погода — это настроение леса. В 2.1 лес тебя заметил, и ясно уже не бывает.
WEATHER = {
    "ясно": ("Ясно. Морозно, но видно далеко.", "Ничего особого."),
    "метель": ("Метель. Снег лепит в лицо, ничего не видно дальше вытянутой руки.",
               "В боях темно, как в ельнике. На карте видно только ближайшие точки."),
    "туман": ("Туман. Звуки идут непонятно откуда.", "В боях звери стоят ближе к тебе."),
    "оттепель": ("Оттепель. Снег мокрый, под ним вода.", "На тропах почти всегда промоины."),
}


def weather(st, rid):
    rng = random.Random(f"{st['seed']}:{rid}:w:{'21' if phase21(st) else '2'}")
    if phase21(st):
        return rng.choice(["метель", "туман", "оттепель"])
    if rid == "birch":
        return "ясно"
    return rng.choice(["ясно", "ясно", "метель", "туман", "оттепель"])


# --------------------------------------------------------------------- генерация карты

def region_map(st, rid):
    """Карта области из сида прохождения: в 2.1 она точь-в-точь та же."""
    rng = random.Random(f"{st['seed']}:{rid}")
    pool = ["fight", "fight", "fight", "event", "event", "event", "puzzle", "puzzle", "cache", "camp", "trader"]
    if rid == "ridge":
        pool += ["camp"]
    layers = []
    for k in range(3):
        n = rng.choice([2, 3, 3])
        cols = [0, 2] if n == 2 else [0, 1, 2]
        nodes = []
        for i, col in enumerate(cols):
            t = rng.choice(pool)
            nodes.append(dict(id=f"{rid}:{k}:{i}", type=t, col=col, sign=rng.choice(SIGNS[t]),
                              seed=rng.randint(1, 10 ** 6)))
        layers.append(nodes)
    # хотя бы один бой и одна передышка в области
    flat = [n for l in layers for n in l]
    if not any(n["type"] == "fight" for n in flat):
        layers[1][0]["type"] = "fight"
    if not any(n["type"] in ("camp", "trader") for n in flat):
        layers[2][-1]["type"] = "camp"
    # событий (нитей) должно хватать: хотя бы по одному в первых двух рядах
    for k in (0, 1):
        if not any(n["type"] == "event" for n in layers[k]):
            cand = [n for n in layers[k] if n["type"] not in ("camp", "trader")] or layers[k]
            cand[-1]["type"] = "event"
    caches = [n for n in flat if n["type"] == "cache"]
    for n in caches[1:]:
        n["type"] = "event"
    for n in flat:
        n["sign"] = random.Random(n["seed"]).choice(SIGNS[n["type"]])
    ex_t = EXIT_KIND.get(rid, "pass")
    exit_node = dict(id=f"{rid}:X", type=ex_t, col=1, sign=SIGNS[ex_t][0], seed=rng.randint(1, 10 ** 6))
    for k in range(2):
        make_edges(layers[k], layers[k + 1], rng)
    for n in layers[2]:
        n["up"] = [1]
    return layers, exit_node


def make_edges(lower, upper, rng):
    """Связи между рядами: только соседние колонки и без пересечений линий."""
    ucols = [n["col"] for n in upper]
    edges = {(n["col"], u) for n in lower for u in ucols if abs(n["col"] - u) <= 1}

    def deg_ok(e):
        a, b = e
        out_a = sum(1 for x in edges if x[0] == a)
        in_b = sum(1 for x in edges if x[1] == b)
        return out_a > 1 and in_b > 1

    changed = True
    while changed:
        changed = False
        for e1 in sorted(edges):
            for e2 in sorted(edges):
                if e1[0] < e2[0] and e1[1] > e2[1]:          # линии пересекаются
                    cand = [e for e in (e1, e2) if deg_ok(e)]
                    victim = rng.choice(cand) if cand else e1
                    edges.discard(victim)
                    changed = True
                    break
            if changed:
                break
    for n in lower:
        n["up"] = sorted(u for (a, u) in edges if a == n["col"])


def find_node(st, rid, nid):
    layers, ex = region_map(st, rid)
    if nid == ex["id"]:
        return 3, ex
    for k, l in enumerate(layers):
        for n in l:
            if n["id"] == nid:
                return k, n
    return None, None


def node_state(st, nid):
    return st["nodes"].setdefault(nid, {"looted": False, "seen2": False, "seen21": False, "flooded": False})


def reachable(st, rid):
    layers, ex = region_map(st, rid)
    pos = st["pos"]
    if pos is None:
        cand = layers[0]
    else:
        k, cur = find_node(st, rid, pos)
        if k == 3:
            return []
        if k == 2:
            return [ex]
        cand = [n for n in layers[k + 1] if n["col"] in cur.get("up", [])]
    flood_key = "flooded21" if phase21(st) else "flooded"
    return [n for n in cand if not node_state(st, n["id"]).get(flood_key)]


# --------------------------------------------------------------------- отрисовка

def render_map(st, rid, reach, lit=False):
    reg = REGIONS[rid]
    layers, ex = region_map(st, rid)
    order = {n["id"]: i + 1 for i, n in enumerate(reach)}
    path = set(st.get("path_now", []))
    flood_key = "flooded21" if phase21(st) else "flooded"
    w = weather(st, rid)
    sub = ("та же дорога, снова.  " if phase21(st) and st.has(f"intro_{rid}_2") else "") + "погода: " + w
    ui.header(reg["name"], sub, C.GRN)
    ui.dim(region_desc(st, rid) + " " + region_rule(st, rid))
    print()
    def label(n, k):
        ns = node_state(st, n["id"])
        word, col = NAMES[n["type"]], GLYPH[n["type"]][1]
        clear = (rid == "birch" and w not in ("метель", "туман")) or st.has("varvara_map")
        show = clear or k == 3 or n["id"] in path or (n["id"] in order and (rid != "spruce" or lit))
        if not show:
            word, col = "?", C.GRY
        if ns.get(flood_key):
            word, col = "затоплено", C.BLU
        return word, col

    ui.say("МАРШРУТ  →  Вход · участок 1 · участок 2 · участок 3 · выход", C.CYN)
    for line in map_view.route_rows(layers, ex, label, st["pos"], order, path):
        print(line)
    print(paint("  ● ты здесь    жёлтая цифра — доступный путь    ✓ пройдено", C.GRY))
    print()
    print("  " + paint(f"Тепло {'♥' * st['warmth']}{'·' * (st['max_warmth'] - st['warmth'])}", C.RED)
          + paint(f"   камни {st.n('камень')}  верёвка {st.n('верёвка')}  опята {st.n('грибы')}"
                  f"  фонарь {'есть' if st.n('фонарь') else 'нет'}", C.GRY))
    print(paint("  Идти можно слева направо по линиям. Цифры совпадают с выбором ниже.", C.GRY))


# --------------------------------------------------------------------- стадии

def region_rule(st, rid):
    if rid == "birch" and weather(st, rid) in ("метель", "туман"):
        return "Обычно отсюда видно всю область, но сейчас погода прячет дальние точки."
    return REGIONS[rid]["rule"]


def region_desc(st, rid):
    w = weather(st, rid)
    if rid == "birch" and w in ("метель", "туман"):
        return ("Белые стволы тонут в " + ("метели" if w == "метель" else "тумане") +
                ". Березняк, где обычно видно далеко, сейчас просматривается шагов на десять.")
    return REGIONS[rid]["desc"]


SASHA = {
    "birch": "Далеко между берёзами мелькает красная шапка. Ты кричишь, но она не оборачивается.",
    "mine": "На рельсах маленькие следы. Саша прыгала по шпалам, как летом на станции.",
    "bog": "На кочке лежит красный помпон. Оторвался? Или его оставили, чтобы ты нашёл?",
    "spruce": "В темноте кто-то смеётся Сашиным смехом. Пересмешник? Ты не уверен.",
    "ash": "На обгорелом стволе мелом нарисована стрелка и написано: «ТУДА! С.»",
    "ridge": "С гребня видно долину. Внизу у дуба сидит кто-то маленький в красной шапке.",
}
SASHA21 = {
    "birch": "Красной шапки больше нигде не видно. Только ветер.",
    "mine": "Следы на шпалах те же. Но теперь они идут в обе стороны.",
    "bog": "Помпона на кочке нет. Ты точно положил его в карман? Карман пустой.",
    "spruce": "Смех в темноте повторяется. Слово в слово, как в прошлый раз.",
    "ash": "Стрелка мелом на стволе. Под ней новая надпись, корявая: «НЕ УХОДИ БЕЗ МЕНЯ».",
}


def a2_start(st):
    st["region"] = "birch"
    st["pos"] = None
    st["path_now"] = []
    st["region_path"] = ["birch"]
    return region_intro(st)


def region_intro(st):
    rid = st["region"]
    reg = REGIONS[rid]
    key = f"intro_{rid}_{'21' if phase21(st) else '2'}"
    if not st.has(key):
        st.set(key)
        prev = st["region_path"][-2] if len(st["region_path"]) > 1 else None
        ui.transition(REGIONS[prev]["biome"] if prev else reg["biome"], reg["biome"],
                      PASS_TEXT.get((prev, rid), f"{reg['name']}..."))
        ui.header(reg["name"], "")
        ui.narr(region_desc(st, rid))
        ui.say("Правило области: " + region_rule(st, rid), C.YEL)
        w = weather(st, rid)
        ui.say(WEATHER[w][0] + " " + WEATHER[w][1], C.CYN)
        if phase21(st) and st.has(f"intro_{rid}_2"):
            ui.say(REVISIT_TEXT.get(rid, "Ты здесь уже был."), C.MAG)
        elif phase21(st):
            ui.say("В прошлый раз ты сюда не сворачивал. Но лес всё равно смотрит так, будто ты тут был.", C.MAG)
        sasha = (SASHA21 if phase21(st) and st.has(f"intro_{rid}_2") else SASHA).get(rid)
        if rid == "ridge" and w in ("метель", "туман"):
            sasha = "В просвете между порывами на миг виден дуб внизу. Красное пятнышко у корней. Моргаешь — снова белая стена."
        if sasha:
            ui.say(sasha, C.RED)
        ui.pause()
    return "a2_map"


REVISIT_TEXT = {
    "birch": "Те же берёзы. Тот же снег. На тропе твои вчерашние следы, только вчера было десять минут назад.",
    "mine": "Рельсы, вагонетка, надпись над Штольней. Всё на месте. Даже твои следы на месте, никуда не делись.",
    "bog": "Туман стоит как стоял. Только лёд стал тоньше, это слышно по треску.",
    "spruce": "Ели как будто подвинулись ближе друг к другу. Пока ты не смотрел.",
    "ash": "Таблички стоят рядами. Их стало больше? Ты не помнишь, сколько было. Не хочешь помнить.",
}

# плавные переходы между областями: лес меняется постепенно
PASS_TEXT = {
    ("birch", "mine"): "Берёзы всё реже... из-под снега торчит рельс... потом ещё один...",
    ("mine", "bog"): "Рельсы уходят под воду. Под ногой чавкает. Пахнет тиной...",
    ("mine", "spruce"): "Рельсы обрываются. Ели. Темнеет так, будто кто-то выключил свет...",
    ("bog", "ash"): "Кочки кончаются. Туман становится серым. Это не туман, это пепел...",
    ("spruce", "ash"): "Ели всё чернее... а потом они просто обгорелые. Пахнет дымом...",
    ("ash", "ridge"): "Пепел сменяется камнем. Ветер. Сразу, без предупреждения...",
}


def a2_map(st):
    rid = st["region"]
    lit = st.get("lit_pos") == (st["pos"] or "entry") and rid == "spruce"
    reach = reachable(st, rid)
    render_map(st, rid, reach, lit)
    opts = []
    for n in reach:
        sign = n["sign"]
        if rid == "spruce" and not lit and n["type"] not in ("shaft", "boss", "pass") and not st.has("varvara_map"):
            sign = "темнота"
        if st.has("varvara_map") and n["type"] in ("fight", "puzzle", "event", "trader", "camp", "cache"):
            sign += f" ({NAMES[n['type']]}, по карте Варвары)"
        direction = DIRS[n["col"]] if len(reach) > 1 else "Дальше"
        opts.append((n["id"], f"{direction}: {sign}"))
    if (rid == "spruce" and not lit and st.n("фонарь") and not st.has("varvara_map")
            and any(n["type"] not in ("pass",) for n in reach)):
        opts.append(("light", "Посветить вперёд фонарём (видно точки, но звери заметят)"))
    if st.has("back_unlocked"):
        opts.append(("back", paint("← Назад, по своим следам, к Штольне", C.CYN)))
    if not reach and not st.has("back_unlocked"):
        opts.append(("stuck", "Стоять"))
    while True:
        k = ui.ask(opts, title="Куда идти?", hidden={"назад": "egg_back", "вернуться": "egg_back"})
        if k == "egg_back" and not st.has("back_unlocked"):
            n = st["egg_back"] = st.get("egg_back", 0) + 1
            ui.say(["Оборачиваешься. Тропы сзади нет. Просто снег, ровный, как простыня.",
                    "Нету там ничего. Варвара же сказала: только вперёд.",
                    "Ты упрямый. Это хорошо. Это потом пригодится."][min(n - 1, 2)], C.GRY)
            continue
        if k == "egg_back":
            k = "back"
        break
    if k == "light":
        st["lit_pos"] = st["pos"] or "entry"
        st.set("lit_spruce")
        return "a2_map"
    if k == "back":
        return go_back(st)
    if k == "stuck":
        return "a2_map"
    # шаг по карте
    if rid == "ridge":
        st.hurt(1)
        ui.dim("Ветер режет лицо. −1 тепло.")
        if st["warmth"] <= 0:
            st["warmth"] = 2
            ui.danger("Ты падаешь за камень, прячась от ветра, и долго растираешь руки. (тепло 2)")
            ui.pause()
    if rid == "bog":
        others = [n for n in reach if n["id"] != k]
        if others:
            rng = random.Random(f"{st['seed']}:{k}:flood")
            f = rng.choice(others)
            node_state(st, f["id"])["flooded21" if phase21(st) else "flooded"] = True
            ui.say(f"Сзади чавкает. Путь «{DIRS[f['col']].lower()}» уходит под воду. Всё, туда уже никак.", C.BLU)
            ui.pause()
    hard_light = rid == "spruce" and lit
    st["pos"] = k
    st.setdefault("path_now", []).append(k)
    st["history"].append(k)
    return resolve(st, k, hard_light)


def go_back(st):
    ui.header("Назад", "")
    via = "топь" if "bog" in st.get("region_path", []) else "ельник"
    ui.narr("Разворачиваешься. Первый раз лес не сопротивляется, тропа за спиной не пропала. "
            f"Твои следы ведут обратно. Через Пепелище, через туман, через {via}. Мимо всего, что ты уже видел.")
    if st.has("canary_alive"):
        ui.say("Канарейка за пазухой поёт всю дорогу. Пять нот, по кругу.", C.YEL)
    ui.transition(REGIONS[st["region"]]["biome"], "mine", "Ты идёшь назад по своим следам...")
    st["region"] = "mine"
    st["pos"] = "mine:X"
    return "a2_shaft"


# --------------------------------------------------------------------- точки

def resolve(st, nid, hard_light=False):
    rid = st["region"]
    _, n = find_node(st, rid, nid)
    ns = node_state(st, nid)
    hard = phase21(st) or hard_light
    t = n["type"]
    rng = random.Random(n["seed"] + (7 if phase21(st) else 0))
    title = REGIONS[rid]["name"]
    if t == "shaft":
        return "a2_shaft"
    if t == "boss":
        return "a2_boss"
    if t == "pass":
        return region_exit(st)
    if t == "fight":
        if phase21(st) and ns["looted"]:
            ui.header(title, "бой")
            ui.say("Тут ты уже дрался. Снег взрыт, на кусте клок шерсти. Но зверь вернулся. "
                   "И он тебя, кажется, запомнил.", C.MAG)
            ui.pause()
        fewer = False
        if phase21(st) and st.has("cub_freed") and not st.has("cubhelp_" + rid):
            st.set("cubhelp_" + rid)
            fewer = True
            ui.header(title, "бой")
            ui.say("Из кустов выскакивает знакомый хромой шорох, подрос уже. Тявкает, носится кругами "
                   "и уводит одного из зверей за собой в чащу. Со вторым придётся самому.", C.YEL)
            ui.pause()
        res = encounter.random_encounter(st, rng, rid, hard=hard, title=title, place="бой",
                                         weather=weather(st, rid), fewer=fewer)
        if not ns["looted"] and not res.get("skipped"):
            ns["looted"] = True
            g = rng.randint(1, 2)
            st.add("грибы", g)
            find = rng.choice([
                "У поваленной берёзы, где возился зверь, опята. Мелкие, но крепкие.",
                "В снегу, который разрыл зверь, пара опят. Он что-то искал, а нашёл ты.",
                "На пне у тропы опята. Пока шла возня, ты их и не заметил.",
                "Под кустом чья-то брошенная котомка, в ней сушёные опята.",
            ])
            ui.say(f"{find} (+{g} {ui.plural(g, 'опёнок', 'опёнка', 'опят')})", C.YEL)
            ui.pause()
    elif t == "puzzle":
        puzzles.run(st, rng, rid, ns, hard)
    elif t == "cache":
        puzzles.cache(st, rng, ns, hard)
    elif t == "event":
        if not threads.run_node(st, rid, ns, title):
            events(st, rid, rng, ns)
    elif t == "trader":
        ui.header(title, "торговец")
        if phase21(st) and ns.get("seen2"):
            ui.voice("Ефим", "Мы с тобой уже торговались. Тут же. Цены, извини, выросли. Зима.")
        elif phase21(st):
            ui.voice("Ефим", "О. Ты. Я тебя тут ещё не видел, а такое чувство, что видел. Цены выросли, зима.")
            if st.has("boss_peace"):
                ui.voice("Ефим", "Слушай... мне тут сон снился. Будто Гришка домой пришёл. С термосом. Ну ладно.")
        else:
            ui.voice("Ефим", "Ну надо же. Выбрался из ущелья? Я ж говорил, кто вверх смотрит...")
            ui.say("Кот Пепел спит на мешках. Тот же кот. Тот же мешок.", C.GRY)
            if not st.has("efim_story"):
                st.set("efim_story")
                ui.voice("Ефим", "Я ведь тоже сюда гулять пришёл. Лет сорок назад. С сыном, с Гришкой. "
                         "Он к дубу побежал, а я отстал. Вот и сижу, торгую. Жду.")
        if st.n("чага") and not threads.done(st, "efim"):
            threads.efim_give(st)
        if st.n("письмо") and (st.has("boss_peace") or st.has("boss_fought")):
            if ui.ask([("give", "Отдать Ефиму письмо Веры к Грише"), ("keep", "Не сейчас")]) == "give":
                st.take("письмо")
                st.set("letter_delivered")
                ui.say("Ефим читает, водя пальцем по строчкам. Губы шевелятся.", C.GRY)
                if st.has("boss_peace"):
                    ui.voice("Ефим", "Вера... Хорошая была девка. Передам Гришке. Он дома уже, представляешь? "
                             "Вчера пришёл. Или сорок лет назад. Не разберёшь тут.")
                else:
                    ui.voice("Ефим", "Вера... Она ему писала. А он так и стоит на гряде. Сохраню. "
                             "Вдруг всё-таки придёт.")
                ui.pause()
        trade(st, markup=1 if phase21(st) else 0)
    elif t == "camp":
        ui.header(title, "костёр")
        key = "c21" if phase21(st) else "c2"
        if ns.get(key):
            ui.say("Кострище холодное. Ты тут уже грелся. Вон даже палочка твоя, которой угли ворошил.", C.GRY)
        else:
            ns[key] = True
            st.heal(3)
            ui.narr("Чьё-то брошенное кострище. Угли ещё живые. Раздуваешь, пока глаза не заслезятся, "
                    "и греешь руки. Хорошо.")
            ui.say("+3 тепла. Прогресс сохранён.", C.YEL)
        threads.warm_at_fire(st)
        ui.pause()
    if phase21(st):
        ns["seen21"] = True
    else:
        ns["seen2"] = True
    return "a2_map"


def region_exit(st):
    rid = st["region"]
    nxt = NEXT[rid]
    if rid == "ash" and phase21(st):
        return "a21_future"
    if len(nxt) == 1:
        new = nxt[0]
    else:
        ui.header(REGIONS[rid]["name"], "развилка")
        ui.narr("Тропа расходится. Вниз — к туману, оттуда пахнет стоячей водой. Вверх — в ельник, такой тёмный, что ничего не разглядеть.")
        if phase21(st):
            prev = [r for r in st["region_path"] if r in nxt]
            if prev:
                ui.say(f"В прошлый раз ты шёл через {REGIONS[prev[-1]]['name']}.", C.GRY)
        new = ui.ask([(r, f"{REGIONS[r]['name']} — {REGIONS[r]['rule']}") for r in nxt])
    st["region"] = new
    st["pos"] = None
    st["path_now"] = []
    st["region_path"].append(new)
    st.pop("lit_pos", None)
    return region_intro(st)


# --------------------------------------------------------------------- события

# Обычные события (не нити). В области не повторяются. В 2.1 у каждого свой отголосок.
EVENT_POOL = {
    "birch": ["sap", "fox", "snowman"],
    "mine": ["cart", "plaque", "rails"],
    "bog": ["ice", "reeds", "boat"],
    "spruce": ["backpack", "owl", "mitten"],
    "ash": ["plaques", "firepit", "photo"],
    "ridge": ["cairn", "binocular", "plaque"],
}


def events(st, rid, rng, ns):
    title = REGIONS[rid]["name"]
    pool = EVENT_POOL[rid]
    if ns.get("fallback"):
        ev = ns["fallback"]
    else:
        seen = st.setdefault("ev_seen", [])
        fresh = [e for e in pool if f"{rid}:{e}" not in seen] or pool
        ev = rng.choice(fresh)
        ns["fallback"] = ev
        seen.append(f"{rid}:{ev}")
    ui.header(title, "")
    done = st.has("ev_" + ev + "_" + rid)
    p21 = phase21(st)

    if ev == "sap":
        ui.narr("Старая берёза, кора толстая, в трещинах. Зимой берёзы спят вообще-то, а эта плачет: "
                "из трещины течёт сок.")
        if done:
            ui.say("Надрез твой, косой, как ты всегда режешь. Засох. Сок больше не идёт.", C.MAG)
        elif ui.ask([("take", "Надрезать и напиться"), ("no", "Не трогать")]) == "take":
            st.set("ev_sap_" + rid)
            st.heal(2)
            ui.say("Сладкий. И тёплый почему-то, как будто его подогрели. +2 тепла.", C.YEL)
    elif ev == "plaque":
        name = rng.choice(["А. Кузнецова", "Г. Ильин", "Митя", "Э. Ш.", "В. Бирюков", "кот Пепел (не уверен)"])
        ui.narr("У корней табличка, медная, потемневшая. Аккуратненькая, как на памятнике.")
        ui.say(f"«Здесь стоит дерево. Раньше это был человек: {name}».", C.WHT)
        if "Пепел" in name:
            ui.thought("Кот Пепел? Это кот Ефима. Он же живой, он у костра спал. Или это другой Пепел...")
        else:
            ui.thought("Дерево с чьим-то именем. Шутка такая? Кто-то же за этими табличками следит.")
        st["plaques"] = st.get("plaques", 0) + 1
    elif ev == "fox":
        ui.narr("На тропе сидит лиса и смотрит прямо на тебя. Отходит на пару шагов, оглядывается. Ждёт.")
        if done:
            ui.say("Лиса смотрит долго, потом уходит. Как будто знает, что ты уже за ней ходил.", C.MAG)
        elif ui.ask([("follow", "Пойти за лисой"), ("no", "Не сворачивать")]) == "follow":
            st.set("ev_fox_" + rid)
            st.add("грибы", 3)
            ui.say("Лиса приводит к поваленной берёзе, а она вся в опятах. Лиса садится и смотрит, "
                   "как ты собираешь. Ей не нужно, она просто показывает. +3 опят.", C.YEL)
    elif ev == "snowman":
        ui.narr("Посреди поляны снеговик. Кривой, с веткой вместо носа. На нём шарф. Твой шарф.")
        ui.say("Ты щупаешь шею. Шарф на тебе. И на снеговике тоже. Одинаковые, с дыркой у края.", C.MAG)
        if p21:
            ui.say("Снеговик повернулся. Немного. Ты уверен, что раньше он смотрел на север.", C.MAG)
        elif ui.ask([("hat", "Поправить ему нос"), ("no", "Отойти подальше")]) == "hat":
            ui.say("Поправляешь нос. Под веткой в снегу камень, гладкий. Забираешь. (+1 камень)", C.YEL)
            st.add("камень", 1)
    elif ev == "cart":
        ui.narr("Вагонетка на ржавых рельсах, доверху полная серой руды.")
        if done:
            ui.say("Вагонетка пустая. На дне в рыжей пыли отпечатки твоих перчаток.", C.MAG)
        else:
            st.set("ev_cart_" + rid)
            st.add("камень", 2)
            ui.say("Набиваешь карманы. Тяжело, зато камни звонкие. +2 камня.", C.YEL)
    elif ev == "rails":
        ui.narr("Рельсы гудят. Тихо, низко, как провода. Ты прикладываешь ухо к железу.")
        ui.say("Там стук. Тук... тук... тук... тук... тук. Пять. Потом тишина и опять пять.", C.MAG)
        if p21:
            ui.thought("Пять раз. Я же знаю уже, что это значит. Или скоро узнаю.")
        else:
            ui.thought("Просто рельсы остывают. Металл стучит, когда остывает. Наверное.")
    elif ev == "ice":
        ui.narr("Тропа упирается в протоку. Лёд серый, тонкий, весь в пузырях.")
        opts = []
        if st.n("камень"):
            opts.append(("stone", "Проверить лёд камнем"))
        opts.append(("go", "Идти так, авось"))
        thaw = weather(st, rid) == "оттепель"
        if ui.ask(opts) == "stone":
            st.take("камень")
            ui.say("У берега под снегом видна вода. Бросаешь камень дальше от промоины: он звенит и "
                   "отскакивает. Проверяешь край палкой и проходишь вдоль берега по целому льду.", C.YEL)
        elif rng.random() < (0.8 if thaw else 0.5):
            st.hurt(2)
            ui.danger("Лёд проламывается. Вода по пояс, ледяная, дух вышибает. −2 тепла.")
        else:
            ui.say("Лёд трещит, но держит. Ты не дышишь, пока не выходишь на кочку.", C.GRY)
    elif ev == "reeds":
        ui.narr("Камыш шуршит, хотя ветра нет вообще. И в камышах кто-то поёт. Человеческим голосом.")
        shout = st.get("shout", "За корнями лаз! Лезь по корням!")
        ui.type_out(f"     «{shout}»", C.MAG, delay=0.04)
        ui.say("Твой голос. Твои слова. Пересмешник выучил их там, в ущелье.", C.GRY)
        if p21:
            ui.say("Теперь он поёт ещё и: «Назад. Штольня. Пять раз». Ты этого ещё не слышал. Или уже?", C.MAG)
    elif ev == "boat":
        ui.narr("Во льду вмёрзла лодка, вверх дном. На днище краской написано: «ВЕРНУСЬ К ОБЕДУ».")
        ui.thought("Гриша говорил... нет, Ефим говорил, что сын обещал к обеду. Это его?")
        if not done and ui.ask([("look", "Заглянуть под лодку"), ("no", "Не трогать")]) == "look":
            st.set("ev_boat_" + rid)
            st.add("верёвка")
            ui.say("Под лодкой сухо и пахнет смолой. Лежит моток верёвки, аккуратно свёрнутый. (+1 верёвка)", C.YEL)
        elif done:
            ui.say("Под лодкой пусто. Ты всё забрал. Надпись на днище облезла ещё сильнее.", C.MAG)
    elif ev == "backpack":
        ui.narr("Под ёлкой рюкзак. Такой же, как у тебя. Совсем такой же, даже значок с лисой.")
        if done:
            ui.say("Рюкзак открыт и пустой. Внутри записка, твой почерк: «не трогай мой рюкзак».", C.MAG)
        elif ui.ask([("take", "Обыскать"), ("no", "Не трогать чужое")]) == "take":
            st.set("ev_backpack_" + rid)
            st.add("верёвка")
            st.add("камень", 2)
            ui.say("Внутри верёвка и два камня. Как будто кто-то знал, что тебе нужно. (+1 верёвка, +2 камня)", C.YEL)
    elif ev == "owl":
        ui.narr("На суку сова. Смотрит не на тебя, а мимо. Тебе за спину.")
        ui.thought("Не оборачиваться. Не оборачиваться. Не...")
        if p21:
            ui.say("За спиной кто-то идёт. Твоим шагом. Чуть отстаёт.", C.MAG)
        elif ui.ask([("turn", "Обернуться"), ("no", "Не оборачиваться")]) == "turn":
            ui.say("Оборачиваешься. Никого. Только твои следы, и рядом ещё одни, такие же. "
                   "Они идут не за тобой, а навстречу.", C.MAG)
    elif ev == "mitten":
        ui.narr("На ветке висит детская варежка, красная, с оленем. Кто-то нашёл и повесил, чтоб видно было.")
        if p21:
            ui.say("Варежки нет. Только нитка на ветке. Значит, кто-то за ней вернулся. Хоть кто-то вернулся.", C.YEL)
        else:
            ui.thought("Не трогай. Её ищут. Пусть найдут.")
    elif ev == "plaques":
        ui.narr("Поляна среди обгорелых стволов. Ровными рядами стоят медные таблички, у каждого дерева своя.")
        ui.say("«...раньше это была Вера». «...раньше это был Андрей Палыч». «...раньше это были двое».", C.WHT)
        ui.say("Одна табличка пустая. Медь чистая, новенькая. Ждёт кого-то.", C.MAG)
        st["plaques"] = st.get("plaques", 0) + 3
    elif ev == "firepit":
        ui.narr("Кострище, холодное, обложено камнями.")
        if done:
            ui.say("Зола ещё тёплая. Твой костёр. Ты вроде бы его не тушил.", C.MAG)
        elif st.n("грибы") >= 1 and ui.ask([("fire", "Развести огонь (1 опёнок на растопку, ну почти)"),
                                            ("no", "Идти дальше")]) == "fire":
            st.set("ev_firepit_" + rid)
            st.take("грибы")
            st.heal(3)
            ui.say("Огонь занимается неохотно, но занимается. Сидишь, пока пальцы не начинают гнуться. +3 тепла.", C.YEL)
    elif ev == "photo":
        ui.narr("В золе, обгорелая с края, фотография. Летний лес, дуб, под дубом кто-то стоит.")
        ui.say(f"Лица не видно, его прожгло. Но куртка видна. И ты знаешь, чья это куртка.", C.MAG)
        ui.say("На обороте карандашом: «лето. дошли. в следующий раз возьмём с собой ещё кого-нибудь»", C.WHT)
        ui.thought("Это я писал. Летом. Я это помню. Помню же?")
    elif ev == "cairn":
        ui.narr("Пирамидка из камней, тур. Путники кладут по камню, чтобы дорога была.")
        if st.n("камень") and ui.ask([("put", "Положить камень"), ("no", "Пройти мимо")]) == "put":
            st.take("камень")
            st.heal(1)
            ui.say("Стало чуть теплее. Наверное, показалось. (+1 тепло)", C.YEL)
    elif ev == "binocular":
        ui.narr("На камне лежит бинокль. Старый, армейский, один окуляр треснутый.")
        if ui.ask([("look", "Посмотреть в бинокль"), ("no", "Не надо")]) == "look":
            ui.say("Далеко внизу, за лесом, видно поляну. На ней огромное серое дерево. "
                   "А вокруг дерева по тропе идёт человечек. Обходит дерево, уходит в лес... "
                   "и через минуту выходит с другой стороны. И опять.", C.MAG)
            ui.thought("Это ущелье. Это тот круг. Там кто-то ещё ходит. Или это я, ещё тогдашний.")
            st.set("saw_loop_binocular")
    ui.pause()


# --------------------------------------------------------------------- Штольня

def a2_shaft(st):
    ui.header("Штольня", "Старый рудник")
    ui.narr("Чёрный вход в гору, укреплён брёвнами. Над входом вырублено: КОПАЙ · БЕРИ · БЕЙ. "
            "Шагов через десять штольня упирается в стену. Глухую.")
    if st.has("back_unlocked"):
        return ritual(st)
    opts = [("knock", "Постучать по стене"), ("go", "Выйти и идти дальше")]
    while True:
        k = ui.ask(opts, hidden={"копать": "early", "копай": "early", "бей": "early", "ударить": "early"})
        if k == "early":
            ui.say("Ковыряешь стену. Порода сыплется, под ней снова порода. Стена не отвечает.", C.GRY)
            continue
        if k == "knock":
            if not st.has("knocked"):
                st.set("knocked")
                ui.say("Тук. Тук. Тишина... и через долгую секунду: тук. С той стороны.", C.MAG)
                ui.thought("Эхо. Это эхо. Конечно эхо.")
            else:
                ui.say("Тишина.", C.GRY)
            opts = [o for o in opts if o[0] != "knock"]
            continue
        break
    return region_exit(st)


RITUAL_REPLY = [
    "Копаешь, берёшь кусок руды, бьёшь по стене. Обычная руда. Обычный звук. Ну и ладно.",
    "Удар, и звук приходит с задержкой. Как будто стена сначала думает, а потом отвечает.",
    "Из стены выпадает камень. Гладкий, звонкий, один из тех, с валуна. Ты его у ручья бросал.",
    "Бьёшь, а изнутри отвечают. Тем же ритмом. Твоим ритмом.",
    "Стена вздыхает, как то дерево на поляне, и расходится трещиной. А за ней тропа, которой на карте нет.",
]


def ritual(st):
    ui.thought("«Пять раз». Он сказал пять раз. Я сказал.")
    seq = ["копать", "собрать", "ударить"]
    step = 0
    while st["ritual"] < 5:
        ui.say(f"Сделано кругов: {st['ritual']} из 5", C.GRY)
        k = ui.ask([("ritual", "Копать, взять руду, ударить по стене"), ("leave", "Уйти")],
                   hidden={"копай": "ritual", "бери": "ritual", "бей": "ritual", "копать": "ritual"})
        if k == "leave":
            ui.thought("Нет. Он сказал пять раз. Я видел его лицо. Своё лицо.")
            continue
        ui.say(RITUAL_REPLY[st["ritual"]], C.MAG if st["ritual"] else C.WHT)
        st["ritual"] += 1
        st.save()
    st["memory"]["штольня"] = "камень"
    ui.pause()
    return "a3_enter"


# --------------------------------------------------------------------- Сторож и исчезающий дуб

def a2_boss(st):
    ui.header("Каменная гряда", "на гребне")
    ui.narr("На гребне, спиной к ветру, стоит высокий человек в длинном плаще из коры. "
            "За его плечом на мгновение разрывается белая пелена. Внизу дерево — знакомая развилка ствола. Дуб."
            if weather(st, "ridge") in ("метель", "туман") else
            "На гребне, спиной к ветру, стоит высокий человек в длинном плаще из коры. "
            "А за ним, далеко внизу, в долине дерево. Даже отсюда видно, что дуб.")
    ui.thought("Наш дуб. Вон он. Внизу.")
    ui.voice("Сторож", "Не ходи к нему. Он не отпускает. Он забирает.", C.RED)
    ui.voice("Сторож", "Я тут стою, чтоб такие как ты разворачивались.", C.RED)
    opts = [("fight", "Пройти мимо него силой"), ("talk", "Спросить, кто он такой")]
    if st.n("термос"):
        opts.append(("thermos", "Показать ему термос Ефима"))
    if st.n("письмо"):
        opts.append(("letter", "Отдать ему письмо Веры"))
    hidden = {"гриша": "grisha", "григорий": "grisha", "термос": "thermos", "письмо": "letter"}
    while True:
        k = ui.ask(opts, hidden=hidden)
        if k == "thermos" and not st.n("термос") or k == "letter" and not st.n("письмо"):
            ui.say("У тебя этого нет.", C.GRY)
            continue
        if k in ("thermos", "letter"):
            return boss_peace(st, k)
        if k == "grisha":
            ui.say("Сторож вздрагивает от имени, как от пощёчины.", C.GRY)
            ui.voice("Сторож", "Откуда знаешь? ...Неважно. Ничего ты не знаешь. Иди отсюда.", C.RED)
            st.set("called_grisha")
            continue
        if k == "talk":
            ui.voice("Сторож", "Я был как ты. Пришёл погулять. Дошёл, дотронулся. "
                     "Лес оставил меня тут сторожить. Батя, наверное, до сих пор ждёт. Всё, уходи.", C.RED)
            opts = [o for o in opts if o[0] != "talk"]
            if len(opts) == 1:
                ui.thought("Батя. Если бы у меня было что-то от его отца...")
            continue
        break
    encounter.play(st, "Сторож", 6, [("сторож", 4)], bushes=[2], place="гребень гряды", can_skip=False)
    ui.header("Каменная гряда", "")
    st.set("boss_fought")
    ui.say("Сторож падает в снег. Слишком легко, будто и не собирался драться. "
           "Плащ из коры осыпается трухой, и под ним просто парень в старом свитере.", C.GRY)
    ui.voice("Сторож", "...Теперь он тебя заметил.", C.RED)
    ui.say("Он отворачивается и больше не встаёт. Ветер заметает его до плеч, а он даже не шевелится.", C.GRY)
    ui.pause()
    return oak_vanish(st)


def boss_peace(st, k):
    if k == "thermos":
        ui.say("Сторож долго смотрит на термос. Потом снимает рукавицу и трогает крышку. Там вмятина.", C.GRY)
        ui.voice("Сторож", "Это я его уронил. С крыльца. Батя орал на весь двор...", C.RED)
        ui.voice("Сторож", "Гриша я. Был Гриша.", C.RED)
    else:
        st.take("письмо")
        st.set("grisha_letter")
        ui.say("Сторож разворачивает записку. Читает. Ещё раз читает, губы шевелятся.", C.GRY)
        ui.voice("Сторож", "Не дошла, значит. А я стою тут и стою. Думал дождусь.", C.RED)
    if st.n("термос") and st.has("grisha_letter"):
        ui.say("Он забирает ещё и термос. Прижимает к груди вместе с письмом, как будто это одно и то же.", C.GRY)
    st.set("boss_peace")
    st["max_warmth"] += 1
    st.heal(3)
    ui.say("Снимает плащ из коры и накидывает тебе на плечи. Тёплый, как печка. (макс. тепла +1)", C.YEL)
    ui.voice("Гриша", "Иди. Только знай, теперь он тебя заметил. Меня он тоже так заметил.", C.RED)
    ui.say("И Гриша идёт вниз, к Ефиму, не оглядываясь. Снег за ним следы не заметает.", C.GRY)
    ui.pause()
    return oak_vanish(st)


def oak_vanish(st):
    ui.transition("ridge", "oak", "Спускаешься в долину, к дубу...")
    ui.header("Долина", "")
    art.show(art.OAK, C.GRN)
    ui.narr("Дуб. Настоящий. С той самой развилкой ствола, с дуплом, куда летом записки прятали. "
            "Под ним снега нет. Под ним трава. Зелёная.")
    ui.say("А под дубом сидит Саша. Красная шапка, коленки в снегу. Она машет тебе рукой: "
           "«Я первая! Я загадала!»", C.RED)
    ui.ask([("touch", "Подойти и дотронуться")])
    ui.header("Долина", "")
    art.show(art.OAK_FADED, C.GRY)
    ui.say("Пальцы проходят сквозь кору, как сквозь туман. Дуб тает. Ветка за веткой, "
           "и долина тает вместе с ним. И Саша тоже, вместе с улыбкой. Последней пропадает красная шапка.", C.MAG)
    ui.sleep(1.5)
    ui.transition("oak", "birch", "...")
    st.set("act21")
    st["region"] = "birch"
    st["pos"] = None
    st["path_now"] = []
    st["history"] = []
    st["region_path"] = ["birch"]
    st.heal(6)
    ui.header("Березняк", "")
    ui.narr("Белые стволы. Светло. Ты стоишь на входе в березняк. Там же, где Варвара тебе карту отдала.")
    ui.say("Карта в руке та же. Каждая тропинка та же. Точь-в-точь.", C.GRY)
    ui.thought("Нет. Нет-нет-нет. Я же победил. Я же дошёл.")
    ui.say("Где-то впереди кто-то бьёт камнем о камень. Медленно. Пять раз.", C.MAG)
    ui.box(["Часть 2.1. Та же дорога, только хуже.",
            "Звери злее, награды уже забраны. Погода испортилась. Лес тебя знает.",
            "Зато на точках, где ты не был, можно доделать то, что пропустил."], "", C.MAG)
    ui.pause()
    return region_intro(st)


def a21_future(st):
    ui.header("Пепелище", "дорога на гряду")
    ui.narr("Тропа к гряде завалена. Камни, корни вывороченные, стволы крест-накрест. "
            "Не пройти. Перелезть через такое невозможно.")
    ui.thought("Тупик. Лес закрыл единственную дорогу.")
    ui.sleep(1.0)
    ui.say("На завале, наверху, стоит человек.", C.CYN)
    ui.say("Куртка как у тебя. Шапка как у тебя. Лицо в саже, глаза красные, как будто не спал неделю. "
           "Нет. Как будто не спал несколько кругов.", C.CYN)
    ui.voice("Ты", "Назад. Штольня. Пять раз.", C.CYN)
    ui.say("Он говорит это так, будто сто раз повторял, чтобы не забыть. И пропадает. "
           "Не уходит, а просто его больше нет.", C.GRY)
    ui.thought("Назад? Отсюда нельзя назад. Варвара же говорила, лес не пускает...")
    ui.say("Оборачиваешься. А тропа за спиной не исчезла. Первый раз за всё время она просто есть.", C.YEL)
    st.set("back_unlocked")
    ui.box(["Открыто: «← Назад». Теперь можно идти по своим следам обратно."], "", C.CYN)
    ui.pause()
    return "a2_map"


STAGES = {
    "a2_start": a2_start,
    "a2_map": a2_map,
    "a2_shaft": a2_shaft,
    "a2_boss": a2_boss,
    "a21_future": a21_future,
}
