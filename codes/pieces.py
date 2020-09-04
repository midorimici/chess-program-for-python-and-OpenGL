W = "W"
B = "B"


class Piece:
    def __init__(self, color):
        self.color = color
        self.name = color + self.abbr

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def rider(self, x, y, gameboard, color, intervals):
        """repeats the given interval until another piece is run into. 
        if that piece is not of the same color, that square is added and
         then the list is returned"""
        answers = []
        for xint, yint in intervals:
            xtemp, ytemp = x+xint, y+yint
            while self.is_in_bounds(xtemp, ytemp):

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

    def is_in_bounds(self, x, y):
        "checks if a position is on the board"
        if x >= 0 and x < 8 and y >= 0 and y < 8:
            return True
        return False

    def no_conflict(self, gameboard, initialColor, x, y):
        "checks if a single position poses no conflict to the rules of chess"
        if self.is_in_bounds(x, y) and (((x, y) not in gameboard) or gameboard[(x, y)].color != initialColor):
            return True
        return False


chess_cardinals = [(1, 0), (0, 1), (-1, 0), (0, -1)]
chess_diagonals = [(1, 1), (-1, 1), (1, -1), (-1, -1)]


def leaper(x, y, int1, int2):
    """sepcifically for the rook, permutes the values needed around a position for no_conflict tests"""
    return [(x+int1, y+int2), (x-int1, y+int2), (x+int1, y-int2), (x-int1, y-int2), (x+int2, y+int1), (x-int2, y+int1), (x+int2, y-int1), (x-int2, y-int1)]


def king_list(x, y):
    return [(x+1, y), (x+1, y+1), (x+1, y-1), (x, y+1), (x, y-1), (x-1, y), (x-1, y+1), (x-1, y-1)]


class Knight(Piece):
    abbr = 'N'

    def available_moves(self, x, y, gameboard):
        return [(xx, yy) for xx, yy in leaper(x, y, 2, 1) if self.no_conflict(gameboard, self.color, xx, yy)]


class Unicorn(Piece):
    abbr = 'Un'

    def available_moves(self, x, y, gameboard):
        return self.rider(x, y, gameboard, self.color, leaper(0, 0, 1, 2))


class Rook(Piece):
    abbr = 'R'

    def available_moves(self, x, y, gameboard):
        return self.rider(x, y, gameboard, self.color, chess_cardinals)


class Bishop(Piece):
    abbr = 'B'

    def available_moves(self, x, y, gameboard):
        return self.rider(x, y, gameboard, self.color, chess_diagonals)


class Queen(Piece):
    abbr = 'Q'

    def available_moves(self, x, y, gameboard):
        return self.rider(x, y, gameboard, self.color, chess_cardinals+chess_diagonals)


class King(Piece):
    abbr = 'K'

    def available_moves(self, x, y, gameboard):
        return [(xx, yy) for xx, yy in king_list(x, y) if self.no_conflict(gameboard, self.color, xx, yy)]


class Pawn(Piece):
    abbr = 'P'

    def available_moves(self, x, y, gameboard):
        self.direction = 1 if self.color == 'W' else -1
        answers = []
        if (x+1, y+self.direction) in gameboard and self.no_conflict(gameboard, self.color, x+1, y+self.direction):
            answers.append((x+1, y+self.direction))
        if (x-1, y+self.direction) in gameboard and self.no_conflict(gameboard, self.color, x-1, y+self.direction):
            answers.append((x-1, y+self.direction))
        if (x, y+self.direction) not in gameboard:
            # the condition after the and is to make sure the non-capturing movement (the only fucking one in the game) is not used in the calculation of checkmate
            answers.append((x, y+self.direction))
        if (((self.color == W and y == 1)
             or (self.color == B and y == 6))
                and (x, y + 1*self.direction) not in gameboard
                and (x, y + 2*self.direction) not in gameboard):
            answers.append((x, y + 2*self.direction))
        return answers


piece_names = [Knight, Rook, Bishop, Queen, King, Pawn, Unicorn]

# 画像IDの割り当て
piece_ID = {}
for i, piece in enumerate(piece_names):
    piece_ID['W' + piece.abbr] = i + 1
    piece_ID['B' + piece.abbr] = -(i + 1)
