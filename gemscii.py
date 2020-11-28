import random
import tcod
import time
from collections import deque
from copy import deepcopy
from enum import Enum
from typing import Tuple, List

from tcod.event import K_9, K_0

gems = "ABCDEF"
MATRIX_WIDTH = 9
MATRIX_HEIGHT = 4
ANIMATION_LENGTH = 5
COLOR_MATRIX_FG = []
COLOR_MATRIX_BG = []

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


def reset_color_matrix(c: str) -> List:
    return [[c for _ in range(MATRIX_HEIGHT)] for _ in range(MATRIX_WIDTH)]


def reset_color_matrices() -> None:
    global COLOR_MATRIX_BG, COLOR_MATRIX_FG
    COLOR_MATRIX_FG = reset_color_matrix("WHITE")
    COLOR_MATRIX_BG = reset_color_matrix("BLACK")


def set_fgcolor(x: int, y: int, color: str) -> None:
    global COLOR_MATRIX_FG
    COLOR_MATRIX_FG[x][y] = color


def set_bgcolor(x: int, y: int, color: str) -> None:
    global COLOR_MATRIX_BG
    COLOR_MATRIX_BG[x][y] = color


def fgcolor(x: int, y: int) -> str:
    return COLOR_MATRIX_FG[x][y]


def bgcolor(x: int, y: int) -> str:
    return COLOR_MATRIX_BG[x][y]


reset_color_matrices()


class CellState(Enum):
    UNKNOWN = -99,
    NO_EVENT = 0,
    KILLED = 10,
    BORN = 11,
    EXPLODE = 12,
    ANIMATE = 13,
    SWAP = 14


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Cell:
    def __init__(self, x: int, y: int, gem: str, color: str = "WHITE"):
        self.p = Point(x, y)
        self.gem = gem
        self.color = color


class Event:
    def __init__(self, cells: List, event_type: CellState):
        self._cells = cells
        self._event_type = event_type

    def go(self) -> None:
        print(self)

    def completed(self) -> bool:
        return True

    def __str__(self):
        return f"UNDEFINED EVENT: {self._event_type}"

    def do_swap(self, matrix):
        assert False, f"TRIED TO CALL SWAP ON NON-SWAP EVENT: {self._event_type}"
        pass


DEFAULT_EVENT = Event([], CellState.NO_EVENT)


def event_create(event: Event):
    GLOBAL_EVENT_QUEUE.append(event)


def event_go() -> Event:
    global DEFAULT_EVENT
    if len(GLOBAL_EVENT_QUEUE) > 0:
        event = GLOBAL_EVENT_QUEUE.popleft()
        event.go()
        return event
    reset_color_matrices()
    return DEFAULT_EVENT


class Animation(Event):
    def __init__(self, cells: List, event_type: CellState, colors: List, stage: int = 0):
        super().__init__(cells, event_type)
        self._colors = colors
        self._stage = stage
        self._max_stage = ANIMATION_LENGTH

    def go(self):
        super().go()
        for cell in self._cells:
            set_fgcolor(cell[0], cell[1], self._colors[0])
        if self._stage < self._max_stage:
            self._colors = self._colors[1:] + self._colors[:1]
            event_create(Animation(self._cells, self._event_type, self._colors, self._stage + 1))

    def __str__(self):
        return "ANIMATION ({} , {}) {} => {}: {}".format(self._cells[0][0], self._cells[0][1], self._stage,
                                                         self._max_stage, self._colors)


COLORS = list(COLOR_MAP.keys())[2:]

GLOBAL_EVENT_QUEUE = deque()


def valid_x(x) -> bool:
    return 0 <= x < MATRIX_WIDTH


def valid_y(y) -> bool:
    return 0 <= y < MATRIX_HEIGHT


def new_gem():
    return random.choice(gems)


def init_matrix() -> List:
    return [[random.choice(gems) for _ in range(MATRIX_HEIGHT)] for _ in range(MATRIX_WIDTH)]


def elt(m, x, y):
    if valid_x(x) and valid_y(y):
        return m[x][y]
    return None


def set_elt(m: List, c: str, x: int, y: int) -> List:
    if valid_x(x) and valid_y(y):
        m[x][y] = c
    return m


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


def matrix_fill(m: List) -> List:
    for _ in range(MATRIX_HEIGHT):
        for i in range(MATRIX_WIDTH):
            for j in range(MATRIX_HEIGHT):
                if elt(m, i, j) == "#":
                    if j < (MATRIX_HEIGHT - 1):
                        m = set_elt(m, elt(m, i, j + 1), i, j)
                        m = set_elt(m, new_gem(), i, j + 1)
                    else:
                        m = set_elt(m, new_gem(), i, j)
    return m


def update_from_streak(m: List, streak: List) -> List:
    for cell in streak:
        _, cx, cy = cell
        set_elt(m, "#", cx, cy)
    return m


def update_swap_streak(m: List, streak: Tuple[Tuple[str, int, int], Tuple[str, int, int]]) -> List:
    ce1, cx1, cy1 = streak[0]
    ce2, cx2, cy2 = streak[1]
    m = set_elt(m, ce2, cx1, cy1)
    m = set_elt(m, ce1, cx2, cy2)
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
    cells = [(elt(m, i, j), i, j) for j in range(1, MATRIX_HEIGHT - 1) for i in range(1, MATRIX_WIDTH - 1)]
    for c in cells:
        neighbors = [("?", (d[0] + c[1]), (d[1] + c[2])) for d in deltas]
        for n in neighbors:
            neighbor_switch_matrix = deepcopy(m)
            if len(matrix_streaks(neighbor_switch_matrix)) > 0:
                assert False, "streaks exist?"
            neighbor_switch_matrix = set_elt(neighbor_switch_matrix, elt(m, c[1], c[2]), n[1], n[2])
            neighbor_switch_matrix = set_elt(neighbor_switch_matrix, elt(m, n[1], n[2]), c[1], c[2])
            if len(matrix_streaks(neighbor_switch_matrix)) > 0:
                candidates.add(tuple(sorted([c, (elt(m, n[1], n[2]), n[1], n[2])])))
    return sorted([c for c in candidates])


class Swap(Event):
    _stage: int
    _max_stage: int
    _ca: Tuple[int, int]
    _cb: Tuple[int, int]
    _completed: bool

    def __init__(self, cells: List, event_type: CellState, stage: int = 0):
        super().__init__(cells, event_type)
        self._ca = cells[0]
        self._cb = cells[1]
        self._stage = stage
        self._max_stage = ANIMATION_LENGTH
        self._completed = True

    def go(self):
        super().go()
        if self._stage < self._max_stage:
            self._stage += 1
            event_create(Swap(self._cells, self._event_type, self._stage))
        else:
            self._completed = False

    def do_swap(self, m: List) -> List:
        cx1, cy1 = self._ca
        cx2, cy2 = self._cb
        streak = tuple([tuple([str(m[cx1][cy1]), cx1, cy1]), tuple([str(m[cx2][cy2]), cx2, cy2])])
        m = update_swap_streak(m, streak)
        m = complete_all_streaks(m)
        return m

    def completed(self) -> bool:
        return self._completed

    def __str__(self):
        return f"SWAP ({self._ca}) <=> ({self._cb}) {self._stage} ... {self._max_stage}"


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


def matrix_tcod(console, m: List) -> None:
    def color_string(foreground: str, background: str):
        return COLOR_MAP[foreground], COLOR_MAP[background]

    def char_colors(x: int, y: int) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
        return color_string(COLOR_MATRIX_FG[x][y], COLOR_MATRIX_BG[x][y])

    streaks = possible_streaks(m)
    for i, streak in enumerate(streaks):
        xmin: int = min([cell[1] for cell in streak])
        xmax: int = max([cell[1] for cell in streak])
        ymin: int = min([cell[2] for cell in streak])
        ymax: int = max([cell[2] for cell in streak])
        x1, y1 = mxy(xmin, ymin)
        x2, y2 = mxy(xmax, ymax)
        console.draw_frame(x1 - 1, y1 - 1, x2 - x1 + 3, y2 - y1 + 3, str(i), clear=False)
    for j in range(MATRIX_HEIGHT):
        for i in range(MATRIX_WIDTH):
            cx, cy = mxy(i, j)
            ce = elt(m, i, j)
            fg, bg = char_colors(i, j)
            console.print_box(x=cx, y=cy, string=ce, fg=fg, bg=bg, width=1, height=1)


def main() -> None:
    # tileset = tcod.tileset.load_tilesheet("curses_square_16x16_b.png", 16, 16, tcod.tileset.CHARMAP_CP437)
    tileset = tcod.tileset.load_tilesheet("dejavu12x12_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD)
    console = tcod.Console(WINDOW_WIDTH, WINDOW_HEIGHT)
    matrix = init_matrix()

    with tcod.context.new(columns=console.width, rows=console.height, tileset=tileset,
                          renderer=tcod.context.RENDERER_SDL2) as context:
        console.clear()
        matrix_tcod(console, matrix)
        context.present(console)
        while True:

            console.clear()
            event = event_go()
            if not event.completed():
                if CellState.SWAP == event._event_type:
                    matrix = event.do_swap(matrix)
            matrix = complete_all_streaks(matrix)
            matrix = matrix_fill(matrix)
            matrix_tcod(console, matrix)
            context.present(console)
            time.sleep(0.05)

            for event in tcod.event.get():
                if event.type == "QUIT":
                    raise SystemExit()
                if event.type == "KEYDOWN":
                    if event.sym == tcod.event.K_q:
                        raise SystemExit()
                    elif K_0 <= event.sym <= K_9:
                        s_num = event.sym - K_0
                        streaks = possible_streaks(matrix)
                        if s_num < len(streaks):
                            streak = streaks[s_num]
                            _, cx1, cy1 = streak[0]
                            _, cx2, cy2 = streak[1]
                            event_create(Swap([(cx1, cy1), (cx2, cy2)], CellState.SWAP))
                            event_create(Animation([(cx1, cy1), (cx2, cy2)], CellState.ANIMATE,
                                                   ["RED", "BLUE", "GREEN", "PURPLE"]))
                    else:
                        print(f"BAD KEY: {event}")


if __name__ == "__main__":
    main()
