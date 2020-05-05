WHITE = "W"
BLACK = "B"


class Piece:

    def __init__(self, color, name):
        self.name = name
        self.position = None
        self.color = color

    def is_valid(self, startpos, endpos, color, gameboard):
        if endpos in self.available_moves(startpos[0], startpos[1], gameboard, color=color):
            return True
        return False

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def available_moves(self, x, y, gameboard, color):
        print("ERROR: no movement for base class")

    def AdNauseum(self, x, y, gameboard, color, intervals):
        """repeats the given interval until another piece is run into. 
        if that piece is not of the same color, that square is added and
         then the list is returned"""
        answers = []
        for xint, yint in intervals:
            xtemp, ytemp = x+xint, y+yint
            while self.isInBounds(xtemp, ytemp):
                #print(str((xtemp,ytemp))+"is in bounds")

                target = gameboard.get((xtemp, ytemp), None)
                if target is None:
                    answers.append((xtemp, ytemp))
                elif target.color != color:
                    answers.append((xtemp, ytemp))
                    break
                else:
                    break

                xtemp, ytemp = xtemp + xint, ytemp + yint
        return answers

    def isInBounds(self, x, y):
        "checks if a position is on the board"
        if x >= 0 and x < 8 and y >= 0 and y < 8:
            return True
        return False

    def noConflict(self, gameboard, initialColor, x, y):
        "checks if a single position poses no conflict to the rules of chess"
        if self.isInBounds(x, y) and (((x, y) not in gameboard) or gameboard[(x, y)].color != initialColor):
            return True
        return False


chessCardinals = [(1, 0), (0, 1), (-1, 0), (0, -1)]
chessDiagonals = [(1, 1), (-1, 1), (1, -1), (-1, -1)]


def knightList(x, y, int1, int2):
    """sepcifically for the rook, permutes the values needed around a position for noConflict tests"""
    return [(x+int1, y+int2), (x-int1, y+int2), (x+int1, y-int2), (x-int1, y-int2), (x+int2, y+int1), (x-int2, y+int1), (x+int2, y-int1), (x-int2, y-int1)]


def kingList(x, y):
    return [(x+1, y), (x+1, y+1), (x+1, y-1), (x, y+1), (x, y-1), (x-1, y), (x-1, y+1), (x-1, y-1)]


class Knight(Piece):
    abbr = 'N'

    def available_moves(self, x, y, gameboard, color=None):
        if color is None:
            color = self.color
        return [(xx, yy) for xx, yy in knightList(x, y, 2, 1) if self.noConflict(gameboard, color, xx, yy)]


class Rook(Piece):
    abbr = 'R'

    def available_moves(self, x, y, gameboard, color=None):
        if color is None:
            color = self.color
        return self.AdNauseum(x, y, gameboard, color, chessCardinals)


class Bishop(Piece):
    abbr = 'B'

    def available_moves(self, x, y, gameboard, color=None):
        if color is None:
            color = self.color
        return self.AdNauseum(x, y, gameboard, color, chessDiagonals)


class Queen(Piece):
    abbr = 'Q'

    def available_moves(self, x, y, gameboard, color=None):
        if color is None:
            color = self.color
        return self.AdNauseum(x, y, gameboard, color, chessCardinals+chessDiagonals)


class King(Piece):
    abbr = 'K'

    def available_moves(self, x, y, gameboard, color=None):
        if color is None:
            color = self.color
        return [(xx, yy) for xx, yy in kingList(x, y) if self.noConflict(gameboard, color, xx, yy)]


class Pawn(Piece):
    abbr = 'P'

    def __init__(self, color, name, direction):
        self.name = name
        self.color = color
        # of course, the smallest piece is the hardest to code. direction should be either 1 or -1, should be -1 if the pawn is traveling "backwards"
        self.direction = direction

    def available_moves(self, x, y, gameboard, color=None):
        if color is None:
            color = self.color
        answers = []
        if (x+1, y+self.direction) in gameboard and self.noConflict(gameboard, color, x+1, y+self.direction):
            answers.append((x+1, y+self.direction))
        if (x-1, y+self.direction) in gameboard and self.noConflict(gameboard, color, x-1, y+self.direction):
            answers.append((x-1, y+self.direction))
        if (x, y+self.direction) not in gameboard:
            # the condition after the and is to make sure the non-capturing movement (the only fucking one in the game) is not used in the calculation of checkmate
            answers.append((x, y+self.direction))
        if (((self.color == WHITE and y == 1)
             or (self.color == BLACK and y == 6))
                and (x, y + 1 * self.direction) not in gameboard
                and (x, y + 2 * self.direction) not in gameboard):
            answers.append((x, y + 2 * self.direction))
        return answers


piece_names = [Knight, Rook, Bishop, Queen, King, Pawn]

# 画像IDの割り当て
piece_ID = {}
for i, piece in enumerate(piece_names):
    piece_ID['W' + piece.abbr] = i + 1
    piece_ID['B' + piece.abbr] = -(i + 1)
