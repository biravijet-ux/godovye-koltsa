"""Нити — связанные события акта 2.

Событий не много, но они нужны друг другу: то, что получил в одной нити,
открывает шаг в другой, мирный проход мимо Сторожа или помогает в финале.

  ЧАГА ──► ЕФИМ ──► термос ──┬──► отогреть КАНАРЕЙКУ ──► ПЁТР ──► кирка
                             └──► Сторож (мирно)
  КАРАНДАШ ──┬──► ВАРВАРА (отдать) ──► карта ──► ВЕРА ──► письмо ──► Сторож (мирно)
             └──► оставить себе ──► ИМЕНА на табличках ──► финал (вторая попытка)
  ЩЕНОК (спасти / бросить) ──► МАТЬ (подарок / засада) ──► в 2.1 уводит зверей

Шаг привязывается к точке карты при первом заходе. В 2.1 на той же точке —
отголосок, а на новых точках можно доделать то, что пропустил.
"""
from . import encounter, ui
from .ui import C


def done(st, sid):
    return st.has("q_" + sid)


def finish(st, sid):
    st.set("q_" + sid)


# ============================================================ ЧАГА / ЕФИМ

def chaga(st):
    ui.narr("Старая кривая берёза. На ней чага, чёрная, как будто кто-то кусок угля прилепил. "
            "Ефим говорил что любит чай с чагой. Или это не он говорил... да нет, он.")
    k = ui.ask([("take", "Срезать чагу ножом"), ("leave", "Не трогать")])
    if k == "take":
        st.add("чага")
        finish(st, "chaga")
        ui.say("Чага твёрдая, как дерево. Режешь долго, лезвие скрежещет. Но срезал. (+чага)", C.YEL)
    else:
        ui.say("Ну и ладно, пусть растёт.", C.GRY)


def chaga_echo(st):
    ui.narr("Та же берёза. На месте чаги срез, твой, кривоватый. Ничего не отросло. Тут вообще ничего не отрастает, кроме опят.")


def efim_give(st, place="trader"):
    if place == "event":
        ui.narr("По тропе тащит санки Ефим. Пыхтит, ругается на санки. Увидел тебя, остановился.")
    ui.voice("Ефим", "О-о. Это у тебя что, чага? Дай-ка... Да, она самая. Сто лет такой не видел.")
    k = ui.ask([("give", "Отдать чагу Ефиму"), ("keep", "Оставить себе")])
    if k != "give":
        ui.voice("Ефим", "Ну смотри. Мне не жалко, тебе не жалко.")
        return
    st.take("чага")
    st.add("термос")
    st["thermos_charges"] = 2
    finish(st, "efim")
    ui.voice("Ефим", "На вот. Термос. Там чай, горячий, не спрашивай, как он столько держит.")
    ui.voice("Ефим", "Это Гришкин термос был. Сын. Ушёл к дубу прошлой зимой, сказал вернётся к обеду.")
    ui.say("Ефим снимает с санок пустой котелок. Долго водит ложкой по дну, потом замечает и убирает её.", C.GRY)
    ui.say("(+термос: два раза спасёт, когда совсем замёрзнешь)", C.YEL)


def efim_echo(st):
    ui.narr("Санный след. Свежий, хотя Ефима ты встречал... когда? Час назад? Круг назад?")


# ============================================================ КАНАРЕЙКА / ПЁТР

def canary(st):
    ui.narr("На гвозде у входа в штрек висит клетка. В ней жёлтая птичка, совсем маленькая, "
            "нахохлилась и не шевелится почти. Ещё живая, клюв открывает.")
    ui.say("Шахтёры раньше таких под землю брали, если птичка замолчит, значит газ, беги.", C.GRY)
    k = ui.ask([("take", "Взять клетку с собой"), ("leave", "Оставить")])
    if k == "take":
        st.add("канарейка")
        st.set("canary_cold")
        finish(st, "canary")
        ui.say("Клетка лёгкая совсем. Птичка ледяная. Её бы отогреть, и побыстрее.", C.YEL)
    else:
        ui.say("Ты уходишь. Сзади тихо-тихо пищит.", C.GRY)


def canary_echo(st):
    if st.has("canary_alive"):
        ui.narr("Пустой гвоздь. Птичка у тебя за пазухой начинает петь, узнала место.")
    else:
        ui.narr("Пустой гвоздь. Ты стараешься на него не смотреть.")


def canary_warm(st):
    ui.narr("Птичка в клетке совсем перестала двигаться. Глаза закрыты. Если сейчас не отогреть, всё.")
    opts = []
    if st.n("термос") and st.get("thermos_charges", 0) > 0:
        opts.append(("thermos", "Капнуть ей Ефимова чаю в поилку и укутать (−1 заряд термоса)"))
    opts.append(("body", "Сунуть клетку за пазуху, к себе (−3 тепла)"))
    opts.append(("let", "Ничего не делать"))
    k = ui.ask(opts)
    st.unset("canary_cold")
    finish(st, "canary_warm")
    if k == "let":
        st.take("канарейка")
        st.set("canary_dead")
        ui.say("Ты ждёшь. Она так и не открывает глаза. Ты оставляешь клетку на пне и идёшь дальше, "
               "быстро, чтобы не думать.", C.GRY)
        return
    if k == "thermos":
        st["thermos_charges"] -= 1
    else:
        st.hurt(3)
        ui.say("Холодная клетка прямо к животу. Бр-р-р.", C.BLU)
    st.set("canary_alive")
    ui.say("Через минуту за пазухой кто-то возится. Потом тихонько: пи. Потом ещё: пи-пи-пиии.", C.YEL)
    ui.say("(канарейка жива: в темноте она чирикает, когда зверь рядом, и ты видишь всех)", C.YEL)


def canary_warm_echo(st):
    ui.narr("Тут ты отогревал птицу. На снегу ещё вмятина, где ты сидел.")


def warm_at_fire(st):
    """Обычный костёр помогает птице без оплаты и отдельной сюжетной точки."""
    if not st.has("canary_cold") or not st.n("канарейка"):
        return False
    st.unset("canary_cold")
    st.set("canary_alive")
    finish(st, "canary_warm")
    ui.say("Ставишь клетку рядом с огнём, прикрыв от ветра курткой. Сначала тихий писк, "
           "потом птичка прыгает на жёрдочку. Теперь можно идти.", C.YEL)
    return True


def miner(st):
    ui.narr("Среди табличек одна стоит отдельно, под сосной. «Здесь стоит дерево. Раньше это был "
            "Пётр Савельич, крепильщик». Внизу, у корней, лежит старая кирка.")
    ui.say("Канарейка за пазухой вдруг рвётся, бьётся, поёт так громко, как никогда. Узнала.", C.YEL)
    k = ui.ask([("give", "Поставить клетку у таблички и открыть дверцу"),
                ("keep", "Нет, птица нужна мне самому")])
    finish(st, "miner")
    if k == "give":
        st.take("канарейка")
        st.unset("canary_alive")
        st.set("canary_home")
        st.add("кирка")
        ui.say("Птичка вылетает и садится на нижнюю ветку. И сразу замолкает, но как-то спокойно. "
               "Кирка у корней теперь лежит так, будто её тебе подвинули.", C.GRY)
        ui.say("(+кирка: полынью можно перейти по льду: бьёшь киркой у края, лёд встаёт плитой, и по ней проходишь сухим)", C.YEL)
    else:
        st.set("kept_canary")
        ui.say("Ты застёгиваешь куртку. Птица долго не успокаивается.", C.GRY)


def miner_echo(st):
    if st.has("canary_home"):
        ui.narr("На ветке над табличкой Петра сидит жёлтая птичка. Не поёт. Просто сидит, смотрит.")
    else:
        ui.narr("Табличка Петра. Кирка у корней. Птица у тебя за пазухой отворачивается.")


# ============================================================ КАРАНДАШ / ВАРВАРА / ВЕРА

def pencil(st):
    ui.narr("В снегу что-то торчит. Карандаш, химический, сточенный почти до конца. "
            "На боку нацарапано «В.»")
    ui.thought("Варвара? Она же рисует карты.")
    st.add("карандаш")
    finish(st, "pencil")
    ui.say("(+карандаш)", C.YEL)


def pencil_echo(st):
    ui.narr("Ямка в снегу, где лежал карандаш. Её почему-то не замело.")


def varvara(st):
    ui.narr("На кочке посреди тумана сидит Варвара и рисует. Пальцем, по грязи, прямо на коленке.")
    ui.voice("Варвара", "А, ты. Представляешь, карандаш потеряла. Последний. Теперь вот так, как дура.")
    k = ui.ask([("give", "Отдать ей карандаш"), ("keep", "Промолчать, карандаш пригодится самому")])
    finish(st, "varvara")
    if k == "give":
        st.take("карандаш")
        st.set("varvara_map")
        st.set("pencil_returned")
        ui.voice("Варвара", "Ты ж мой хороший. Давай карту.")
        ui.say("Она быстро-быстро черкает у тебя на карте. Значки, стрелки, крестики.", C.GRY)
        ui.voice("Варвара", "Вот, дальше всё отмечено, что где. И ещё. Будешь на Пепелище, посмотри "
                 "там Веру, сестру мою. Она туда ушла и... ну, ты понял.")
        ui.say("(дальше на карте видно содержимое всех точек)", C.YEL)
    else:
        st.set("pencil_kept")
        ui.say("Ты киваешь, сочувствуешь. Карандаш в кармане жжёт как уголёк.", C.GRY)
        ui.thought("Мне он нужнее. Наверное.")


def varvara_echo(st):
    if st.has("pencil_returned"):
        ui.narr("Варвара на той же кочке. Смотрит на тебя, щурится.")
        ui.voice("Варвара", "Мы знакомы? Странно... У меня такое чувство, что ты мне уже отдавал карандаш.")
    else:
        ui.narr("Варвара на той же кочке, рисует пальцем по грязи. Тебя не замечает. Или делает вид.")


def vera(st):
    ui.narr("Ты ищешь среди табличек. «...раньше это была Вера». Под ней снег как будто рыхлее.")
    k = ui.ask([("dig", "Разгрести снег"), ("leave", "Не трогать")])
    if k != "dig":
        return
    finish(st, "vera")
    st.add("письмо")
    ui.say("Под снегом жестяная коробочка из-под леденцов. Внутри записка:", C.GRY)
    ui.type_out("     «Гриша, я не дошла. Не стой там вечно, слышишь? Иди домой. В.»", C.WHT, delay=0.03)
    ui.thought("Гриша. Ефим говорил про Гришу. Сын его.")
    ui.say("(+письмо Веры)", C.YEL)


def vera_echo(st):
    ui.narr("Табличка Веры. Снег под ней раскопан, твоими руками. Коробочка пустая.")


# ============================================================ ИМЕНА

NAME_PLAQUES = {
    "names_birch": ("Соня и Лёва", "Две таблички на одной берёзе, рядом, чуть внахлёст."),
    "names_mine": ("Пашка Рыжий", "Табличка прибита прямо к крепи, криво, наспех."),
    "names_ash": ("Андрей Палыч", "Табличка закопчённая, буквы кто-то процарапал ногтем."),
    "names_ridge": ("тётя Нина", "Табличка на камне, примотана проволокой. Видно, что её много раз поправляли."),
}


def make_names(sid):
    name, look = NAME_PLAQUES[sid]

    def run(st):
        ui.narr(look)
        ui.say(f"«Здесь стоит дерево. Раньше это был человек: {name}».", C.WHT)
        if st.n("карандаш"):
            k = ui.ask([("copy", "Переписать имя на край карты"), ("leave", "Просто прочитать")])
            if k == "copy":
                st.setdefault("names", []).append(name)
                finish(st, sid)
                ui.say("Ты переписываешь. Зачем — сам не знаешь. Просто кажется, что если записать, "
                       "то человек как будто не совсем пропал.", C.YEL)
                ui.say(f"(имён записано: {len(st['names'])})", C.YEL)
                return
        if st.has("pencil_returned"):
            finish(st, sid)
        ui.thought("Надо бы запомнить. Не запомню ведь.")

    def echo(st):
        if name in st.get("names", []):
            ui.narr(f"Табличка «{name}». На ней чуть-чуть грифеля, ты прислонял карту.")
        else:
            ui.narr(f"Табличка «{name}». Ты помнишь, что читал её. Имя уже вылетело из головы.")
    return run, echo


# ============================================================ ЩЕНОК / МАТЬ

def cub(st):
    ui.narr("Скулит кто-то. В старом капкане лапой застрял маленький шорох, щенок совсем. "
            "Слепой, как все они, мордой крутит на твои шаги.")
    k = ui.ask([("free", "Разжать капкан (он может цапнуть)"), ("leave", "Обойти стороной")])
    finish(st, "cub")
    if k == "free":
        st.hurt(1)
        st.set("cub_freed")
        ui.say("Цапнул, конечно. Через варежку, но больно. (−1 тепло) Щенок хромает в кусты, "
               "оглядывается. Как будто запоминает, как ты пахнешь.", C.YEL)
    else:
        st.set("cub_left")
        ui.say("Ты обходишь. Скулёж долго слышно за спиной.", C.GRY)


def cub_echo(st):
    if st.has("cub_freed"):
        ui.narr("Пустой капкан, ржавый. Рядом следы маленьких лап, свежие. Он сюда приходит.")
    else:
        ui.narr("Капкан. В нём ничего уже нет, только клок серой шерсти. Ты отводишь глаза.")


def mother(st):
    finish(st, "mother")
    if st.has("cub_freed"):
        ui.narr("Поперёк тропы стоит шорох. Огромный, втрое больше обычных. Нюхает воздух. "
                "Из-за её лапы выглядывает тот самый щенок, хромой.")
        ui.say("Она подходит вплотную, обнюхивает твою прокушенную варежку. Фыркает. "
               "И кладёт на снег клок своей шерсти, густой, тёплой.", C.YEL)
        st["max_warmth"] += 1
        st.heal(2)
        ui.say("(Шерсть в варежки: максимум тепла +1. Позже щенок ещё отплатит: в бою уведёт за собой одного зверя)", C.YEL)
    else:
        ui.narr("Тихо. Слишком тихо. А потом из кустов, со всех сторон сразу: шорох, шорох, шорох.")
        ui.danger("Мать. Она нашла капкан. И нашла тебя по запаху.")
        ui.pause()
        encounter.play(st, "Мать", 8, [("шорох", 4), ("шорох", 6)], bushes=[2, 5], hard=True,
                       place="она пришла за тобой")


def mother_echo(st):
    if st.has("cub_freed"):
        ui.narr("Следы большой лапы и маленькой уходят в ельник. Совсем рядом. И почему-то совсем не страшно.")
    else:
        ui.narr("Снег взрыт. Ты помнишь, что тут было, и не хочешь помнить.")


# ============================================================ список шагов

_names = {sid: make_names(sid) for sid in NAME_PLAQUES}

STEPS = [
    # id, области, условие, шаг, отголосок
    ("chaga", {"birch", "mine"}, lambda st: True, chaga, chaga_echo),
    ("pencil", {"birch", "mine"}, lambda st: True, pencil, pencil_echo),
    ("cub", {"birch", "mine"}, lambda st: True, cub, cub_echo),
    ("canary", {"mine"}, lambda st: True, canary, canary_echo),
    ("efim", {"mine", "bog", "spruce", "ash"}, lambda st: st.n("чага") > 0,
     lambda st: efim_give(st, "event"), efim_echo),
    ("canary_warm", {"mine", "bog", "spruce", "ash", "ridge"}, lambda st: st.has("canary_cold"),
     canary_warm, canary_warm_echo),
    ("varvara", {"bog", "spruce", "ash"}, lambda st: st.n("карандаш") > 0 and not st.has("q_varvara"),
     varvara, varvara_echo),
    ("mother", {"bog", "spruce", "ash"}, lambda st: done(st, "cub"), mother, mother_echo),
    ("miner", {"ash"}, lambda st: st.has("canary_alive"), miner, miner_echo),
    ("vera", {"ash"}, lambda st: st.has("pencil_returned"), vera, vera_echo),
    ("names_birch", {"birch"}, lambda st: True, *_names["names_birch"]),
    ("names_mine", {"mine"}, lambda st: True, *_names["names_mine"]),
    ("names_ash", {"ash"}, lambda st: True, *_names["names_ash"]),
    ("names_ridge", {"ridge"}, lambda st: True, *_names["names_ridge"]),
]
BY_ID = {s[0]: s for s in STEPS}

# шаги, ведущие куда-то дальше, важнее табличек
PRIORITY = ["canary_warm", "efim", "varvara", "vera", "miner", "mother", "canary", "chaga", "pencil", "cub"]


def pick(st, rid, taken):
    order = sorted(STEPS, key=lambda s: PRIORITY.index(s[0]) if s[0] in PRIORITY else 99)
    for sid, regions, cond, _, _ in order:
        if rid in regions and not done(st, sid) and sid not in taken and cond(st):
            return sid
    return None


def run_node(st, rid, ns, title):
    """Запускает нить на точке-событии. False — нитей тут нет, нужно обычное событие."""
    p21 = st.has("act21")
    sid = ns.get("ev")
    taken = {n.get("ev") for n in st["nodes"].values() if n.get("ev") and not done(st, n.get("ev"))}
    if sid and sid in BY_ID:
        _, _, cond, step, echo = BY_ID[sid]
        ui.header(title, "")
        if done(st, sid):
            echo(st)
            # на старой точке может ждать следующий шаг другой нити
            nxt = pick(st, rid, taken)
            if p21 and nxt and not ns.get("ev2"):
                ns["ev2"] = nxt
                ui.pause()
                ui.header(title, "")
                BY_ID[nxt][3](st)
        elif cond(st):
            step(st)
        else:
            echo(st)
        ui.pause()
        return True
    taken.discard(None)
    sid = pick(st, rid, taken)
    if not sid:
        return False
    ns["ev"] = sid
    ui.header(title, "")
    BY_ID[sid][3](st)
    ui.pause()
    return True


def thread_summary(st):
    """Для «и»: что ты сейчас несёшь по нитям."""
    out = []
    if st.has("canary_alive"):
        out.append("Канарейка за пазухой, живая.")
    elif st.has("canary_cold"):
        out.append("Канарейка мёрзнет. Её надо отогреть.")
    if st.n("термос"):
        out.append(f"Термос Ефима (зарядов: {st.get('thermos_charges', 0)}).")
    if st.get("names"):
        out.append("Записанные имена: " + ", ".join(st["names"]) + ".")
    if st.has("cub_freed"):
        out.append("Где-то рядом ходит хромой щенок шороха.")
    return out
