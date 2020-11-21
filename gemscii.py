# * % . % . # . . . . # *
# * * % % . . % . # * # *
# # # * . * * . . X % X X
# . X . # * * % # . X # #
# . . X X . # # % X X # .
# % . % % X * % X # * % #
# * X . % # * * # X . X X
import random
from typing import Tuple, List

import tcod

gems = "ABCDE"
MATRIX_WIDTH = 10
MATRIX_HEIGHT = 6


def valid_x(x):
    return 0 <= x < MATRIX_WIDTH


def valid_y(y):
    return 0 <= y < MATRIX_HEIGHT


def new_gem():
    return random.choice(gems)


def init_matrix():
    return [[random.choice(gems) for _ in range(MATRIX_HEIGHT)] for _ in range(MATRIX_WIDTH)]


def meta_matrix():
    return {i: {j: {} for j in range(MATRIX_HEIGHT)} for i in range(MATRIX_WIDTH)}


def elt(m, x, y):
    if valid_x(x) and valid_y(y):
        return m[x][y]
    return None


def display(c="|", i=-1, j=-1):
    if i < 0 or j < 0:
        print("", end="\n")
    elif len(c) == 1:
        print("{:5s}".format(c), end="")
    else:
        print("{:5s}".format(c), end="")


# def print_matrix(m):
#     new_line = lambda: display()
#     for j in range(MATRIX_HEIGHT):
#         new_line()
#         new_line()
#         for i in range(MATRIX_WIDTH):
#             display(c=elt(m, i, j), i=i, j=j)
#     new_line()


# def print_meta(m, meta, streaks):
#     assert False, "UNIMPLEMENTED"


def matrix_streaks(m: List) -> List:
    streaks = set()
    deltas = [(i, j) for i in range(-1, 2) for j in range(-1, 2) if i != 0 or j != 0]
    cells = [(i, j) for j in range(MATRIX_HEIGHT) for i in range(MATRIX_WIDTH)]
    for cell in cells:
        for delta in deltas:
            wins = 0
            cx, cy = cell
            dx, dy = delta
            ax, ay = delta
            cell_type = elt(m, cx, cy)
            streak = {tuple([cell_type, cx, cy])}
            while cell_type and valid_x(cx + ax) and valid_y(cy + ay) and cell_type == elt(m, cx + ax, cy + ay):
                streak.add(tuple([cell_type, cx + ax, cy + ay]))
                ax += dx
                ay += dy
                wins += 1
            if wins >= 2:
                new_streak = frozenset(streak)
                if not any(new_streak.issubset(s) for s in streaks):
                    streaks.add(frozenset(streak))
    return [x for x in streaks if not any(x.issubset(s) for s in streaks if s != x)]


# def print_streaks(m, sx):
#     for streak in sx:
#         for cell in sorted(streak, key=lambda e: e[1]):
#             _, x, y = cell
#             m[x][y] = elt(m, x, y) + "!"
#     print_matrix(m)


def matrix_fill(m: List) -> object:
    mm = meta_matrix()
    for _ in range(MATRIX_HEIGHT):
        for i in range(MATRIX_WIDTH):
            for j in range(MATRIX_HEIGHT):
                if m[i][j] == "#":
                    mm[i][j]["color"] = "GREEN"
                    if j < (MATRIX_HEIGHT - 1):
                        m[i][j] = m[i][j + 1]
                        m[i][j + 1] = new_gem()
                    else:
                        m[i][j] = new_gem()
    return m, mm


def update_from_streak(m: List, mm: object, streak: List) -> object:
    for cell in streak:
        _, cx, cy = cell
        m[cx][cy] = "#"
    return m, mm


def matrix_update(m: List, mm: object) -> object:
    streaks = matrix_streaks(m)
    if len(streaks) > 0:
        relevant_streak = random.choice(streaks)
        return update_from_streak(m, mm, relevant_streak)
    return m, mm


color_map = dict({"RED": ((255, 255, 255), (255, 0, 0)), "GREEN": ((255, 255, 255), (0, 255, 0)), "WHITE": ((255, 255, 255), (0, 0, 0))})


def char_colors(x, y, m, mm) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    meta_info = mm[x][y]
    if "color" in meta_info:
        return color_map[meta_info["color"]]
    else:
        c = m[x][y]
        if "#" == c:
            return color_map["RED"]
    return color_map["WHITE"]


WINDOW_WIDTH = MATRIX_WIDTH * 4
WINDOW_HEIGHT = MATRIX_HEIGHT * 4
X_BUFFER: int = int(WINDOW_WIDTH / (1 + MATRIX_WIDTH))
Y_BUFFER: int = int(WINDOW_HEIGHT / (1 + MATRIX_HEIGHT))
X_START: int = 2 * X_BUFFER
Y_START: int = Y_BUFFER


def matrix_tcod(console, m: List, mm: object):
    for j in range(MATRIX_HEIGHT):
        for i in range(MATRIX_WIDTH):
            cx = X_START + i * X_BUFFER
            cy = Y_START + j * Y_BUFFER
            ce = m[i][j]
            fg, bg = char_colors(i, j, m, mm)
            console.print_box(x=cx, y=cy, string=ce, fg=fg, bg=bg, width=1, height=1)


def main() -> None:
    tileset = tcod.tileset.load_tilesheet("curses_square_16x16_b.png", 16, 16, tcod.tileset.CHARMAP_CP437)

    console = tcod.Console(WINDOW_WIDTH, WINDOW_HEIGHT)
    matrix = init_matrix()
    meta = meta_matrix()
    # print_matrix(matrix)

    with tcod.context.new(columns=console.width, rows=console.height, tileset=tileset) as context:
        while True:  # Main loop, runs until SystemExit is raised.
            console.clear()
            matrix_tcod(console, matrix, meta)
            context.present(console)

            for event in tcod.event.wait():
                # context.convert_event(event)  # Sets tile coordinates for mouse events.
                if event.type == "KEYDOWN":
                    # print(event)
                    console.clear()
                    if event.sym == tcod.event.K_q:
                        raise SystemExit()
                    elif event.sym == tcod.event.K_d:
                        matrix, meta = matrix_update(matrix, meta)
                    elif event.sym == tcod.event.K_s:
                        streaks = matrix_streaks(matrix)
                    elif event.sym == tcod.event.K_a:
                        matrix, meta = matrix_fill(matrix)
                    elif event.sym == tcod.event.K_r:
                        matrix = init_matrix()
                        meta = meta_matrix()

                    matrix_tcod(console, matrix, meta)
                    context.present(console)  # Show the console.
                if event.type == "QUIT":
                    raise SystemExit()
        # The window will be closed after the above with-block exits.


if __name__ == "__main__":
    main()
