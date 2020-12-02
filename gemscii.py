import random
from datetime import datetime

import tcod
import time
from collections import deque
from copy import deepcopy
from enum import Enum
from typing import Tuple, List, FrozenSet

from tcod.event import K_9, K_0

# CONSTANTS

gems: str = "ABCDEF"
MATRIX_WIDTH: int = 9
MATRIX_HEIGHT: int = 4
ANIMATION_LENGTH: int = 5
WINDOW_WIDTH: int = MATRIX_WIDTH * 8
WINDOW_HEIGHT: int = MATRIX_HEIGHT * 8
X_BUFFER: int = int(WINDOW_WIDTH / (2 + MATRIX_WIDTH))
Y_BUFFER: int = int(WINDOW_HEIGHT / (2 + MATRIX_HEIGHT))
X_START: int = 2 * X_BUFFER
Y_START: int = Y_BUFFER
GLOBAL_EVENT_QUEUE = deque()

# CLASSES and TYPES

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
    SWAP = 14,
    DYING = 15


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


class Event:
    def __init__(self, cells: List[Point], event_type: CellState, stage: int = 0):
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
        if self.stage >= self.max_stage:
            self._completed = True
        return self._completed

    @completed.setter
    def completed(self, completed: bool) -> None:
        self._completed = completed

    def __str__(self) -> str:
        return f"UNDEFINED EVENT: {self.event_type} {datetime.now()}"


DEFAULT_EVENT = Event([], CellState.NO_EVENT)


class CAnimation(Event):
    def __init__(self, cells: List[Point], colors: List[str], stage: int = 0, max_stage: int = ANIMATION_LENGTH):
        super().__init__(cells, CellState.ANIMATE)
        self._colors = colors
        self._stage = stage
        self._max_stage = max_stage
        self._completed = True

    @property
    def color(self) -> str:
        output = self.colors[0]
        self.colors = self.colors[1:] + self.colors[:1]
        return output

    @property
    def colors(self) -> List[str]:
        return self._colors

    @colors.setter
    def colors(self, colors: List[str]) -> None:
        self._colors = colors

    def go(self) -> None:
        super().go()
        for cell in self._cells:
            c_set_colors(cell.x, cell.y, self.color)
        if not self.completed:
            event_create(CAnimation(self.cells, self.colors, self.stage + 1))

    def __str__(self):
        return f"ANIMATION ({[str(c) for c in self.cells]}) {self.stage} => {self.max_stage}: {self.colors}"


class CSwap(Event):
    def __init__(self, cells: List[Point], stage: int = 0):
        super().__init__(cells, CellState.SWAP, stage)
        self._max_stage = ANIMATION_LENGTH
        event_create(CAnimation(self._cells, ["GREEN", "PURPLE"], stage))

    def go(self):
        super().go()
        if not self.completed:
            event_create(CSwap(self.cells, self.stage))
        else:
            c_complete_all_streaks()
            assert 2 == len(self.cells), f"ERROR: CSwap was asked to swap this: {self.cells}"
            c_swap_gems(tuple([cell for cell in self.cells]))


class CBirth(Event):
    def __init__(self, cells: List[Point], stage: int = 0):
        super().__init__(cells, CellState.BORN, stage)
        self._max_stage = ANIMATION_LENGTH
        event_create(CAnimation(self._cells, ["CYAN", "PURPLE"], stage))

    def go(self):
        super().go()
        if not self.completed:
            event_create(CBirth(self.cells, self.stage))
        else:
            c_complete_all_streaks()
            assert 1 == len(self.cells), f"ERROR: CBirth was asked to create this: {self.cells}"
            p = self.cells[0]
            c_set_gem(p.x,p.y,new_gem())

class CMatch(Event):
    def __init__(self, cells: List[Point], stage: int = 0):
        super().__init__(cells, CellState.MATCH, stage)
        event_create(CAnimation(self.cells, ["ORANGE", "PINK"], stage))

    def go(self):
        super().go()
        if not self.completed:
            event_create(CMatch(self.cells, self.stage))
        else:
            c_complete_all_streaks()
            c_swap_gems(tuple([self.cells[0], self.cells[1]]))


class CDeath(Event):
    def __init__(self, cells: List[Point]):
        super().__init__(cells, CellState.DYING)
        event_create(CAnimation(self.cells, ["RED", "WHITE"]))


# UTILITY FUNCTIONS

def new_gem() -> str:
    return random.choice(gems)


GLOBAL_CELL_MATRIX: CellMatrix = [[Cell(i, j, new_gem()) for j in range(MATRIX_HEIGHT)] for i in range(MATRIX_WIDTH)]


def valid_x(x) -> bool:
    return 0 <= x < MATRIX_WIDTH


def valid_y(y) -> bool:
    return 0 <= y < MATRIX_HEIGHT


def cm_cell(m: CellMatrix, x: int, y: int) -> Cell:
    return m[x][y]


def c_cell(x: int, y: int) -> Cell:
    return cm_cell(GLOBAL_CELL_MATRIX, x, y)


def c_set_state(x: int, y: int, state: CellState) -> None:
    global GLOBAL_CELL_MATRIX
    GLOBAL_CELL_MATRIX[x][y].state = state


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


def c_reset_color_matrix(fg: str, bg: str) -> None:
    for j in range(MATRIX_HEIGHT):
        for i in range(MATRIX_WIDTH):
            c_set_colors(i, j, fg, bg)


# GAME FUNCTIONS

def event_create(event: Event) -> None:
    GLOBAL_EVENT_QUEUE.append(event)


def event_go() -> Event:
    global DEFAULT_EVENT
    if len(GLOBAL_EVENT_QUEUE) > 0:
        event = GLOBAL_EVENT_QUEUE.popleft()
        event.go()
        return event
    else:
        c_reset_color_matrix("WHITE", "BLACK")
    return DEFAULT_EVENT


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


def c_matrix_fill() -> None:
    for _ in range(MATRIX_HEIGHT):
        for i in range(MATRIX_WIDTH):
            for j in range(MATRIX_HEIGHT):
                if c_state(i, j) == CellState.KILLED:
                    if j < (MATRIX_HEIGHT - 1):
                        c_set_gem(i, j, c_gem(i, j + 1))
                        c_set_gem(i, j + 1, new_gem())
                        event_create(CAnimation([Point(i, j),Point(i, j+1)], ["RED", "PINK"]))
                    else:
                        c_set_gem(i, j, new_gem())
                        event_create(CAnimation([Point(i, j)], ["RED", "PINK"]))


def c_update_from_streak(streak: FrozenSet[Point]) -> None:
    for p in streak:
        c_set_state(p.x, p.y, CellState.KILLED)


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


def c_complete_all_streaks() -> None:
    streaks = c_matrix_streaks()
    while len(streaks) > 0:
        c_update_from_streak(streaks[0])
        c_matrix_fill()
        streaks = c_matrix_streaks()


def c_possible_streaks() -> List[FrozenSet[Point]]:
    # assert False, "c_possible_streaks() UNIMPLEMENTED"
    candidates = set()
    c_complete_all_streaks()
    deltas = [Point(i, j) for i in range(-1, 2) for j in range(-1, 2) if abs(i) != abs(j)]
    points = [Point(i, j) for j in range(1, MATRIX_HEIGHT - 1) for i in range(1, MATRIX_WIDTH - 1)]
    for p in points:
        neighbors: List[Point] = [Point(p.x + d.x, p.y + d.y) for d in deltas if
                                  valid_x(p.x + d.x) and valid_y(p.y + d.y)]
        for n in neighbors:
            neighbor_switch_matrix: CellMatrix = deepcopy(GLOBAL_CELL_MATRIX)
            neighbor_switch_matrix = cm_swap_gems(neighbor_switch_matrix, tuple([p, n]))
            if len(cm_matrix_streaks(neighbor_switch_matrix)) > 0:
                candidates.add(frozenset([p, n]))
    return sorted([c for c in candidates])


def ij_to_window_xy(cx: int, cy: int) -> Tuple[int, int]:
    x = X_START + cx * X_BUFFER
    y = Y_START + cy * Y_BUFFER
    return x, y


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
        console.draw_frame(pmin.x - w_buffer, pmin.y - w_buffer, pmax.x - pmin.x + 3 * w_buffer,
                           pmax.y - pmin.y + 3 * w_buffer, str(i), clear=False)
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
                print(".", end="")
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
                            event_create(CSwap(list(streaks[s_num])))
                    else:
                        print(f"BAD KEY: {event}")


if __name__ == "__main__":
    main()
