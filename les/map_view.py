"""Компактная карта: одинаковые карточки и непрерывные линии слева направо."""
from .ui import C, paint

WIDTH = 77
HEIGHT = 17
CENTERS = (16, 39, 62)
LANES = (2, 8, 14)
HALF = 6


def route_rows(layers, exit_node, describe, current, available, visited):
    cells = [[" "] * WIDTH for _ in range(HEIGHT)]
    colors = [[C.GRY] * WIDTH for _ in range(HEIGHT)]
    links = {}

    def put(x, y, text, color=C.GRY):
        for i, ch in enumerate(text):
            if 0 <= x + i < WIDTH and 0 <= y < HEIGHT:
                cells[y][x + i] = ch
                colors[y][x + i] = color

    def edge_color(source, destination):
        if source == current and destination in available:
            return C.YEL + C.B
        if source in visited and (destination in visited or destination == current):
            return C.GRN
        return C.GRY

    def wire(x1, y1, x2, y2, color):
        # Шагаем по соседним клеткам и собираем стыки: линии непрерывны,
        # а у общего начала или конца получается развилка, а не крестик.
        distance = x2 - x1
        x, y = x1, y1
        path = [(x, y)]
        for nx in range(x1 + 1, x2 + 1):
            path.append((nx, y))
            target_y = round(y1 + (y2 - y1) * (nx - x1) / max(1, distance))
            while y != target_y:
                y += 1 if target_y > y else -1
                path.append((nx, y))
        for a, b in zip(path, path[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            for point, direction in ((a, (dx, dy)), (b, (-dx, -dy))):
                links.setdefault(point, set()).add(direction)
                px, py = point
                if colors[py][px] == C.GRY or color == C.YEL + C.B:
                    colors[py][px] = color
        links.setdefault(path[0], set()).add((-1, 0))
        links.setdefault(path[-1], set()).add((1, 0))

    # Соединения между участками, до карточек: рамки остаются ровными.
    for level, row in enumerate(layers[:-1]):
        next_row = {node["col"]: node for node in layers[level + 1]}
        for node in row:
            for column in node.get("up", []):
                target = next_row.get(column)
                if target:
                    wire(CENTERS[level] + HALF + 1, LANES[node["col"]],
                         CENTERS[level + 1] - HALF - 1, LANES[column],
                         edge_color(node["id"], target["id"]))

    glyphs = {frozenset(dirs): glyph for dirs, glyph in [
        (((-1, 0), (1, 0)), "─"), (((0, -1), (0, 1)), "│"),
        (((1, 0), (0, 1)), "╭"), (((-1, 0), (0, 1)), "╮"),
        (((1, 0), (0, -1)), "╰"), (((-1, 0), (0, -1)), "╯"),
        (((-1, 0), (1, 0), (0, 1)), "┬"),
        (((-1, 0), (1, 0), (0, -1)), "┴"),
        (((0, -1), (0, 1), (1, 0)), "├"),
        (((0, -1), (0, 1), (-1, 0)), "┤"),
    ]}
    for (x, y), directions in links.items():
        cells[y][x] = glyphs.get(frozenset(directions), "┼")

    # Вход и выход — общий ствол. Здесь соединение линий намеренное.
    ys = [LANES[n["col"]] for n in layers[0]] + [8]
    for y in range(min(ys), max(ys) + 1):
        put(7, y, "│")
    put(4, 8, "───")
    for node in layers[0]:
        color = C.YEL + C.B if current is None and node["id"] in available else C.GRY
        put(7, LANES[node["col"]], "├──", color)
    if min(ys) < max(ys):
        put(7, min(ys), "╭", colors[min(ys)][7])
        put(7, max(ys), "╰", colors[max(ys)][7])
    ys = [LANES[n["col"]] for n in layers[2]] + [8]
    for y in range(min(ys), max(ys) + 1):
        put(70, y, "│")
    for node in layers[2]:
        put(69, LANES[node["col"]], "─┤", edge_color(node["id"], exit_node["id"]))
    if min(ys) < max(ys):
        put(70, min(ys), "╮", colors[min(ys)][70])
        put(70, max(ys), "╯", colors[max(ys)][70])
    put(70, 8, "┼")
    put(0, 8, "● ВХОД" if current is None else "ВХОД", C.GRN + C.B if current is None else C.GRY)
    exit_label = f"{available[exit_node['id']]} ВЫХОД" if exit_node["id"] in available else "ВЫХОД"
    put(WIDTH - len(exit_label), 8, exit_label,
        C.YEL + C.B if exit_node["id"] in available else C.GRN)

    for level, row in enumerate(layers):
        for node in row:
            word, color = describe(node, level)
            nid = node["id"]
            if nid == current:
                title, color = "● ТЫ ЗДЕСЬ", C.GRN + C.B
            elif nid in available:
                title, color = f"{available[nid]} {word.upper()}", C.YEL + C.B
            elif nid in visited:
                title, color = "✓ " + word.upper(), C.GRY
            else:
                title = word.upper()
            title = title[:11].center(11)
            x, y = CENTERS[level] - HALF, LANES[node["col"]]
            put(x, y - 1, "╭───────────╮", color)
            put(x, y, "│" + title + "│", color)
            put(x, y + 1, "╰───────────╯", color)

    rows = []
    for chars, styles in zip(cells, colors):
        last = max((i for i, ch in enumerate(chars) if ch != " "), default=-1)
        out = []
        start = 0
        while start <= last:
            end = start + 1
            while end <= last and styles[end] == styles[start]:
                end += 1
            out.append(paint("".join(chars[start:end]), styles[start]))
            start = end
        rows.append("".join(out))
    return rows
