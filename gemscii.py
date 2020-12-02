import random
from datetime import datetime

import tcod
import time
from collections import deque
from copy import deepcopy
from enum import Enum
from typing import Tuple, List, FrozenSet

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


class CellState(Enum):
    UNKNOWN = -99,
    NO_EVENT = 0,
    ALIVE = 1,
    KILLED = 10,
    BORN = 11,
    MATCH = 12,
    ANIMATE = 13,
    SWAP = 14


COLORS = list(COLOR_MAP.keys())[2:]

GLOBAL_EVENT_QUEUE = deque()


def valid_x(x) -> bool:
    return 0 <= x < MATRIX_WIDTH


def valid_y(y) -> bool:
    return 0 <= y < MATRIX_HEIGHT


def new_gem() -> str:
    return random.choice(gems)


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __key(self):
        return self.x, self.y

    def __ne__(self, other):
        return not self.__eq__(other)

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, Point):
            return self.__key() == other.__key()
        return NotImplemented

    def __str__(self):
        return f"P({self.x},{self.y})"


class Cell:
    def __init__(self, x: int, y: int, gem: str, fg: str = "WHITE", bg: str = "BLACK",
                 state: CellState = CellState.BORN):
        self.p = Point(x, y)
        self._gem = gem
        self._fgcolor = fg
        self._bgcolor = bg
        self._state = state

    @property
    def gem(self):
        return self._gem

    @property
    def fgcolor(self):
        return self._fgcolor

    @property
    def bgcolor(self):
        return self._bgcolor

    @property
    def state(self) -> CellState:
        return self._state

    @state.setter
    def state(self, state: CellState):
        self._state = state

    @gem.setter
    def gem(self, gem: str) -> None:
        self._gem = gem

    @fgcolor.setter
    def fgcolor(self, fg: str) -> None:
        self._fgcolor = fg

    @bgcolor.setter
    def bgcolor(self, bg: str) -> None:
        self._bgcolor = bg

    def __str__(self):
        return f"CELL ({self.p.x}, {self.p.y}) = {self.state} [{self.fgcolor}, {self.bgcolor}]"


CellMatrix = List[List[Cell]]
ColorRGB = Tuple[int, int, int]
SwapStreak = FrozenSet[Point]

GLOBAL_CELL_MATRIX = [[Cell(i, j, new_gem()) for j in range(MATRIX_HEIGHT)] for i in range(MATRIX_WIDTH)]


def cm_cell(m: CellMatrix, x: int, y: int) -> Cell:
    return m[x][y]


def c_cell(x: int, y: int) -> Cell:
    return cm_cell(GLOBAL_CELL_MATRIX, x, y)


def c_set_state(x: int, y: int, state: CellState) -> None:
    global GLOBAL_CELL_MATRIX
    GLOBAL_CELL_MATRIX[x][y].state = state


# def cm_set_cell(m: CellMatrix, x: int, y: int, cell: Cell) -> CellMatrix:
#     m[x][y] = cell
#     return m


# def c_set_cell(x: int, y: int, cell: Cell) -> None:
#     global GLOBAL_CELL_MATRIX
#     GLOBAL_CELL_MATRIX[x][y] = cell


def c_set_gem(x: int, y: int, gem: str) -> None:
    global GLOBAL_CELL_MATRIX
    GLOBAL_CELL_MATRIX[x][y].gem = gem
    GLOBAL_CELL_MATRIX[x][y].state = CellState.BORN


def cm_set_gem(m: CellMatrix, x: int, y: int, gem: str) -> CellMatrix:
    m[x][y].gem = gem
    m[x][y].state = CellState.BORN
    return m


def c_set_colors(x: int, y: int, fg: str = "WHITE", bg: str = "BLACK") -> None:
    GLOBAL_CELL_MATRIX[x][y].bgcolor = bg
    GLOBAL_CELL_MATRIX[x][y].fgcolor = fg


def cm_set_colors(m: CellMatrix, x: int, y: int, fg: str = "WHITE", bg: str = "BLACK") -> CellMatrix:
    m[x][y].bgcolor = bg
    m[x][y].fgcolor = fg
    return m


def c_colors(x: int, y: int) -> Tuple[str, str]:
    global GLOBAL_CELL_MATRIX
    return cm_cell(GLOBAL_CELL_MATRIX, x, y).fgcolor, cm_cell(GLOBAL_CELL_MATRIX, x, y).bgcolor


def cm_gem(m: CellMatrix, x: int, y: int) -> str:
    return cm_cell(m, x, y).gem


def c_gem(x: int, y: int) -> str:
    return cm_cell(GLOBAL_CELL_MATRIX, x, y).gem


def cm_state(m: CellMatrix, x: int, y: int) -> CellState:
    return cm_cell(m, x, y).state


def c_state(x: int, y: int) -> CellState:
    global GLOBAL_CELL_MATRIX
    return cm_state(GLOBAL_CELL_MATRIX, x, y)


# c_set_colors(0,0,"PURPLE","GREEN")
# assert "PURPLE" == c_cell(0,0).fgcolor and "GREEN" == c_cell(0,0).bgcolor, "c_set_colors not working as intended"
#

def c_reset_color_matrix(fg: str, bg: str) -> None:
    for j in range(MATRIX_HEIGHT):
        for i in range(MATRIX_WIDTH):
            c_set_colors(i, j, fg, bg)


# def reset_color_matrix(c: str) -> List:
#     return [[c for _ in range(MATRIX_HEIGHT)] for _ in range(MATRIX_WIDTH)]
#
#
# def reset_color_matrices() -> None:
#     global COLOR_MATRIX_BG, COLOR_MATRIX_FG
#     COLOR_MATRIX_FG = reset_color_matrix("WHITE")
#     COLOR_MATRIX_BG = reset_color_matrix("BLACK")
#
#
# def set_fgcolor(x: int, y: int, color: str) -> None:
#     global COLOR_MATRIX_FG
#     COLOR_MATRIX_FG[x][y] = color
#
#
# def set_bgcolor(x: int, y: int, color: str) -> None:
#     global COLOR_MATRIX_BG
#     COLOR_MATRIX_BG[x][y] = color
#
#
# def fgcolor(x: int, y: int) -> str:
#     return COLOR_MATRIX_FG[x][y]
#
#
# def bgcolor(x: int, y: int) -> str:
#     return COLOR_MATRIX_BG[x][y]
#
#
# reset_color_matrices()
# c_reset_color_matrix("WHITE", "BLACK")


class Event:
    def __init__(self, cells: List, event_type: CellState, stage: int = 0):
        self._cells = cells
        self._event_type = event_type
        self._completed = True
        self._stage = stage
        self._max_stage = ANIMATION_LENGTH

    @property
    def event_type(self) -> CellState:
        return self._event_type

    @property
    def cells(self) -> List:
        return self._cells

    @property
    def stage(self) -> int:
        return self._stage

    @property
    def max_stage(self) -> int:
        return self._max_stage

    @stage.setter
    def stage(self, stage: int) -> None:
        self._stage = stage

    def go(self) -> None:
        self.stage += 1
        print(self)

    @property
    def completed(self) -> bool:
        return self._completed

    @completed.setter
    def completed(self, completed: bool) -> None:
        self._completed = completed

    def __str__(self) -> str:
        return f"UNDEFINED EVENT: {self.event_type} {datetime.now()}"


DEFAULT_EVENT = Event([], CellState.NO_EVENT)


def event_create(event: Event):
    GLOBAL_EVENT_QUEUE.append(event)


def event_go() -> Event:
    global DEFAULT_EVENT
    if len(GLOBAL_EVENT_QUEUE) > 0:
        event = GLOBAL_EVENT_QUEUE.popleft()
        event.go()
        return event
    c_reset_color_matrix("WHITE","BLACK")
    return DEFAULT_EVENT
#

# class Animation(Event):
#     def __init__(self, cells: List, event_type: CellState, colors: List, stage: int = 0):
#         super().__init__(cells, event_type)
#         self._colors = colors
#         self._stage = stage
#         self._max_stage = ANIMATION_LENGTH
#
#     def go(self):
#         super().go()
#         for cell in self._cells:
#             set_fgcolor(cell[0], cell[1], self._colors[0])
#         if self._stage < self._max_stage:
#             self._colors = self._colors[1:] + self._colors[:1]
#             event_create(Animation(self.cells, self.event_type, self._colors, self._stage + 1))
#
#     def __str__(self):
#         return "ANIMATION ({} , {}) {} => {}: {}".format(self._cells[0][0], self._cells[0][1], self._stage,
#                                                          self._max_stage, self._colors)


class CAnimation(Event):
    def __init__(self, cells: List[Point], colors: List, stage: int = 0):
        super().__init__(cells, CellState.ANIMATE)
        self._colors = colors
        self._stage = stage
        self._max_stage = ANIMATION_LENGTH
        self._completed = True

    @property
    def color(self) -> str:
        output = self._colors[0]
        self._colors = self._colors[1:] + self._colors[:1]
        return output

    @property
    def colors(self):
        return self._colors

    def go(self):
        super().go()
        for cell in self._cells:
            c_set_colors(cell.x, cell.y, self.color)
        if self._stage < self._max_stage:
            event_create(CAnimation(self.cells, self.colors, self.stage + 1))

    def __str__(self):
        return f"ANIMATION ({[str(c) for c in self.cells]}) {self.stage} => {self.max_stage}: {self.colors}"
#
#
# def init_matrix() -> List:
#     return [[random.choice(gems) for _ in range(MATRIX_HEIGHT)] for _ in range(MATRIX_WIDTH)]
#
#
# def elt(m, x, y):
#     if valid_x(x) and valid_y(y):
#         return m[x][y]
#     return None
#
#
# def set_elt(m: List, c: str, x: int, y: int) -> List:
#     if valid_x(x) and valid_y(y):
#         m[x][y] = c
#     return m

#
# def matrix_streaks(m: List) -> List:
#     streaks = set()
#     deltas = [(i, j) for i in range(-1, 2) for j in range(-1, 2) if i != 0 or j != 0]
#     cells = [(i, j) for j in range(MATRIX_HEIGHT) for i in range(MATRIX_WIDTH)]
#     for cell in cells:
#         for delta in deltas:
#             wins = 0
#             cx, cy = cell
#             dx, dy = delta
#             ax, ay = delta
#             cell_type = elt(m, cx, cy)
#             streak = {tuple([cell_type, cx, cy])}
#             while cell_type and valid_x(cx + ax) and valid_y(cy + ay) and cell_type == elt(m, cx + ax, cy + ay):
#                 streak.add(tuple([cell_type, cx + ax, cy + ay]))
#                 ax += dx
#                 ay += dy
#                 wins += 1
#             if wins >= 2:
#                 new_streak = frozenset(streak)
#                 if not any(new_streak.issubset(s) for s in streaks):
#                     streaks.add(frozenset(streak))
#     return sorted([x for x in streaks if not any(x.issubset(s) for s in streaks if s != x)])


def cm_matrix_streaks(m: CellMatrix) -> List[FrozenSet[Point]]:
    streaks = set()
    deltas = [(i, j) for i in range(-1, 2) for j in range(-1, 2) if i != 0 or j != 0]
    points = [Point(i, j) for j in range(MATRIX_HEIGHT) for i in range(MATRIX_WIDTH)]
    for p in points:
        for delta in deltas:
            matches = 0
            dx, dy = delta
            ax, ay = delta
            gem = cm_gem(m, p.x, p.y)
            streak = {Point(p.x, p.y)}
            while valid_x(p.x + ax) and valid_y(p.y + ay) and gem == cm_gem(m, p.x + ax, p.y + ay):
                streak.add(Point(p.x + ax, p.y + ay))
                ax += dx
                ay += dy
                matches += 1
            if matches >= 2:
                streaks.add(frozenset(streak))
    return sorted([x for x in streaks if not any(x.issubset(s) for s in streaks if s != x)])


def c_matrix_streaks() -> List[FrozenSet[Point]]:
    global GLOBAL_CELL_MATRIX
    return cm_matrix_streaks(GLOBAL_CELL_MATRIX)


# def c_matrix_streaks() -> List[FrozenSet[Point]]:
#     streaks = set()
#     deltas = [(i, j) for i in range(-1, 2) for j in range(-1, 2) if i != 0 or j != 0]
#     points = [Point(i, j) for j in range(MATRIX_HEIGHT) for i in range(MATRIX_WIDTH)]
#     for p in points:
#         for delta in deltas:
#             matches = 0
#             dx, dy = delta
#             ax, ay = delta
#             gem = c_gem(p.x, p.y)
#             streak = {Point(p.x,p.y)}
#             while valid_x(p.x + ax) and valid_y(p.y + ay) and gem == c_gem(p.x + ax, p.y + ay):
#                 streak.add(Point(p.x + ax, p.y + ay))
#                 ax += dx
#                 ay += dy
#                 matches += 1
#             if matches >= 2:
#                 streaks.add(frozenset(streak))
#     return sorted([x for x in streaks if not any(x.issubset(s) for s in streaks if s != x)])

#
# def matrix_fill(m: List) -> List:
#     for _ in range(MATRIX_HEIGHT):
#         for i in range(MATRIX_WIDTH):
#             for j in range(MATRIX_HEIGHT):
#                 if elt(m, i, j) == "#":
#                     if j < (MATRIX_HEIGHT - 1):
#                         m = set_elt(m, elt(m, i, j + 1), i, j)
#                         m = set_elt(m, new_gem(), i, j + 1)
#                     else:
#                         m = set_elt(m, new_gem(), i, j)
#     return m


def c_matrix_fill() -> None:
    for _ in range(MATRIX_HEIGHT):
        for i in range(MATRIX_WIDTH):
            for j in range(MATRIX_HEIGHT):
                if c_state(i, j) == CellState.KILLED:
                    print(f"KILLED: ({i},{j})")
                    if j < (MATRIX_HEIGHT - 1):
                        c_set_gem(i, j, c_gem(i, j + 1))
                        c_set_gem(i, j, new_gem())
                    else:
                        c_set_gem(i, j, new_gem())


# def update_from_streak(m: List, streak: List) -> List:
#     for cell in streak:
#         _, cx, cy = cell
#         set_elt(m, "#", cx, cy)
#     return m


def c_update_from_streak(streak: FrozenSet[Point]) -> None:
    for p in streak:
        c_set_state(p.x, p.y, CellState.KILLED)

#
# def swap_gems(m: List, streak: Tuple[Tuple[str, int, int], Tuple[str, int, int]]) -> List:
#     ce1, cx1, cy1 = streak[0]
#     ce2, cx2, cy2 = streak[1]
#     m = set_elt(m, ce2, cx1, cy1)
#     m = set_elt(m, ce1, cx2, cy2)
#     return m
#

def cm_swap_gems(m: CellMatrix, streak: Tuple[Point, ...]) -> CellMatrix:
    p1, p2 = streak
    swap_gem = cm_gem(m, p1.x, p1.y)
    m = cm_set_gem(m, p1.x, p1.y, c_gem(p2.x, p2.y))
    m = cm_set_gem(m, p2.x, p2.y, swap_gem)
    return m


def c_swap_gems(streak: Tuple[Point, ...]) -> None:
    p1, p2 = streak
    swap_gem = c_gem(p1.x, p1.y)
    c_set_gem(p1.x, p1.y, c_gem(p2.x, p2.y))
    c_set_gem(p2.x, p2.y, swap_gem)

#
# def complete_all_streaks(m: List) -> List:
#     streaks = matrix_streaks(m)
#     while len(streaks) > 0:
#         m = update_from_streak(m, streaks[0])
#         m = matrix_fill(m)
#         streaks = matrix_streaks(m)
#     return m


def c_complete_all_streaks() -> None:
    streaks = c_matrix_streaks()
    while len(streaks) > 0:
        c_update_from_streak(streaks[0])
        c_matrix_fill()
        streaks = c_matrix_streaks()


# def possible_streaks(m: List) -> List:
#     candidates = set()
#     m = complete_all_streaks(m)
#     deltas = [(i, j) for i in range(-1, 2) for j in range(-1, 2) if abs(i) != abs(j)]
#     cells = [(elt(m, i, j), i, j) for j in range(1, MATRIX_HEIGHT - 1) for i in range(1, MATRIX_WIDTH - 1)]
#     for c in cells:
#         neighbors = [("?", (d[0] + c[1]), (d[1] + c[2])) for d in deltas]
#         for n in neighbors:
#             neighbor_switch_matrix = deepcopy(m)
#             if len(matrix_streaks(neighbor_switch_matrix)) > 0:
#                 assert False, "streaks exist?"
#             neighbor_switch_matrix = set_elt(neighbor_switch_matrix, elt(m, c[1], c[2]), n[1], n[2])
#             neighbor_switch_matrix = set_elt(neighbor_switch_matrix, elt(m, n[1], n[2]), c[1], c[2])
#             if len(matrix_streaks(neighbor_switch_matrix)) > 0:
#                 candidates.add(tuple(sorted([c, (elt(m, n[1], n[2]), n[1], n[2])])))
#     return sorted([c for c in candidates])


def c_possible_streaks() -> List[FrozenSet[Point]]:
    # assert False, "c_possible_streaks() UNIMPLEMENTED"
    candidates = set()
    c_complete_all_streaks()
    deltas = [Point(i, j) for i in range(-1, 2) for j in range(-1, 2) if abs(i) != abs(j)]
    points = [Point(i, j) for j in range(1, MATRIX_HEIGHT - 1) for i in range(1, MATRIX_WIDTH - 1)]
    for p in points:
        neighbors: List[Point] = [Point(p.x + d.x, p.y + d.y) for d in deltas if valid_x(p.x + d.x) and valid_y(p.y + d.y)]
        for n in neighbors:
            neighbor_switch_matrix: CellMatrix = deepcopy(GLOBAL_CELL_MATRIX)
            neighbor_switch_matrix = cm_swap_gems(neighbor_switch_matrix, tuple([p, n]))
            if len(cm_matrix_streaks(neighbor_switch_matrix)) > 0:
                candidates.add(frozenset([p, n]))
    return sorted([c for c in candidates])


class CSwap(Event):
    def __init__(self, cells: List, stage: int = 0):
        super().__init__(cells, CellState.SWAP, stage)
        self._max_stage = ANIMATION_LENGTH

    def go(self):
        super().go()
        if 0 == self.stage:
            event_create(CAnimation(self._cells, ["GREEN", "PURPLE"]))
        if self.stage < self.max_stage:
            self.stage += 1
            event_create(CSwap(self.cells, self.stage))
        else:
            c_complete_all_streaks()
            assert 2 == len(self.cells), f"ERROR: CSwap was asked to swap this: {self.cells}"
            c_swap_gems(tuple([cell for cell in self.cells]))


class CMatch(Event):
    def __init__(self, cells: List, stage: int = 0):
        super().__init__(cells, CellState.MATCH, stage)

    def go(self):
        super().go()
        if self.stage < self.max_stage:
            event_create(CAnimation(self._cells, ["ORANGE", "PINK"]))
            event_create(CMatch(self._cells, self._stage))
        else:
            c_complete_all_streaks()
            c_swap_gems(tuple([self._cells[0], self._cells[1]]))


class CDeath(Event):
    def __init__(self, cells: List, event_type: CellState):
        super().__init__(cells, event_type)
        assert False, "CDeath UNIMPLEMENTED"

#
# class Swap(Event):
#     _stage: int
#     _max_stage: int
#     _ca: Tuple[int, int]
#     _cb: Tuple[int, int]
#     _completed: bool
#
#     def __init__(self, cells: List, event_type: CellState, stage: int = 0):
#         super().__init__(cells, event_type)
#         self._ca = cells[0]
#         self._cb = cells[1]
#         self._stage = stage
#         self._max_stage = ANIMATION_LENGTH
#         self._completed = True
#
#     def go(self):
#         super().go()
#         if self._stage < self._max_stage:
#             self._stage += 1
#             event_create(Swap(self._cells, self._event_type, self._stage))
#         else:
#             self._completed = False
#
#     def do_swap(self, m: List) -> List:
#         cx1, cy1 = self._ca
#         cx2, cy2 = self._cb
#         streak = tuple([tuple([str(m[cx1][cy1]), cx1, cy1]), tuple([str(m[cx2][cy2]), cx2, cy2])])
#         m = swap_gems(m, streak)
#         m = complete_all_streaks(m)
#         return m
#
#     def __str__(self):
#         return f"SWAP ({self._ca}) <=> ({self._cb}) {self._stage} ... {self._max_stage}"
#


WINDOW_WIDTH = MATRIX_WIDTH * 8
WINDOW_HEIGHT = MATRIX_HEIGHT * 8
X_BUFFER: int = int(WINDOW_WIDTH / (2 + MATRIX_WIDTH))
Y_BUFFER: int = int(WINDOW_HEIGHT / (2 + MATRIX_HEIGHT))
X_START: int = 2 * X_BUFFER
Y_START: int = Y_BUFFER


def ij_to_window_xy(cx: int, cy: int) -> Tuple[int, int]:
    x = X_START + cx * X_BUFFER
    y = Y_START + cy * Y_BUFFER
    return x, y


# def matrix_tcod(console, m: List) -> None:
#     def color_string(foreground: str, background: str):
#         return COLOR_MAP[foreground], COLOR_MAP[background]
#
#     def char_colors(x: int, y: int) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
#         return color_string(COLOR_MATRIX_FG[x][y], COLOR_MATRIX_BG[x][y])
#
#     streaks = possible_streaks(m)
#     for i, streak in enumerate(streaks):
#         xmin: int = min([cell[1] for cell in streak])
#         xmax: int = max([cell[1] for cell in streak])
#         ymin: int = min([cell[2] for cell in streak])
#         ymax: int = max([cell[2] for cell in streak])
#         x1, y1 = ij_to_window_xy(xmin, ymin)
#         x2, y2 = ij_to_window_xy(xmax, ymax)
#         console.draw_frame(x1 - 1, y1 - 1, x2 - x1 + 3, y2 - y1 + 3, str(i), clear=False)
#     for j in range(MATRIX_HEIGHT):
#         for i in range(MATRIX_WIDTH):
#             cx, cy = ij_to_window_xy(i, j)
#             ce = elt(m, i, j)
#             fg, bg = char_colors(i, j)
#             console.print_box(x=cx, y=cy, string=ce, fg=fg, bg=bg, width=1, height=1)


def c_matrix_tcod(console) -> None:
    global GLOBAL_CELL_MATRIX
    w_buffer: int = 1

    def cx_to_wx(cx: int) -> int:
        return X_START + cx * X_BUFFER

    def cy_to_wy(cy: int) -> int:
        return Y_START + cy * Y_BUFFER

    def c_color_string(foreground: str, background: str) -> Tuple[ColorRGB, ColorRGB]:
        return COLOR_MAP[foreground], COLOR_MAP[background]

    def c_char_colors(x: int, y: int) -> Tuple[ColorRGB, ColorRGB]:
        _fg, _bg = c_colors(x, y)
        return c_color_string(_fg, _bg)

    streaks = c_possible_streaks()
    for i, streak in enumerate(streaks):
        xmin: int = min([cell.x for cell in streak])
        xmax: int = max([cell.x for cell in streak])
        ymin: int = min([cell.y for cell in streak])
        ymax: int = max([cell.y for cell in streak])
        pmin = Point(cx_to_wx(xmin), cy_to_wy(ymin))
        pmax = Point(cx_to_wx(xmax), cy_to_wy(ymax))
        console.draw_frame(pmin.x - w_buffer, pmin.y - w_buffer, pmax.x - pmin.x + 3 * w_buffer, pmax.y - pmin.y + 3 * w_buffer, str(i), clear=False)
    for j in range(MATRIX_HEIGHT):
        for i in range(MATRIX_WIDTH):
            fg, bg = c_char_colors(i, j)
            console.print_box(x=cx_to_wx(i), y=cy_to_wy(j), string=c_gem(i, j), fg=fg, bg=bg, width=1, height=1)


def main() -> None:
    # tileset = tcod.tileset.load_tilesheet("curses_square_16x16_b.png", 16, 16, tcod.tileset.CHARMAP_CP437)
    tileset = tcod.tileset.load_tilesheet("dejavu12x12_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD)
    console = tcod.Console(WINDOW_WIDTH, WINDOW_HEIGHT)

    with tcod.context.new(columns=console.width, rows=console.height, tileset=tileset,
                          renderer=tcod.context.RENDERER_SDL2) as context:
        console.clear()
        c_matrix_tcod(console)
        context.present(console)
        while True:

            console.clear()
            event = event_go()
            if CellState.NO_EVENT == event.event_type:
                print(".",end="")
            else:
                print(f"MAIN LOOP EVENT: {event} [OPTIONS: {len(c_possible_streaks())}]")
            c_complete_all_streaks()
            c_matrix_fill()
            c_matrix_tcod(console)
            context.present(console)
            time.sleep(0.5)

            for event in tcod.event.get():
                if event.type == "QUIT":
                    raise SystemExit()
                if event.type == "KEYDOWN":
                    if event.sym == tcod.event.K_q:
                        raise SystemExit()
                    elif K_0 <= event.sym <= K_9:
                        s_num = event.sym - K_0
                        streaks = c_possible_streaks()
                        if s_num < len(streaks):
                            print(f"SELECTED: STREAK {s_num}")
                            streak = streaks[s_num]
                            event_create(CSwap(streak))
                    else:
                        print(f"BAD KEY: {event}")


if __name__ == "__main__":
    main()
