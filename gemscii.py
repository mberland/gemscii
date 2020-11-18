# * % . % . # . . . . # *
# * * % % . . % . # * # *
# # # * . * * . . X % X X
# . X . # * * % # . X # #
# . . X X . # # % X X # .
# % . % % X * % X # * % #
# * X . % # * * # X . X X

import random
from collections import defaultdict

gems = "ABCDE"
width = 10
height = 5


def valid_x(x):
    return 0 <= x < width


def valid_y(y):
    return 0 <= y < height


def init_matrix():
    return [[random.choice(gems) for j in range(height)] for i in range(width)]


def meta_matrix():
    return {i: {j: {} for j in range(height)} for i in range(width)}


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
    for j in range(height):
        new_line()
        new_line()
        for i in range(width):
            display(c=elt(m, i, j), i=i, j=j)
    new_line()


def print_meta(m,meta,streaks):
    assert False, "UNIMPLEMENTED"


def cell_options(m):
    streaks = set()
    deltas = [(i, j) for i in range(-1, 2) for j in range(-1, 2) if i != 0 or j != 0]
    cells = [(i, j) for j in range(height) for i in range(width)]
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


matrix = init_matrix()
meta = meta_matrix()
# print_matrix(matrix)
streaks = cell_options(matrix)
print_streaks(matrix, streaks)
