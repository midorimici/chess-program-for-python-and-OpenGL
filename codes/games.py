'''ゲームの種類によって変わる駒の配置や名前、画像IDを記録したモジュール'''

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


class withUnicorn:
    '''通常のチェス'''
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
game_dict = {0: (Normal, withUnicorn)}