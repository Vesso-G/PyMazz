from random import randint
from random import choice
from tkinter import Tk, Canvas
from ctypes import windll


def separated(p1, p2, sep):
    """
    :param p1: The square being checked as a start or end point in the maze
    :param p2: The list of end points for the maze
    :param sep: The distance away the end points must be away from each other
    :return:
    """

    if not p2:
        return True
    else:
        return abs(p1[0] - p2[0][0]) + abs(p1[1] - p2[0][1]) > sep


# Creates an initial maze with random start and end points, having separate horizontal and vertical matrices
def create_maze_matrices(x, y, sep):
    """
    :param x: The number of horizontal spaces
    :param y: The number of vertical spaces
    :param sep: The distance away the start and end points must be
    :return: Two matrices representing vertical and horizontal gates, being shown as a 0 for open and 1 for closed
    """

    vertical = [[1] * (x + 1) for _ in range(y)]    # Initialising the vertical gates
    horizontal = [[1] * x for _ in range(y + 1)]    # Initialising the horizontal gates

    end_points = []

    while len(end_points) < 2:
        side = randint(1, 4)

        if side == 1:
            rnd = randint(0, x - 1)
            if [0, rnd] not in end_points and separated([0, rnd], end_points, sep):
                horizontal[0][rnd] = 0
                end_points.append([0, rnd])

        elif side == 2:
            rnd = randint(0, y - 1)
            if [rnd, x - 1] not in end_points and separated([rnd, x - 1], end_points, sep):
                vertical[rnd][x] = 0
                end_points.append([rnd, x - 1])

        elif side == 3:
            rnd = randint(0, x - 1)
            if [y - 1, rnd] not in end_points and separated([y - 1, rnd], end_points, sep):
                horizontal[y][rnd] = 0
                end_points.append([y - 1, rnd])

        else:
            rnd = randint(0, y - 1)
            if [rnd, 0] not in end_points and separated([rnd, 0], end_points, sep):
                vertical[rnd][0] = 0
                end_points.append([rnd, 0])


    return horizontal, vertical, end_points

# Checks which gates can be opened legally, to avoid travelling on previous square, leaving the maze or opening spaces
def check_valid_openings(h, v, pos, travelled):
    """
    :param h: The horizontal gate matrix
    :param v: The vertical gate matrix
    :param pos: The position being looked at, (y, x)
    :param travelled: A set of which squares have been travelled through already that mustn't be re-used
    :return: A list representing which directions are valid, [UP, DOWN, LEFT, RIGHT], where 1 is valid and 0 is invalid
    """

    valid = [1, 1, 1, 1]    # [UP, DOWN, LEFT, RIGHT]

    y, x = pos

    # The path cannot travel back onto any squares it has previously went through
    if (y - 1, x) in travelled:
        valid[0] = 0
    if (y + 1, x) in travelled:
        valid[1] = 0
    if (y, x - 1) in travelled:
        valid[2] = 0
    if (y, x + 1) in travelled:
        valid[3] = 0

    # If on the left-most column left isn't a valid move
    if x == 0:
        valid[2] = 0
    # If on the right-most column right isn't a valid move
    elif x == len(h[0]) - 1:
        valid[3] = 0
    # If on the up-most row up isn't a valid move
    if y == 0:
        valid[0] = 0
    # If on the down-most row down isn't a valid move
    elif y == len(v) - 1:
        valid[1] = 0

    # Sorry for anyone reading this bit, its ugly but it works...
    values = []   # Open/close values of certain gates, 0 for closed, 1 for open and 2 for out-of-bounds

    #   _|_|_
    #   _|_|_
    #    | |
    # Basically I'm checking the lines surrounding the square in a grid as shown above. By checking which of these
    # gates are open or closed or out of bounds I can determine whether going a particular direction will make an "open"
    # space which I don't want, "open" as in any 2x2 area (anything not a 1xN or Nx1). Due to index errors I can't just
    # initialise the list straight away, and need to check each individually to see if the gate is out of bounds, except
    # for the lines in the middle which should never be out of bounds, which would only occur if the square itself was
    # out of bounds.

    # Top left and right vertical lines
    if valid[0]:
        values.append(v[y-1][x])
        values.append(v[y-1][x+1])
    else:
        values.append(2)
        values.append(2)

    # Middle vertical lines
    values.append(v[y][x])
    values.append(v[y][x+1])

    # Bottom left and right vertical lines
    if valid[1]:
        values.append(v[y+1][x])
        values.append(v[y+1][x+1])
    else:
        values.append(2)
        values.append(2)

    # Top right horizontal line
    if valid[2]:
        values.append(h[y][x-1])
    else:
        values.append(2)

    # Top middle horizontal line
    values.append(h[y][x])

    # Top left horizontal line
    if valid[3]:
        values.append(h[y][x+1])
    else:
        values.append(2)

    # Bottom right horizontal line
    if valid[2]:
        values.append(h[y+1][x-1])
    else:
        values.append(2)

    # Bottom middle horizontal line
    values.append(h[y+1][x])

    # Bottom left horizontal line
    if valid[3]:
        values.append(h[y+1][x+1])
    else:
        values.append(2)

    for i in range(len(values)):
        values[i] = 1 - values[i]

    # If going up is illegal
    if values[0] and values[2] and values[6] or values[1] and values[8] and values[3] or values[7]:
        valid[0] = 0
    # If going down is illegal
    if values[2] and values[9] and values[4] or values[3] and values[11] and values[5] or values[10]:
        valid[1] = 0
    # If going left is illegal
    if values[6] and values[0] and values[7] or values[9] and values[4] and values[10] or values[2]:
        valid[2] = 0
    # If going right is illegal
    if values[7] and values[1] and values[8] or values[10] and values[11] and values[5] or values[3]:
        valid[3] = 0

    return valid

# Attempts to connect two points avoiding creating "open" spaces or covering already travelled spaces
def path_between_points(h, v, p1, p2, travelled):
    """
    :param h: The horizontal gate matrix
    :param v: The vertical gate matrix
    :param p1: The starting square
    :param p2: The ending square
    :param travelled: A list to add each square passed through into
    :return: The new gate matrices
    """

    square = p1             # The current square the path is at
    valid_moves = True      # Whether there is at least one valid move

    travelled.add(tuple(square))

    while square != p2 and valid_moves:     # Loops, adding to the path, until reaching p2 or no valid moves

        possible = []       # A list of which moves are valid where 0 is up, 1 is down, 2 is left and 3 is right
        valid = check_valid_openings(h, v, square, travelled)  # Which directions are valid moves

        # Loops through each probability and sets it to 0 if it's an invalid move
        for i in range(4):
            if valid[i]:
                possible.append(i)

        if not possible:
            valid_moves = False

        else:
            direction = choice(possible)            # Random value representing a valid direction

            # If up
            if direction == 0:
                h[square[0]][square[1]] = 0         # Open gate
                square[0] -= 1                      # Move square
            # If down
            elif direction == 1:
                h[square[0] + 1][square[1]] = 0     # Open gate
                square[0] += 1                      # Move square
            # If left
            elif direction == 2:
                v[square[0]][square[1]] = 0         # Open gate
                square[1] -= 1                      # Move square
            # Else right
            else:
                v[square[0]][square[1] + 1] = 0     # Open gate
                square[1] += 1                      # Move square

        travelled.add(tuple(square))

    return h, v

class Draw:

    def __init__(self, rt, scale, dim):

        self.scale = scale - scale % 4          # Size of each square
        self.width = self.scale * 0.3    # Width of the lines
        self.dim = dim              # Dimensions of the maze [y, x] being number of columns and rows

        # The initialised vertical and horizontal matrices, as well as a list containing the start and end points of the maze
        self.h, self.v, self.end_points = create_maze_matrices(dim[1], dim[0], sum(dim) / 3)

        self.travelled_squares = set()      # Any squares that have been travelled over will go here

        # The initial "solution" path, this may not be the actual solution path, but it will be close and other branches
        # will complete the maze if not
        path_between_points(self.h, self.v, self.end_points[0], self.end_points[1], self.travelled_squares)

        # Loops through picking a random square already travelled on and attempts to connect it to another random point
        # until the entire maze is complete
        while len(self.travelled_squares) < 1 * self.dim[0] * self.dim[1]:
            path_between_points(self.h, self.v, list(choice(list(self.travelled_squares))), [randint(0, dim[0] - 1), randint(0, dim[1] - 1)], self.travelled_squares)

        self.rt = rt      # Tkinter root object
        # self.rt.attributes(fullscreen=True)

        # Canvas initialisation
        self.c = Canvas(self.rt, width=(dim[1] + 1) * self.scale, height=(dim[0] + 1) * self.scale, bg='grey30', highlightthickness=0)
        self.c.pack()

        self.player_pos = self.end_points[0]

        # Draw maze
        self.display_maze()

    def display_maze(self):

        # Draws the horizontal lines with various offsets based on the border around the maze and line width
        for i in range(len(self.h)):
            for j in range(len(self.h[0])):
                if self.h[i][j]:
                    x0 = (j + 0.5) * self.scale - self.width / 2
                    y0 = (i + 0.5) * self.scale
                    x1 = x0 + self.scale + self.width
                    y1 = y0
                    self.c.create_line(x0, y0, x1, y1, width=self.width)

        # Draws the vertical lines with various offsets based on the border around the maze and line width
        for i in range(len(self.v)):
            for j in range(len(self.v[0])):
                if self.v[i][j]:
                    x0 = (j + 0.5) * self.scale
                    y0 = (i + 0.5) * self.scale - self.width / 2
                    x1 = x0
                    y1 = y0 + self.scale + self.width
                    self.c.create_line(x0, y0, x1, y1, width=self.width)

def run():

    # Obtaining screen dimensions
    # screen_dim = windll.user32.GetSystemMetrics
    # screen_dim = [screen_dim(0), screen_dim(1)]

    # Creates the tkinter object, passing it to the Draw object, to then create and draw the maze
    rt = Tk()

    # Creating random maze dimensions and determining scale to fit full screen
    # y = randint(3, 100)
    # x = randint(3, 100)
    #
    # scale = screen_dim[1] * 0.9 / y
    #
    # if screen_dim[0] * 0.9 / x < scale:
    #     scale = screen_dim[0] * 0.9 / x

    y, x = 15, 20
    scale = 50

    Draw(rt, scale, (y, x))
    rt.mainloop()

if __name__ == "__main__":
    run()
