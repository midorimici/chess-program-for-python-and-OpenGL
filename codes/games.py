'''ゲームの種類によって変わる駒の配置や名前、画像IDを記録したモジュール'''

from random import randint

from pieces import *


class Normal:
    '''通常のチェス'''
    # 盤面のサイズ
    size = 8
    # キャスリングの有無
    castling = True
    # プロモーション先
    promote2 = [Knight, Bishop, Rook, Queen]
    # 駒の配置
    placers = {1: [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook],
        2: [Pawn] * size}
    # 画像IDの割り当て
    ID = {}
    for rk in placers:
        for fl in range(size):
            if placers[rk][fl] is not None:
                ID['W' + placers[rk][fl].abbr] = size * rk + fl
                ID['B' + placers[rk][fl].abbr] = -(size * rk + fl)


class Chess960:
    '''チェス960'''
    # 盤面のサイズ
    size = 8
    # キャスリングの有無
    castling = True
    # プロモーション先
    promote2 = [Knight, Bishop, Rook, Queen]
    # 駒の配置
    placers = {1: [None] * size,
        2: [Pawn] * size}
    
    ID = {}
    
    def __init__(self):
        # 駒の配置の決定
        pos_id = randint(0, 959)
        while pos_id == 518:
            pos_id = randint(0, 959)
        krn = [
            [Knight, Knight, Rook, King, Rook],
            [Knight, Rook, Knight, King, Rook],
            [Knight, Rook, King, Knight, Rook],
            [Knight, Rook, King, Rook, Knight],
            [Rook, Knight, Knight, King, Rook],
            [Rook, Knight, King, Knight, Rook],
            [Rook, Knight, King, Rook, Knight],
            [Rook, King, Knight, Knight, Rook],
            [Rook, King, Knight, Rook, Knight],
            [Rook, King, Rook, Knight, Knight]
        ]

        q, r = pos_id//4, pos_id%4
        self.placers[1][2*r + 1] = Bishop

        q, r = q//4, q%4
        self.placers[1][2*r] = Bishop

        q, r = q//6, q%6
        for i in range(self.size):
            if self.placers[1][i] is None:
                if i == r:
                    self.placers[1][i] = Queen
                    break
            else: r += 1
        
        for piece in krn[q]:
            self.placers[1][self.placers[1].index(None)] = piece
            
        # 画像IDの割り当て
        for rk in self.placers:
            for fl in range(self.size):
                if self.placers[rk][fl] is not None:
                    self.ID['W' + self.placers[rk][fl].abbr] = self.size * rk + fl
                    self.ID['B' + self.placers[rk][fl].abbr] = -(self.size * rk + fl)


class withUnicorn:
    '''キングサイドのナイトがユニコーンになったチェス'''
    # 盤面のサイズ
    size = 8
    # キャスリングの有無
    castling = True
    # プロモーション先
    promote2 = [Knight, Bishop, Rook, Queen, Unicorn]
    # 駒の配置
    placers = {1: [Rook, Knight, Bishop, Queen, King, Bishop, Unicorn, Rook],
        2: [Pawn] * size}
    # 画像IDの割り当て
    ID = {}
    for rk in placers:
        for fl in range(size):
            if placers[rk][fl] is not None:
                ID['W' + placers[rk][fl].abbr] = size * rk + fl
                ID['B' + placers[rk][fl].abbr] = -(size * rk + fl)


# ゲーム選択画面に表示するゲーム
game_dict = {0: (Normal, Chess960, withUnicorn)}