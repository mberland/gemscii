# * % . % . # . . . . # *
# * * % % . . % . # * # *
# # # * . * * . . X % X X
# . X . # * * % # . X # #
# . . X X . # # % X X # .
# % . % % X * % X # * % #
# * X . % # * * # X . X X
import random
from copy import deepcopy
from typing import Tuple, List
import tcod
from tcod.event import K_9, K_0
from enum import Enum
from collections import deque

gems = "ABCDEF"
MATRIX_WIDTH = 9
MATRIX_HEIGHT = 4


class Event(Enum):
    UNKNOWN = -99,
    KILLED = 10,
    BORN = 11,
    EXPLODE = 12


class Trigger:
    _cells: List
    _event: Event
    _stage: int
    _max_stage: int

    def __init__(self, cells: List, event: Event, stage: int, max_stage: int):
        self._cells = cells
        self._event = event
        self._stage = stage
        self._max_stage = max_stage

    def __str__(self):
        return "TRIGGER_{} ({} -> {}): {}".format(self._event,self._stage,self._max_stage,self._cells)


def create_trigger(cells: List, event: Event, stage: int, max_stage: int):
    GLOBAL_EVENT_QUEUE.append(Trigger(cells,event,stage,max_stage))


COLOR_MAP = dict(
    {"BLACK": (0, 0, 0),
     "WHITE": (255, 255, 255),
     "RED": (255, 0, 0),
     "GREEN": (0, 255, 0),
     "PURPLE": (255, 0, 255),
     "ORANGE": (255, 127, 0),
     "PINK": (255, 0, 127),
     "YELLOW": (255, 255, 0),
     "CYAN": (0, 255, 255),
     "BLUE": (0, 0, 255),
     })

COLORS = list(COLOR_MAP.keys())[2:]

GLOBAL_EVENT_QUEUE = deque()


def color_string(foreground: str, background: str):
    return COLOR_MAP[foreground], COLOR_MAP[background]


def valid_x(x) -> bool:
    return 0 <= x < MATRIX_WIDTH


def valid_y(y) -> bool:
    return 0 <= y < MATRIX_HEIGHT


def new_gem():
    return random.choice(gems)


def init_matrix() -> List:
    return [[random.choice(gems) for _ in range(MATRIX_HEIGHT)] for _ in range(MATRIX_WIDTH)]


# def meta_matrix() -> dict:
#     return {i: {j: {} for j in range(MATRIX_HEIGHT)} for i in range(MATRIX_WIDTH)}


def elt(m, x, y):
    if valid_x(x) and valid_y(y):
        return m[x][y]
    return None


# def display(c="|", i=-1, j=-1):
#     if i < 0 or j < 0:
#         print("", end="\n")
#     elif len(c) == 1:
#         print("{:5s}".format(c), end="")
#     else:
#         print("{:5s}".format(c), end="")


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
    return sorted([x for x in streaks if not any(x.issubset(s) for s in streaks if s != x)])


# def print_streaks(m, sx):
#     for streak in sx:
#         for cell in sorted(streak, key=lambda e: e[1]):
#             _, x, y = cell
#             m[x][y] = elt(m, x, y) + "!"
#     print_matrix(m)


def matrix_fill(m: List) -> List:
    for _ in range(MATRIX_HEIGHT):
        for i in range(MATRIX_WIDTH):
            for j in range(MATRIX_HEIGHT):
                if m[i][j] == "#":
                    if j < (MATRIX_HEIGHT - 1):
                        m[i][j] = m[i][j + 1]
                        m[i][j + 1] = new_gem()
                    else:
                        m[i][j] = new_gem()
    return m


def update_from_streak(m: List, streak: List) -> List:
    for cell in streak:
        _, cx, cy = cell
        m[cx][cy] = "#"
    return m


def update_swap_streak(m: List, streak: List) -> List:
    ce1, cx1, cy1 = streak[0]
    ce2, cx2, cy2 = streak[1]
    m[cx1][cy1] = ce2
    m[cx2][cy2] = ce1
    return m


def matrix_update(m: List) -> List:
    streaks = matrix_streaks(m)
    if len(streaks) > 0:
        for i, streak in enumerate(streaks):
            for cell in streak:
                _, cx, cy = cell
    return m


def complete_all_streaks(m: List) -> List:
    streaks = matrix_streaks(m)
    while len(streaks) > 0:
        m = update_from_streak(m, streaks[0])
        m = matrix_fill(m)
        streaks = matrix_streaks(m)
    return m


def possible_streaks(m: List) -> List:
    candidates = set()
    m = complete_all_streaks(m)
    deltas = [(i, j) for i in range(-1, 2) for j in range(-1, 2) if abs(i) != abs(j)]
    cells = [(m[i][j], i, j) for j in range(1, MATRIX_HEIGHT - 1) for i in range(1, MATRIX_WIDTH - 1)]
    for c in cells:
        neighbors = [("?", (d[0] + c[1]), (d[1] + c[2])) for d in deltas]
        for n in neighbors:
            neighbor_switch_matrix = deepcopy(m)
            if len(matrix_streaks(neighbor_switch_matrix)) > 0:
                assert False, "streaks exist?"
            neighbor_switch_matrix[n[1]][n[2]] = m[c[1]][c[2]]
            neighbor_switch_matrix[c[1]][c[2]] = m[n[1]][n[2]]
            if len(matrix_streaks(neighbor_switch_matrix)) > 0:
                candidates.add(tuple(sorted([c, (m[n[1]][n[2]], n[1], n[2])])))
    # print(candidates)
    return sorted([c for c in candidates])


def char_colors(x, y, m) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    cell_info = m[x][y]
    fg = "WHITE"
    bg = "BLACK"
    if "#" == cell_info:
        fg = "WHITE"
        bg = "RED"
    return color_string(fg, bg)


WINDOW_WIDTH = MATRIX_WIDTH * 8
WINDOW_HEIGHT = MATRIX_HEIGHT * 8
X_BUFFER: int = int(WINDOW_WIDTH / (2 + MATRIX_WIDTH))
Y_BUFFER: int = int(WINDOW_HEIGHT / (2 + MATRIX_HEIGHT))
X_START: int = 2 * X_BUFFER
Y_START: int = Y_BUFFER


def mxy(i: int, j: int) -> Tuple[int, int]:
    x = X_START + i * X_BUFFER
    y = Y_START + j * Y_BUFFER
    return x, y


def matrix_tcod(console, m: List, streaks: List = None) -> None:
    if streaks is None:
        streaks = matrix_streaks(m)
    for i, streak in enumerate(streaks):
        xmin: int = min([cell[1] for cell in streak])
        xmax: int = max([cell[1] for cell in streak])
        ymin: int = min([cell[2] for cell in streak])
        ymax: int = max([cell[2] for cell in streak])
        x1, y1 = mxy(xmin, ymin)
        x2, y2 = mxy(xmax, ymax)
        # print(xmin,ymin,xmax,ymax)
        console.draw_frame(x1 - 1, y1 - 1, x2 - x1 + 3, y2 - y1 + 3, str(i), clear=False)
    for j in range(MATRIX_HEIGHT):
        for i in range(MATRIX_WIDTH):
            cx, cy = mxy(i, j)
            ce = m[i][j]
            fg, bg = char_colors(i, j, m)
            console.print_box(x=cx, y=cy, string=ce, fg=fg, bg=bg, width=1, height=1)


def enact_global_event():
    if GLOBAL_EVENT_QUEUE.count() > 0:
        print("GLOBAL_EVENT_QUEUE ENACTING: ",GLOBAL_EVENT_QUEUE.popleft())


def main() -> None:
    # tileset = tcod.tileset.load_tilesheet("curses_square_16x16_b.png", 16, 16, tcod.tileset.CHARMAP_CP437)
    tileset = tcod.tileset.load_tilesheet("dejavu12x12_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD)
    console = tcod.Console(WINDOW_WIDTH, WINDOW_HEIGHT)
    matrix = init_matrix()
    # print_matrix(matrix)

    # os.environ["SDL_RENDER_DRIVER"] = "software"
    with tcod.context.new(columns=console.width, rows=console.height, tileset=tileset,
                          renderer=tcod.context.RENDERER_SDL2) as context:
        console.clear()
        matrix_tcod(console, matrix)
        context.present(console)
        while True:  # Main loop, runs until SystemExit is raised.
            for event in tcod.event.wait(1):
                # print(event)
                # context.convert_event(event)  # Sets tile coordinates for mouse events.

                if event.type == "KEYDOWN":

                    if event.sym == tcod.event.K_q:
                        raise SystemExit()

                    console.clear()

                    if event.sym == tcod.event.K_f:
                        matrix = complete_all_streaks(matrix)
                        # matrix, meta = matrix_update(matrix, meta)
                        matrix_tcod(console, matrix, possible_streaks(matrix))
                    else:
                        # if event.sym == tcod.event.K_d:
                        #     matrix, meta = matrix_update(matrix, meta)
                        if event.sym == tcod.event.K_s:
                            matrix = complete_all_streaks(matrix)
                        if event.sym == tcod.event.K_a:
                            matrix = matrix_fill(matrix)
                        if event.sym == tcod.event.K_r:
                            matrix = init_matrix()
                            # meta = meta_matrix()
                        if K_0 <= event.sym <= K_9:
                            s_num = event.sym - K_0
                            streaks = possible_streaks(matrix)
                            if s_num < len(streaks):
                                matrix = update_swap_streak(matrix, streaks[s_num])
                                matrix = complete_all_streaks(matrix)

                        matrix = matrix_update(matrix)
                        matrix_tcod(console, matrix)

                    context.present(console)
                if event.type == "QUIT":
                    raise SystemExit()
        # The window will be closed after the above with-block exits.


if __name__ == "__main__":
    main()
