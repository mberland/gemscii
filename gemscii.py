# * % . % . # . . . . # *
# * * % % . . % . # * # *
# # # * . * * . . X % X X
# . X . # * * % # . X # #
# . . X X . # # % X X # .
# % . % % X * % X # * % #
# * X . % # * * # X . X X

import tcod
import random


from collections import defaultdict

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
    return [[random.choice(gems) for j in range(MATRIX_HEIGHT)] for i in range(MATRIX_WIDTH)]


def meta_matrix():
    return {i: {j: {} for j in range(MATRIX_HEIGHT)} for i in range(MATRIX_WIDTH)}


# print(meta_matrix()[width - 1][height - 1])


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


def print_matrix(m):
    new_line = lambda : display()
    for j in range(MATRIX_HEIGHT):
        new_line()
        new_line()
        for i in range(MATRIX_WIDTH):
            display(c=elt(m, i, j), i=i, j=j)
    new_line()


def print_meta(m,meta,streaks):
    assert False, "UNIMPLEMENTED"


def cell_options(m):
    streaks = set()
    deltas = [(i, j) for i in range(-1, 2) for j in range(-1, 2) if i != 0 or j != 0]
    cells = [(i, j) for j in range(MATRIX_HEIGHT) for i in range(MATRIX_WIDTH)]
    for cell in cells:
        for delta in deltas:
            wins = 0
            cx = cell[0]
            cy = cell[1]
            dx = delta[0]
            dy = delta[1]
            ax = dx
            ay = dy
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
                # output_matrix[elt_id(cx,cy)] = cell_type + str(cx)+str(cy)
    streaks = [x for x in streaks if not any(x.issubset(s) for s in streaks if s != x)]
    #
    # for s in streaks:
    #     print(sorted(s))
    return streaks


def print_streaks(m, sx):
    for streak in sx:
        for cell in sorted(streak, key=lambda e: e[1]):
            x = cell[1]
            y = cell[2]
            m[x][y] = elt(m, x, y) + "!"
    print_matrix(m)

#
# matrix = init_matrix()
# meta = meta_matrix()
# # print_matrix(matrix)
# streaks = cell_options(matrix)
# print_streaks(matrix, streaks)


def fill_matrix(m: object) -> object:
    for i in range(MATRIX_WIDTH):
        for j in range(MATRIX_HEIGHT):
            if m[i][j] == "#":
                if j < (MATRIX_HEIGHT - 1):
                    m[i][j] = m[i][j+1]
                    m[i][j+1] = new_gem()
                else:
                    m[i][j] = new_gem()
    return m


def update_from_streak(m: object, streak: object) -> object:
    for cell in streak:
        cx = cell[1]
        cy = cell[2]
        m[cx][cy] = "#"
    return m


def update_matrix(m: object) -> object:
    streaks = cell_options(m)
    if len(streaks) > 0:
        relevant_streak = random.choice(streaks)
        return update_from_streak(m,relevant_streak)
    else:
        return m


WINDOW_WIDTH = MATRIX_WIDTH * 4
WINDOW_HEIGHT = MATRIX_HEIGHT * 4 #= 40, 24 # Console width and height in tiles.


def tcod_matrix(console, m):
    BUFFER_X: int = int(WINDOW_WIDTH / (1 + MATRIX_WIDTH))
    BUFFER_Y: int = int(WINDOW_HEIGHT / (1 + MATRIX_HEIGHT))
    for j in range(MATRIX_HEIGHT):
        for i in range(MATRIX_WIDTH):
            cx = 2 * BUFFER_X + i * BUFFER_X
            cy = BUFFER_Y + j * BUFFER_Y
            ce = m[i][j]
            console.print(x=cx, y=cy, string=ce)


def main() -> None:
    tileset = tcod.tileset.load_tilesheet("curses_square_16x16_b.png", 16, 16, tcod.tileset.CHARMAP_CP437)

    console = tcod.Console(WINDOW_WIDTH, WINDOW_HEIGHT)
    matrix = init_matrix()
    meta = meta_matrix()
    print_matrix(matrix)
    
    with tcod.context.new(columns=console.width, rows=console.height, tileset=tileset) as context:
        while True:  # Main loop, runs until SystemExit is raised.
            console.clear()
            # tcod_matrix(console,matrix)
            # # console.print(x=0, y=0, string="Hello World!")
            # context.present(console)  # Show the console.

            for event in tcod.event.wait():
                # context.convert_event(event)  # Sets tile coordinates for mouse events.
                if event.type == "KEYDOWN":
                    # print_matrix(matrix)
                    # print(event)
                    console.clear()
                    if event.sym == tcod.event.K_d:
                        matrix = update_matrix(matrix)
                    if event.sym == tcod.event.K_a:
                        matrix = fill_matrix(matrix)
                    if event.sym == tcod.event.K_r:
                        matrix = init_matrix()
                    tcod_matrix(console,matrix)
                    context.present(console)  # Show the console.
                if event.type == "QUIT":
                    raise SystemExit()
        # The window will be closed after the above with-block exits.


if __name__ == "__main__":
    main()
