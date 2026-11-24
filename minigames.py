"""Отдельная площадка для оценки настоящих игровых сцен."""
import argparse
import random
from datetime import datetime
from pathlib import Path

import main
from les import VERSION, act3, encounter, puzzles, state, ui
from les.ui import C

GAMES = [
    ("levers", "Рычаги и четыре лампы"),
    ("tracks", "Следы на снегу"),
    ("signs", "Метки на деревьях"),
    ("echo", "Эхо: запомнить ритм"),
    ("cache", "Кодовый тайник"),
    ("shoroh", "Бой: Шорох"),
    ("mixed", "Бой: Шорох и Теплоед"),
    ("rings", "Финальные кольца — содержит спойлеры"),
]
REVIEWS = state.BASE / "Отзывы-миниигр.txt"


class ReturnToMenu(Exception):
    pass


class PracticeState(state.State):
    def save(self):
        pass  # Пробные попытки живут только в памяти.


def fresh_state(seed):
    st = PracticeState(state.new_state())
    st.update(name="Путник", stage="a2_map", loop=3, seed=seed)
    st["inv"].update({"камень": 4, "верёвка": 2, "грибы": 2})
    st["memory"].update({"пень": "нож", "ручей": "верёвка", "ручей_камень": True,
                         "ущелье": "фонарь"})
    return st


def play_game(kind, seed, hard):
    st = fresh_state(seed)
    main.CUR["st"] = st
    rng = random.Random(seed)
    if hard:
        st["caches_opened"] = 1
    if kind == "signs":
        ui.say("Перед развилкой Варвара сказала: «Мои метки — крестик углём. Остальным не верь».", C.CYN)
    if kind in {"levers", "tracks", "signs", "echo", "cache"}:
        ns = {"looted": False}
        getattr(puzzles, kind)(st, rng, ns, hard)
        ui.say("Попытка закончена. Тепло: " + str(st["warmth"]) + "/6.", C.CYN)
    elif kind in {"shoroh", "mixed"}:
        creatures = [("шорох", 4, True)]
        if kind == "mixed":
            creatures.append(("теплоед", 7, True))
        # Одна попытка: поражение возвращает в меню повтора, без сюжетного цикла.
        fight = encounter.Encounter(st, "Пробная тропа", 10, creatures,
                                    bushes=(2, 4, 7), items=(3, 6), hard=hard,
                                    intro="Дойди до конца тропы. Камни отвлекают Шороха, свет притягивает Теплоеда.")
        ui.IN_ENCOUNTER = True
        try:
            result = fight.run()
        finally:
            ui.IN_ENCOUNTER = False
        ui.say("Тропа пройдена." if result["win"] else "Не получилось. Можно повторить с теми же вещами.", C.CYN)
    else:
        ui.box(["Это отдельная проба финала. В этой попытке:",
                "у пня оставлен нож; ручей пройден с верёвкой и камнем;",
                "в ущелье помог фонарь; в штольне — камень; на пепелище — голос.",
                "Сюжетные финалы за эту пробу не открываются."], "Перед кольцами", C.GRY)
        ui.pause()
        outcome = act3.a3_rings(st, rng=rng)
        ui.say("Кольца освобождены." if outcome == "end_good" else "Кольца удержали тебя. Можно повторить.", C.CYN)


def save_review(kind, seed, hard):
    score = ui.raw_input("Оценка от 1 до 10 (Enter — отменить): ").strip()
    if not score or score.lower() == "меню":
        return
    while score not in {str(n) for n in range(1, 11)}:
        score = ui.raw_input("Нужна цифра от 1 до 10, либо Enter для отмены: ").strip()
        if not score or score.lower() == "меню":
            return
    comment = ui.raw_input("Что понравилось или мешало? ").strip()
    if comment.lower() == "меню":
        return
    line = (f"{datetime.now():%Y-%m-%d %H:%M} | {dict(GAMES)[kind]} | "
            f"сид {seed} | {'повторный' if hard else 'первый'} проход | {score}/10 | {comment}\n")
    try:
        with REVIEWS.open("a", encoding="utf-8") as file:
            file.write(line)
        ui.say("Записано в «Отзывы-миниигр.txt».", C.GRN)
    except OSError as error:
        ui.say(f"Не удалось записать отзыв: {error}. Оценка: {score}/10. {comment}", C.RED)


def run(seed=None):
    hard = False
    old_handler, old_state = ui.GLOBAL_HANDLER, main.CUR["st"]
    old_input, old_fast = ui.raw_input, ui.FAST
    in_scene = False

    def practice_input(prompt="> "):
        text = old_input(prompt)
        if in_scene and text.strip().lower() == "меню":
            raise ReturnToMenu()
        if text.strip().lower() in {"выход", "exit", "quit", "q"}:
            raise SystemExit(0)
        return text

    ui.GLOBAL_HANDLER = main.global_cmd
    ui.raw_input = practice_input
    main.CUR["st"] = fresh_state(seed or 1)
    ui.FAST = True
    try:
        while True:
            ui.header("Миниигры", f"версия {VERSION} · {'повторный проход' if hard else 'первый проход'}")
            ui.dim("Выбери любую сцену. Вещи и тепло обновляются при каждой попытке.")
            ui.dim("В ответе можно написать «меню» для возврата или «выход» для закрытия.")
            choice = ui.ask(GAMES + [("difficulty", "Сменить первый / повторный проход"), ("exit", "Закрыть")],
                            hidden={"меню": "root"})
            if choice == "root":
                continue
            if choice == "exit":
                return
            if choice == "difficulty":
                hard = not hard
                continue
            variant = seed if seed is not None else random.randrange(1, 10**9)
            while True:
                ui.say(f"Вариант: {variant}. {'Повторный' if hard else 'Первый'} проход.", C.CYN)
                try:
                    in_scene = True
                    play_game(choice, variant, hard)
                except ReturnToMenu:
                    break
                finally:
                    in_scene = False
                while True:
                    action = ui.ask([("repeat", "Повторить этот вариант"), ("new", "Другой вариант"),
                                     ("rate", "Оценить и записать отзыв"), ("menu", "К списку миниигр")],
                                    hidden={"меню": "menu"})
                    if action != "rate":
                        break
                    save_review(choice, variant, hard)
                if action == "menu":
                    break
                if action == "new":
                    variant += 1
    finally:
        ui.GLOBAL_HANDLER, main.CUR["st"] = old_handler, old_state
        ui.raw_input, ui.FAST = old_input, old_fast
        ui.IN_ENCOUNTER = False


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, help="номер воспроизводимого варианта")
    args = parser.parse_args()
    try:
        run(args.seed)
    except (EOFError, KeyboardInterrupt, ReturnToMenu):
        print("\nПроба закрыта.")


if __name__ == "__main__":
    cli()
