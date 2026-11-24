"""ГОДОВЫЕ КОЛЬЦА — консольное приключение.

Запуск:   python main.py
Ключи:    --fast   без печати по буквам и анимаций
          --new    начать заново (стирает сохранение)
          --debug  меню перехода к любой сцене (для проверки финалов)
"""
import sys

from les import act1, act2, act3, art, state, threads, ui
from les import VERSION
from les.ui import C, paint

STAGES = {}
STAGES.update(act1.STAGES)
STAGES.update(act2.STAGES)
STAGES.update(act3.STAGES)

ACT3_LATE = {"a3_gate_check", "a3_free", "a3_empty_map", "a3_oak", "a3_rings", "end_good", "end_sad",
             "end_together"}

# пасхалки: слово -> ответы по очереди (последний повторяется)
EGGS = {
    ("дуб",): ["Зовёшь дуб. Дуб не отвечает. А ты чего хотел.",
              "Дуб всё ещё не отвечает. Но, кажется, слышит."],
    ("домой", "хочу домой"): ["Если бы всё было так просто.", "Все хотят. Никто не может. Пока что."],
    ("мама",): ["Мама далеко. Мама думает, что ты гуляешь. Ты и гуляешь, в общем-то."],
    ("inscryption", "инскрипшн"): ["Тут никто не попросит у тебя глаз. Только время. Ну и опята."],
    ("шишка",): ["Шишка сезонов одобрительно шуршит где-то за кадром."],
    ("кольца", "годовые кольца"): ["Раз кольцо, два кольцо... ты считаешь их, как овец. Не помогает."],
    ("пепел", "кот"): ["Где-то далеко кот Ефима поворачивает ухо в твою сторону."],
    ("42",): ["Не та книжка, но ответ засчитан."],
    ("recurse=false",): ["Не здесь. В файле. Но мысль правильная."],
    ("сохраниться", "сейв"): ["Игра и так всё сохраняет. Каждый шаг. Лес вообще ничего не забывает."],
    ("спать", "уснуть"): ["Спать в снегу нельзя. Это все знают. Даже лес это знает, просто молчит."],
    ("ау", "ау!"): ["Ау-у-у... Эхо отвечает через секунду. А через две отвечает ещё раз, чуть другим голосом."],
}

CUR = {"st": None}
START_ACT = 1


def fresh_state():
    st = state.State(state.new_state())
    if START_ACT == 2:
        st.update(name="Путник", stage="a2_start", loop=3)
        st["inv"].update({"фонарь": 1, "верёвка": 1, "камень": 3, "грибы": 2})
        st["memory"].update({"пень": "нож", "ручей": "верёвка", "ручей_камень": True, "ущелье": "фонарь"})
        for flag in ("helped", "heard_self", "threw_lantern", "stream_cleared", "asked_efim_road"):
            st.set(flag)
    return st


def use_act2_slot():
    """Отдельная видимая папка: обычное прохождение не перезаписывается."""
    base = state.BASE / "Тест-акта-2"
    base.mkdir(parents=True, exist_ok=True)
    state.BASE = base
    state.DATA = base / ".lesdata"
    state.SAVE = state.DATA / "state.json"
    state.ENDINGS = state.DATA / "endings.json"
    state.FAKE_SAVE = base / "save.txt"
    state.HINTS = base / "подсказки"
    act3.FAKE_SAVE = state.FAKE_SAVE
    act3.HINTS = state.HINTS


def show_inventory(st):
    inv = st["inv"]
    lines = [f"Тепло: {'♥' * st['warmth']}{'·' * (st['max_warmth'] - st['warmth'])}  ({st['warmth']}/{st['max_warmth']})"]
    for k, title in state.ITEM_NAMES.items():
        n = inv.get(k, 0)
        if k in ("фонарь", "нож"):
            lines.append(f"{title}: {'есть' if n else 'нет'}")
        elif k == "верёвка":
            lines.append(f"{title}: {n} шт.")
        else:
            lines.append(f"{title}: {n}")
    extra = {"чага": "Чага", "термос": "Термос Ефима", "канарейка": "Канарейка в клетке",
             "карандаш": "Карандаш «В.»", "письмо": "Письмо Веры", "кирка": "Кирка Петра"}
    for k, title in extra.items():
        if inv.get(k, 0):
            lines.append(title)
    lines += threads.thread_summary(st)
    ui.box(lines, f"Рюкзак — {st['name']}", C.YEL)


def show_journal(st):
    lines = []
    if st.has("act21") or st["stage"].startswith("a3"):
        lines.append("Саша: была у дуба, когда он растаял. Ищу её.")
    elif st["stage"].startswith("a2") or st["stage"] == "a1_exit":
        lines.append("Саша: Варвара видела её, ушла к дубу. Догнать.")
    else:
        if st["loop"] >= 2:
            lines.append("Саша: её следы пропали. Я хожу по кругу: пень, ручей, ущелье, дерево и снова пень. "
                         "Надо найти, где этот круг рвётся.")
        else:
            lines.append("Саша: убежала вперёд по тропе. Догнать у дуба.")
    if st["stage"].startswith(("a2", "a3")) or st["stage"] == "a1_exit":
        lines.append("Варвара: правильные тропы она метит крестиком углём (не ножом, не мелом).")
    if st.has("efim_story"):
        lines.append("Ефим: пришёл сюда с сыном Гришей сорок лет назад. Гриша ушёл к дубу. Ефим ждёт.")
    if st.n("чага") and not st.has("q_efim"):
        lines.append("Чага: Ефим её любит. Отдать ему.")
    if st.has("q_varvara") and st.has("pencil_returned") and not st.has("q_vera"):
        lines.append("Варвара просила найти на Пепелище табличку её сестры Веры.")
    if st.n("письмо"):
        lines.append("Письмо Веры: передать Ефиму, если Гриша уже ушёл или остался на гряде."
                     if st.has("boss_peace") or st.has("boss_fought") else
                     "Письмо Веры Грише: «Не стой там вечно. Иди домой». Найти Гришу.")
    if st.has("canary_cold"):
        lines.append("Канарейка мёрзнет. Её надо отогреть, и быстро.")
    if st.has("boss_peace"):
        lines.append("Гриша ушёл к отцу.")
    elif st.has("boss_fought"):
        lines.append("Сторож остался лежать на гряде.")
    if st.has("back_unlocked") and st["ritual"] < 5:
        lines.append("«Назад. Штольня. Пять раз.»")
    lines += threads.thread_summary(st)
    ui.box(lines, "Журнал", C.CYN)


def call_sasha(st):
    stage = st["stage"]
    ui.voice("Ты", "Саша-а-а!", C.CYN)
    if stage.startswith("a1") and st["loop"] == 1:
        ui.say("Издалека, впереди: «Догоня-а-ай!» И смех. Она где-то там, на тропе.", C.RED)
    elif stage.startswith("a1"):
        ui.say("Эхо возвращается через секунду. Твоим голосом. Саша не отвечает.", C.GRY)
        ui.thought("Утром она отзывалась. А теперь как будто её вообще нет в этом круге.")
    elif stage.startswith("a2") and not st.has("act21"):
        ui.say("Ветер. Где-то далеко, на самом краю слышимости, будто бы: «Я тут! Я у дуба!»", C.RED)
    elif stage.startswith("a2"):
        ui.say("Тишина. Даже ветер замолкает, как будто лес тоже прислушивается.", C.GRY)
    else:
        ui.say("Лес отвечает шелестом. В шелесте ты почти различаешь своё имя.", C.MAG)


def global_cmd(cmd):
    st = CUR["st"]
    if cmd in ("согреть птицу", "отогреть птицу", "согреть канарейку", "отогреть канарейку"):
        if CUR.get("item_busy"):
            ui.say("Сначала реши, как согреть её.", C.GRY)
        elif not st.has("canary_cold") or not st.n("канарейка"):
            ui.say("Некого отогревать: замерзающей птицы у тебя нет.", C.GRY)
        elif ui.IN_ENCOUNTER:
            ui.say("Сначала надо выбраться с тропы. Сейчас нельзя выпускать зверей из виду.", C.GRY)
        else:
            CUR["item_busy"] = True
            try:
                threads.canary_warm(st)
            finally:
                CUR["item_busy"] = False
            recover_after_scene(st)
            st.save()
        return True
    if cmd in ("съесть сахар", "сахар"):
        if ui.IN_ENCOUNTER:
            ui.say("Сначала выйди из боя. Руки заняты.", C.GRY)
        elif not st.n("сахар"):
            ui.say("В кармане нет сахара.", C.GRY)
        elif st["warmth"] >= st["max_warmth"]:
            ui.say("Ты уже согрелся. Оставишь сахар на потом.", C.GRY)
        else:
            st.take("сахар")
            before = st["warmth"]
            st.heal(2)
            ui.say(f"Сахар хрустит на зубах. (+{st['warmth'] - before} тепла)", C.YEL)
            st.save()
        return True
    if cmd in ("и", "инв", "инвентарь", "рюкзак"):
        show_inventory(st)
        return True
    if cmd in ("ж", "журнал"):
        show_journal(st)
        return True
    if cmd in ("помощь", "help", "?"):
        ui.box(["Вводи номер варианта и Enter.",
                "и — рюкзак и тепло;  ж — журнал;  выход — сохранить и выйти.",
                "Между боями: «съесть сахар», «согреть птицу».",
                "В сцене-тропе ход существ показан заранее: используй это.",
                "Иногда стоит попробовать ввести слово, которого нет в списке."], "Помощь", C.GRY)
        return True
    if cmd in ("саша", "саша!", "позвать сашу", "звать сашу", "крикнуть сашу", "искать сашу", "сашу"):
        call_sasha(st)
        return True
    for keys, replies in EGGS.items():
        if cmd in keys:
            n = st.setdefault("eggs", {}).get(keys[0], 0)
            st["eggs"][keys[0]] = n + 1
            ui.say(replies[min(n, len(replies) - 1)], C.MAG)
            return True
    if cmd in ("выход", "exit", "quit", "q"):
        st.save()
        ui.say("Сохранено. До встречи в лесу.", C.GRY)
        sys.exit(0)
    return False


def title_menu(st):
    ui.clear()
    art.show(art.TITLE, C.GRN)
    print(paint(f"     сборка {VERSION}", C.GRY))
    seen = state.endings_seen()
    if seen:
        reg = [e for e in seen if e != "Вместе"]
        extra = "  + секретный" if "Вместе" in seen else ""
        print(paint(f"     открыто финалов: {len(reg)}/2{extra}  ({', '.join(seen)})", C.GRY))
    if "Вместе" in seen:
        print(paint("     лес отпустил тебя. но ты можешь вернуться погулять.", C.GRN))
    elif "Табличка" in seen:
        print(paint("     у дуба теперь стоит табличка. с твоим именем.", C.YEL))
    print()
    if st and st["stage"] != "intro":
        new_label = "Заново со второго акта" if START_ACT == 2 else "Новая игра"
        k = ui.ask([("cont", f"Продолжить ({st['name']})"), ("new", new_label), ("quit", "Выйти")])
    else:
        k = ui.ask([("new", "Новая игра"), ("quit", "Выйти")])
    if k == "quit":
        sys.exit(0)
    if k == "new":
        state.reset()
        return fresh_state()
    return st


def check_fake_save(st):
    """Игрок поменял save.txt руками: реагируем в зависимости от того, где он."""
    r = state.read_recurse()
    stage = st["stage"]
    if r is not False or stage in ACT3_LATE:
        return
    if st.has("gate_reached"):
        ui.header("save.txt", "", C.MAG)
        ui.say("recurse=false. Но ты сейчас не у того пня.", C.MAG)
        k = ui.ask([("go", "Продолжить путь — дойти до пня через круг"),
                    ("jump", "Откатить сохранение к моменту у пня")])
        if k == "jump":
            st["stage"] = "a3_gate_check"
        else:
            st.set("recurse_off_early")
        return
    if stage.startswith("a3"):
        st.set("recurse_off_early")
        return
    ui.clear()
    ui.voice("Лес", "Рано. Ты ещё даже не знаешь, зачем это. Верну как было.", C.MAG)
    state.write_fake_save(True, "кто-то трогал этот файл")
    ui.pause()


def recover_after_scene(st):
    """Холод от загадок и событий тоже не оставляет живого героя с нулём тепла."""
    if st["warmth"] > 0:
        return
    if st.n("термос") and st.get("thermos_charges", 0) > 0:
        st["thermos_charges"] -= 1
        st["warmth"] = st["max_warmth"] // 2 + 1
        ui.say("Ты успеваешь открыть термос. Горячий чай возвращает чувствительность пальцам. "
               f"(тепло {st['warmth']}, глотков осталось {st['thermos_charges']})", C.YEL)
    else:
        st["warmth"] = max(2, st["max_warmth"] // 2)
        ui.say("Очнулся в сугробе у ствола. Прячешь руки под куртку и долго сидишь, пока "
               f"не перестаёт трясти. Дальше будешь осторожнее. (тепло {st['warmth']})", C.BLU)
    ui.pause()


def debug_menu(st):
    names = list(STAGES)
    for i, n in enumerate(names, 1):
        print(f"  {i:>2}) {n}")
    s = ui.raw_input("сцена (Enter — как есть)> ")
    if s in names or s.isdigit() and 1 <= int(s) <= len(names):
        st["stage"] = s if s in names else names[int(s) - 1]
        if st["stage"].startswith("a2") or st["stage"].startswith("a3"):
            st.setdefault("region", "birch")
            if st["region"] is None:
                st["region"] = "birch"
        if st["stage"].startswith("a3"):
            st["memory"].setdefault("ручей", "камень")
            st["memory"].setdefault("ущелье", "фонарь")


def main():
    global START_ACT
    args = sys.argv[1:]
    if "--version" in args:
        print(VERSION)
        return
    if "--fast" in args:
        ui.FAST = True
    START_ACT = 2 if "--act2" in args else 1
    if START_ACT == 2:
        use_act2_slot()
    if "--new" in args:
        state.reset()
    ui.GLOBAL_HANDLER = global_cmd
    if not state.FAKE_SAVE.exists():
        state.write_fake_save(True)

    st = state.load()
    if START_ACT == 2 and st is None:
        st = fresh_state()
        ui.say("Тест второго акта. Ты выбрался из ущелья и получил карту Варвары. Саша ушла к дубу.", C.CYN)
        st.save()
    elif "--quick" not in args:
        st = title_menu(st)
    if st is None:
        st = fresh_state()
    CUR["st"] = st
    if "--debug" in args:
        debug_menu(st)
    check_fake_save(st)

    while True:
        stage = st["stage"]
        fn = STAGES.get(stage)
        if fn is None:
            ui.say(f"Неизвестная сцена {stage!r}. Начинаем сначала.", C.RED)
            st["stage"] = "intro"
            continue
        nxt = fn(st)
        if nxt == "__reset__":
            state.reset()
            st = fresh_state()
            CUR["st"] = st
            continue
        st["stage"] = nxt
        recover_after_scene(st)
        st.save()


class _AgentOut:
    """Вывод для тестировщика: без ANSI-цветов, сразу в файл."""
    def __init__(self, path):
        import re
        self.f = open(path, "a", encoding="utf-8")
        self.re = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

    def write(self, s):
        self.f.write(self.re.sub("", s))
        self.f.flush()

    def flush(self):
        self.f.flush()


def run():
    if "--minigames" in sys.argv:
        import minigames
        sys.argv.remove("--minigames")
        minigames.cli()
        return
    if not ui.AGENT_DIR:
        try:
            main()
        except KeyboardInterrupt:
            print()
            if CUR["st"]:
                CUR["st"].save()
            sys.exit(0)
        return
    from pathlib import Path
    d = Path(ui.AGENT_DIR)
    sys.stdout = _AgentOut(d / "out.txt")
    ui.FAST = True
    code = 0
    try:
        main()
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 0
    except Exception:
        import traceback
        traceback.print_exc(file=sys.stdout)
        code = 99
    sys.stdout.flush()
    (d / "status.txt").write_text(str(code), encoding="utf-8")
    sys.exit(code)


if __name__ == "__main__":
    run()
