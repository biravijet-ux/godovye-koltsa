"""Загадки акта 2. Все генерируются из сида точки — в 2.1 те же, но награда уже забрана."""
import itertools
from collections import deque

from . import ui
from .ui import C, paint


def reward(st, rng, ns, hard):
    if ns["looted"]:
        ui.say("Награду тут уже забрали. Ты же и забрал. Но решить всё равно приятно было.", C.GRY)
        return
    ns["looted"] = True
    roll = rng.random()
    if roll < 0.25 and not st.has("mittens"):
        st.set("mittens")
        st["max_warmth"] += 1
        st.heal(1)
        ui.say("Шерстяные варежки! Колючие, но тёплые. Максимум тепла +1.", C.YEL)
    elif roll < 0.5 and st.n("верёвка") < 2:
        st.add("верёвка")
        ui.say("Моток верёвки. (+1 верёвка)", C.YEL)
    elif st.n("камень") < 4:
        st.add("камень", 1)
        ui.say("Гладкий звонкий камень. (+1 камень)", C.YEL)
    else:
        st.add("грибы", 1)
        ui.say("На дне свёрток с сушёным опёнком. (+1 опёнок)", C.YEL)
        if st.n("сахар") < 2:
            st.add("сахар")
            ui.say("Кусочек сахара убираешь в карман. «Съесть сахар» — вернуть 2 тепла между боями.", C.YEL)


def run(st, rng, rid, ns, hard):
    if ns.get("looted"):
        ui.narr("Узнаёшь место. Ты уже разобрался, как здесь пройти. На этот раз не задерживаешься.")
        ui.pause()
        return
    kinds = ["echo", "signs", "tracks"]
    if rid == "mine":
        kinds = ["levers", "levers", "echo"]
    if rid in ("bog", "spruce"):
        kinds = ["echo", "tracks", "signs"]
    if rid in ("ash", "ridge"):
        kinds = ["tracks", "signs", "echo"]
    if ns.get("puzzle") in kinds:
        kind = ns["puzzle"]
    else:
        seen = st.setdefault("puz_seen", [])
        kinds_seen = {x.split(":")[1] for x in seen}
        fresh = ([k for k in kinds if k not in kinds_seen]
                 or [k for k in kinds if f"{rid}:{k}" not in seen] or kinds)
        kind = rng.choice(fresh)
        ns["puzzle"] = kind
        seen.append(f"{rid}:{kind}")
    {"echo": echo, "signs": signs, "levers": levers, "tracks": tracks}[kind](st, rng, ns, hard)


# --------------------------------------------------------------------- следы

MY_TRACKS = ["подошва ёлочкой", "носки чуть внутрь, косолапо", "петляют и уходят назад",
             "на ремне фонаря зацепилась такая же красная нитка", "тот же размер что у тебя"]
BEAST_TRACKS = ["четыре лапы", "когти как крючки", "волочится что-то, хвост?", "пахнет мокрой шерстью",
                "шаг слишком длинный для человека"]
GOOD_TRACKS = ["маленькие, лёгкие", "идут прямо, ни разу не свернули", "на снегу крошки хлеба",
               "чуть присыпаны, давние", "палочка рядом втыкалась, как посох"]


def tracks(st, rng, ns, hard):
    ui.header("Следы", "загадка")
    ui.narr("На выходе с поляны висит Сашина красная нитка. До неё ведут три цепочки маленьких "
            "следов с узорчатой подошвой. Снег сохранил даже края каблуков.")
    ui.say("Вспоминаешь, как Саша убегала: у носка снег разбрызгивается вперёд, а каблук оставляет "
           "глубокий край сзади. Твой тяжёлый след пересекает все три цепочки. Она прошла раньше тебя.", C.GRY)
    trails = [
        ("good", ["носочки смотрят от тебя к нитке", "твоя подошва смяла края маленьких следов"]),
        ("my", ["носочки смотрят от нитки обратно к тебе", "твоя подошва смяла края маленьких следов"]),
        ("beast", ["носочки смотрят от тебя к нитке", "маленький каблук продавил твой большой след"]),
    ]
    rng.shuffle(trails)
    names = ["Первые", "Вторые", "Третьи"]
    for i, (_, feats) in enumerate(trails):
        ui.say(f"• {names[i]}: " + ", ".join(feats) + ".", C.WHT)
    k = ui.ask([(i, f"Идти по следам: {names[i].lower()}") for i in range(3)])
    kind = trails[k][0]
    if kind == "good":
        ui.good("Старые следы ведут от тебя. Ветка с ниткой ещё качается, а дальше на снегу виден следующий отпечаток. Идёшь за ним.")
        reward(st, rng, ns, hard)
    elif kind == "my":
        st.hurt(1)
        ui.danger("Цепочка идёт в обратную сторону. Через десять минут ты опять у своего следа. −1 тепло.")
    else:
        st.hurt(2)
        ui.danger("Эти отпечатки появились после тебя. За кустом что-то тяжело переставляет ноги. "
                  "Оставляет маленький след, потом большой. Отступаешь. −2 тепла.")
    ui.pause()


# --------------------------------------------------------------------- эхо

SOUNDS = ["стук", "свист", "хруст", "уханье"]


def echo(st, rng, ns, hard):
    ui.header("Пересмешник", "загадка")
    ui.narr("На ветке пересмешник, серый, взъерошенный, как старая варежка. Поёт коротенькую песню "
            "и смотрит с ожиданием. Повторишь, отдаст что у него в дупле. Они так играют.")
    st["echo_count"] = st.get("echo_count", 0) + (0 if ns.get("echo_done") else 1)
    ns["echo_done"] = True
    n = min(7, 3 + st["echo_count"] + (1 if hard else 0))
    seq = [rng.choice(SOUNDS) for _ in range(n)]
    ui.pause("Enter — слушать")
    print()
    print("     " + paint("  ·  ".join(s.upper() for s in seq), C.MAG, C.B))
    ui.sleep(1.2 + 0.6 * n)
    ui.pause("Enter — когда запомнишь")
    ui.header("Пересмешник", "загадка")
    print("  Повтори. Введи номера через пробел:  " +
          "   ".join(f"{paint(str(i + 1), C.YEL)}={s}" for i, s in enumerate(SOUNDS)))
    raw = ui.raw_input("песня> ").replace(",", " ").split()
    try:
        if any(not 1 <= int(x) <= len(SOUNDS) for x in raw):
            raise ValueError("неизвестный звук")
        ans = [SOUNDS[int(x) - 1] for x in raw]
    except (ValueError, IndexError):
        ans = []
    if ans == seq:
        ui.good("Пересмешник наклоняет голову набок, думает... и роняет что-то из дупла. Засчитал.")
        reward(st, rng, ns, hard)
    else:
        st.hurt(1)
        ui.danger("Пересмешник хохочет. Твоим голосом. И улетает. Обидно, и холодно ещё. −1 тепло.")
        ui.say("Было: " + " · ".join(seq), C.GRY)
    ui.pause()


# --------------------------------------------------------------------- приметы

RIGHT = [
    "{d} — на берёзе у развилки чёрный крестик углём. Свежий, уголь ещё пачкает палец.",
    "{d} — на сосне углём нарисован крестик, кривоватый, но крестик.",
    "{d} — на стволе крестик углём, и рядом в снегу маленькие следы. Узорчатая подошва.",
]
WRONG = [
    "{d} — тропа широкая и удобная, натоптанная. На стволе выцарапан ножом крестик.",
    "{d} — на ветке выцветшая красная ленточка. Кто-то когда-то отмечал путь.",
    "{d} — на стволе углём нарисован круг. Не крестик, круг.",
    "{d} — много старых следов, все в одну сторону. Обратно никто не шёл.",
    "{d} — на камне мелом стрелка, полустёртая. Мел, не уголь.",
    "{d} — тропа ровная, чистая. На дереве зарубка, свежая, ножом.",
]


def signs(st, rng, ns, hard):
    ui.header("Приметы", "загадка")
    ui.narr("Тропа рассыпается на три. Одна ведёт куда надо, две в никуда. Каждая чем-то помечена. "
            "Вопрос только, кому из тех, кто метил, можно верить.")
    if not st.has("q_varvara_marks_told"):
        st.set("q_varvara_marks_told")
        ui.thought("Варвара говорила что-то про метки. Углём? Ножом? Надо вспомнить.")
    dirs = ["Налево", "Прямо", "Направо"]
    right = rng.randrange(3)
    wrong_texts = rng.sample(WRONG, 2)
    lines = []
    wi = 0
    for i, d in enumerate(dirs):
        if i == right:
            lines.append(rng.choice(RIGHT).format(d=d))
        else:
            lines.append(wrong_texts[wi].format(d=d))
            wi += 1
    if hard:
        lines.append("Пересмешник с ветки орёт: «" + dirs[(right + 1) % 3] + "! " + dirs[(right + 1) % 3] + "!» "
                     "Они всегда врут, это все знают.")
    for l in lines:
        ui.say("• " + l, C.WHT)
    k = ui.ask([(i, d) for i, d in enumerate(dirs)])
    if k == right:
        ui.good("Крестик углём, как у Варвары. Через пять минут выходишь к поляне и даже снега в ботинки "
                "не набрал. (+1 тепло)")
        st.heal(1)
        reward(st, rng, ns, hard)
    else:
        st.hurt(1)
        ui.danger("Тропа петляет и упирается в бурелом. Выбираешься обратно, злой и замёрзший. −1 тепло.")
        ui.thought("Варвара ставит крестик углём. Углём, не ножом и не мелом.")
    ui.pause()


# --------------------------------------------------------------------- рычаги (рудник)

def lever_solution(start, toggles):
    """Кратчайшее решение; используется и генератором, и проверками сборки."""
    queue = deque([(tuple(start), ())])
    seen = {tuple(start)}
    while queue:
        lamps, path = queue.popleft()
        if all(lamps):
            return path
        for i, cells in enumerate(toggles):
            nxt = tuple(not value if j in cells else value for j, value in enumerate(lamps))
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, path + (i,)))
    return None


def lever_layout(rng, hard=False):
    # Независимая четвёртая связь ломает старую ловушку чётности трёх ламп.
    wiring = [(0, 1), (1, 2), (2, 3), (0, 2, 3)]
    labels = list(range(4))
    rng.shuffle(labels)
    toggles = [tuple(labels[c] for c in wire) for wire in wiring]
    rng.shuffle(toggles)
    distance = 3 if hard else 2
    candidates = []
    for bits in itertools.product((False, True), repeat=4):
        solution = lever_solution(bits, toggles)
        if solution is not None and len(solution) == distance:
            candidates.append(bits)
    return list(rng.choice(candidates)), toggles


def levers(st, rng, ns, hard):
    ui.header("Рычаги", "загадка")
    ui.narr("В боковом штреке щит с четырьмя лампами. Под ним шкафчик: «Все горят — открыто». "
            "На каждом рычаге ещё читаются номера проводов. Рычаг меняет состояние всех своих ламп: "
            "горевшая гаснет, тёмная загорается.")
    lamps, toggles = lever_layout(rng, hard)
    pulls = 0
    limit = 6 if hard else 5
    while pulls < limit:
        if pulls:
            ui.header("Рычаги", "загадка")
            ui.dim(f"Последнее действие: рычаг {k + 1}. Все четыре лампы должны гореть.")
        print()
        print("   Лампы:  " + "  ".join(paint(f"{i + 1} ●", C.YEL, C.B) if x else paint(f"{i + 1} ○", C.GRY)
                                          for i, x in enumerate(lamps)))
        for i, t in enumerate(toggles):
            print(paint(f"   Рычаг {i + 1}: лампы " + ", ".join(str(c + 1) for c in t), C.GRY))
        print(paint(f"   Осталось попыток: {limit - pulls}", C.GRY))
        k = ui.ask([(i, f"Дёрнуть рычаг {i + 1}") for i in range(4)] + [("leave", "Оставить шкафчик")])
        if k == "leave":
            break
        pulls += 1
        for t in toggles[k]:
            lamps[t] = not lamps[t]
        if all(lamps):
            ui.header("Рычаги", "шкафчик открыт")
            print("\n   Лампы:  " + "  ".join(paint(f"{i + 1} ●", C.YEL, C.B) for i in range(4)))
            ui.good("Щёлк. Дверца шкафчика отходит.")
            reward(st, rng, ns, hard)
            ui.pause()
            return
    ui.say("Контакты нагрелись, и щит отключился. Шкафчик остаётся закрытым. "
           "Проход рядом свободен — идти дальше он не мешает.", C.GRY)
    ui.pause()


# --------------------------------------------------------------------- тайник с кодом

OBJECTS = {
    "ВОРОНЫ": ["одна ворона", "две вороны", "три вороны", "четыре вороны", "пять ворон"],
    "ПНИ": ["один пень", "два пня", "три пня", "четыре пня", "пять пней"],
    "СОСНЫ": ["одна сосна", "две сосны", "три сосны", "четыре сосны", "пять сосен"],
    "ТАБЛИЧКИ": ["одна табличка", "две таблички", "три таблички", "четыре таблички", "пять табличек"],
    "ШИШКИ": ["одна шишка", "две шишки", "три шишки", "четыре шишки", "пять шишек"],
}


def cache(st, rng, ns, hard):
    ui.header("Тайник", "")
    if ns["looted"]:
        ui.narr("Ящик под ёлкой открыт. Внутри пусто, только снег. И твой отпечаток пальца на замке, в инее.")
        ui.pause()
        return
    keys = rng.sample(list(OBJECTS), 3)
    counts = [rng.randint(1, 5) for _ in keys]
    repeat = st.get("caches_opened", 0) > 0
    if repeat:
        counts[1] = rng.randint(1, 3)
        counts[0] = rng.randint(counts[1] + 1, 5)
        counts[2] = rng.randint(1, 5)
    parts = [OBJECTS[k][c - 1] for k, c in zip(keys, counts)]
    rng.shuffle(parts)
    ui.narr("Под ёлкой железный ящик, замок кодовый, на три цифры. На крышке гвоздём нацарапано: "
            + " · ".join(keys) + ".")
    ui.say("Оглядываешь поляну. " + ", ".join(parts).capitalize() + ".", C.WHT)
    ui.thought(rng.choice(["Кто-то загадал код по тому, что видно с этой поляны.",
                           "Тот, кто прятал ящик, явно сидел тут и считал.",
                           "Код где-то вокруг. Надо просто посмотреть."]))
    if repeat:
        ui.say("Под надписью мелкие буквы: «В первую цифру — сколько первого без второго. "
               "Во вторую — сколько второго. В третью — сколько третьего вместе со вторым».", C.GRY)
        # Первая величина больше второй, а сумма остаётся одной цифрой.
        # Повторный ящик требует сопоставить порядок и правило, не угадывать пароль.
        code = f"{counts[0] - counts[1]}{counts[1]}{counts[2] + counts[1]}"
    else:
        code = "".join(str(c) for c in counts)
    if hard and not repeat and "ВОРОНЫ" in keys:
        ui.say("Сверху, на ветке, сидит ещё одна ворона — её не сразу заметишь.", C.GRY)
        i = keys.index("ВОРОНЫ")
        counts[i] += 1
        code = "".join(str(c) for c in counts)
    for attempt in range(3):
        s = ui.raw_input("код> ").replace(" ", "")
        if s == code:
            ui.good("Замок щёлкает.")
            st["caches_opened"] = st.get("caches_opened", 0) + 1
            reward(st, rng, ns, hard)
            ui.pause()
            return
        if attempt == 1:
            ui.say("Сначала порядок на крышке, потом правило под ним." if repeat else
                   "Порядок цифр — как на крышке.", C.GRY)
        else:
            ui.say("Не подходит.", C.GRY)
    ui.say("Замок замерзает намертво. Ну и ладно. Наверняка там чьи-нибудь носки.", C.GRY)
    ns["looted"] = True
    ui.pause()
