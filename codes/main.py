import sys
from copy import copy
from time import sleep
from math import pi, sin

from OpenGL.GL import *
from OpenGL.GLUT import *
import pygame

from utils import *
from games import *
from pieces import *

WSIZE = 720     # 画面サイズ

opponent = {W: B, B: W}

# 音声の設定
pygame.mixer.init()
snd = pygame.mixer.Sound
# 各効果音の設定
select_snd = snd('../sounds/select.wav')
move_snd = snd('../sounds/move.wav')

class Game:
    def __init__(self):
        self.playersturn = W
        self.gameboard = {}
        self.kind = None

        # アンパッサン
        self.advanced2_pos = None
        # プロモーション
        self.prom = False
        # キャスリング
        # キャスリングのポテンシャルが残っているか
        self.can_castling = {'W': [True, True], 'B': [True, True]}
        # キャスリングするかどうかをプレイヤーに確認するか
        self.confirm_castling = False
        # キャスリングできる状態にあるか
        self.do_castling = False

        # マウスポインタの位置
        self.mousepos = [-1.0, -1.0]
        # 行先の指定
        self.select_dest = False
        # 始点・終点
        self.startpos, self.endpos = (None, None), (None, None)
        # アニメーション
        self.moving = False
        self.time = 1

        self.glmain()

    def after_deciding_kind(self):
        '''ゲーム種類決定後の処理'''
        # 駒の配置
        self.place_pieces()
        # 画像の設定
        for name, num in self.kind.ID.items():
            set_img(name, name[0], num)

    def place_pieces(self):
        for fl in range(self.kind.size):
            for rk in self.kind.placers:
                # None を指定すれば駒が置かれることはなく次のマスへ進む
                if self.kind.placers[rk][fl] is not None:
                    # 白の駒
                    self.gameboard[(fl, rk - 1)] \
                        = self.kind.placers[rk][fl]('W')
                    # 黒の駒
                    self.gameboard[(fl, self.kind.size - rk)] \
                        = self.kind.placers[rk][fl]('B')

    def main(self):
        startpos, endpos = self.startpos, self.endpos
        if None not in startpos + endpos:
            try:
                target = self.gameboard[startpos]
            except:
                target = None

            if target and target.color == self.playersturn:

                # 相手のポーンが2歩進んだ
                if target.abbr == 'P':
                    if endpos[1] == startpos[1] + 2*target.direction:
                        self.advanced2_pos = endpos
                    else:
                        self.advanced2_pos = None

                # キングが動いた
                if target.name == 'WK':
                    self.can_castling['W'] = [False, False]
                if target.name == 'BK':
                    self.can_castling['B'] = [False, False]
                # ルークが動いた
                if target.name == 'WR':
                    if startpos[0] == 0:
                        self.can_castling['W'][0] = False
                    if startpos[0] == 7:
                        self.can_castling['W'][1] = False
                if target.name == 'BR':
                    if startpos[0] == 0:
                        self.can_castling['B'][0] = False
                    if startpos[0] == 7:
                        self.can_castling['B'][1] = False

                self.renew_gameboard(startpos, endpos, self.gameboard)
                self.promotion(target, endpos)
                if self.is_check(target.color, self.gameboard):
                    print(f"{target.color} player is in check")
                if self.cannot_move(target.color, self.gameboard):
                    if self.is_check(target.color, self.gameboard):
                        print(f"Checkmate! {opponent[target.color]} player won!")
                        sys.exit()
                    else:
                        print("Stalemate! It's draw.")
                        sys.exit()
                if self.playersturn == B:
                    self.playersturn = W
                else:
                    self.playersturn = B

    def valid_moves(self, piece, startpos, gameboard):
        '''
        動ける位置を出力．味方駒上には移動不可．

        Parameters
        ----------
        piece : obj
            駒．
        startpos : tuple > (int, int)
            開始位置．絶対座標．
        gameboard : dict > {(int, int): obj, ...}
            盤面．

        Returns
        -------
        result : list > [(int, int), ...]
        '''
        result = piece.available_moves(*startpos, gameboard)
        # アンパッサン
        self.en_passant = False
        for endpos in ([(i, 2) for i in range(8)] + [(i, 5) for i in range(8)]):
            if self.en_passant_requirements(piece, startpos, endpos):
                self.en_passant = True
                result += [endpos]
        # キャスリング
        for endpos in [(2, 0), (6, 0), (2, 7), (6, 7)]:
            if self.castling_requirements(piece, endpos, 0, gameboard):
                result += [endpos]
                self.do_castling = True
            if self.castling_requirements(piece, endpos, 1, gameboard):
                result += [endpos]
                self.do_castling = True
        # チェック回避のため動き縛り
        result_tmp = copy(result)
        for endpos in result_tmp:
            gameboard_tmp = copy(gameboard)
            self.renew_gameboard(startpos, endpos, gameboard_tmp)
            if self.is_check(piece.color, gameboard_tmp):
                result.remove(endpos)
        return result

    def en_passant_requirements(self, piece, startpos, endpos):
        '''
        アンパッサンの条件を満たすとき True を返す

        Parameters
        ----------
        piece : obj
            動かす駒．
        startpos, endpos : tuple > (int, int)
            開始位置，終了位置．

        Returns
        -------
        bool
        '''
        return (piece.abbr == 'P'
            and self.advanced2_pos
            and startpos[1] == endpos[1] - piece.direction
            and startpos[1] == self.advanced2_pos[1]
            and endpos[1] == self.advanced2_pos[1] + piece.direction
            and abs(startpos[0] - endpos[0]) == 1
            and abs(startpos[0] - self.advanced2_pos[0]) == 1
            and endpos[0] == self.advanced2_pos[0])

    def promotion(self, piece, endpos):
        '''
        プロモーションできるとき，True

        Parameters
        ----------
        piece : obj
            駒．
        endpos : tuple > (int, int)
            終了位置．

        Returns
        -------
        bool
        '''
        if (piece.name == 'WP' and endpos[1] == 7
                or piece.name == 'BP' and endpos[1] == 0):
            self.prom = True

    def castling_requirements(self, piece, endpos, side, gameboard):
        '''
        キャスリングの条件を満たすとき，True
        side == 0 -> aファイル側
        side == 1 -> hファイル側

        Parameters
        ----------
        piece : obj
            駒．キングでなければ return は False．
        endpos : tuple > (int, int)
            終了位置．絶対座標．
        side : int > 0, 1
            0 -- クイーンサイド
            1 -- キングサイド
        gameboard : dict > {(int, int): obj, ...}
            盤面．

        Returns
        -------
        bool
        '''
        size = self.kind.size

        rook_init_pos = [pos for pos, piece in enumerate(self.kind.placers[1]) if piece == Rook]
        king_init_pos = self.kind.placers[1].index(King)

        def create_tmp_board(startpos_y, endpos):
            '''
            キングの通過するマスが攻撃されていないことを確認するために，
            キングがそのマスに動いたときに攻撃されるかを見るための
            仮の盤面を出力する

            Parameters
            ----------
            startpos_y : int
                開始位置y座標．
            endpos : tuple > (int, int)
                終了位置．絶対座標．

            Returns
            -------
            gameboard_tmp : dict > {(int, int): obj, ...}
            '''
            gameboard_tmp = copy(gameboard)
            if (king_init_pos, startpos_y) in gameboard_tmp:
                gameboard_tmp[endpos] = gameboard_tmp[(king_init_pos, startpos_y)]
                del gameboard_tmp[(king_init_pos, startpos_y)]
            return gameboard_tmp

        def path_is_not_attacked(startpos_y, king_route):
            '''
            キングが通るマスのどれかが相手の駒に攻撃されていれば False を返す

            Parameters
            ----------
            startpos_y : int
                開始位置y座標．
            king_route : list > [int, ...]
                キングが通る位置x座標のリスト．

            Returns
            -------
            bool
            '''
            for pos in king_route:
                if self.is_check(piece.color, create_tmp_board(startpos_y, (pos, startpos_y))):
                    return False
            return True

        common_req = (self.can_castling[piece.color][side]  # キャスリングに関与する駒が一度も動いていない
                      and not self.is_check(piece.color, gameboard))  # キングがチェックされていない
        # 白のキャスリング
        if piece.color == 'W':
            piece_req = (piece.name == 'WK'
                         and (rook_init_pos[side], 0) in gameboard
                         and gameboard[(rook_init_pos[side], 0)].name == 'WR')
            gameboard_tmp = copy(gameboard)
            # キャスリングに関与するキングとルークは除外して考える
            if (king_init_pos, 0) in gameboard_tmp:
                del gameboard_tmp[(king_init_pos, 0)]
            if (rook_init_pos[side], 0) in gameboard_tmp:
                del gameboard_tmp[(rook_init_pos[side], 0)]
            # クイーンサイド
            if side == 0:
                # キングとルークの通過するマス
                king_route = list(range(2, king_init_pos)) + list(range(2, king_init_pos, -1))
                rook_route = list(range(3, rook_init_pos[side])) + list(range(3, rook_init_pos[side], -1))
                special_req = (endpos == (2, 0)
                                # キングとルークの通過するマスに駒がない
                                and not any((x, 0) in gameboard_tmp
                                    for x in king_route + rook_route)
                                # キングが通過するマスが敵に攻撃されていない
                                and path_is_not_attacked(0, list(x for x in range(2, king_init_pos)))
                                )
            # キングサイド
            if side == 1:
                # キングとルークの通過するマス
                king_route = list(range(size - 2, king_init_pos)) + list(range(size - 2, king_init_pos, -1))
                rook_route = list(range(size - 3, rook_init_pos[side])) + list(range(size - 3, rook_init_pos[side], -1))
                special_req = (endpos == (size - 2, 0)
                                # キングとルークの通過するマスに駒がない
                                and not any((x, 0) in gameboard_tmp
                                    for x in king_route + rook_route)
                                # キングが通過するマスが敵に攻撃されていない
                                and path_is_not_attacked(0, list(x for x in range(size - 2, king_init_pos, -1)))
                                )
        # 黒のキャスリング
        if piece.color == 'B':
            piece_req = (piece.name == 'BK'
                         and (rook_init_pos[side], size - 1) in gameboard
                         and gameboard[(rook_init_pos[side], size - 1)].name == 'BR')
            gameboard_tmp = copy(gameboard)
            # キャスリングに関与するキングとルークは除外して考える
            if (king_init_pos, size - 1) in gameboard_tmp:
                del gameboard_tmp[(king_init_pos, size - 1)]
            if (rook_init_pos[side], size - 1) in gameboard_tmp:
                del gameboard_tmp[(rook_init_pos[side], size - 1)]
            # クイーンサイド
            if side == 0:
                # キングとルークの通過するマス
                king_route = list(range(2, king_init_pos)) + list(range(2, king_init_pos, -1))
                rook_route = list(range(3, rook_init_pos[side])) + list(range(3, rook_init_pos[side], -1))
                special_req = (endpos == (2, size - 1)
                                # キングとルークの通過するマスに駒がない
                                and not any((x, size - 1) in gameboard_tmp
                                    for x in king_route + rook_route)
                                # キングが通過するマスが敵に攻撃されていない
                                and path_is_not_attacked(size - 1, list(x for x in range(2, king_init_pos)))
                                )
            # キングサイド
            if side == 1:
                # キングとルークの通過するマス
                king_route = list(range(size - 2, king_init_pos)) + list(range(size - 2, king_init_pos, -1))
                rook_route = list(range(size - 3, rook_init_pos[side])) + list(range(size - 3, rook_init_pos[side], -1))
                special_req = (endpos == (size - 2, size - 1)
                                # キングとルークの通過するマスに駒がない
                                and not any((x, size - 1) in gameboard_tmp
                                    for x in king_route + rook_route)
                                # キングが通過するマスが敵に攻撃されていない
                                and path_is_not_attacked(size - 1, list(x for x in range(size - 2, king_init_pos, -1)))
                                )

        return common_req and piece_req and special_req

    def castle_or_not(self, piece, endpos):
        '''
        キャスリングするかしないかを確認するか

        Parameters
        ----------
        piece : obj
            駒．
        endpos : tuple > (int, int)
            終了位置．絶対座標．

        Notes
        -----
        if文の条件式について．

        キングの移動終了位置が，キャスリング終了位置としてありうる4つの位置のうちのいずれかにあてはまる
        and (クイーンサイドキャスリングの条件にあてはまる
            or キングサイドキャスリングの条件にあてはまる)
        and キングの初期位置とキャスリング終了位置のx座標の差 == 1
        and 移動先に駒がない（＝キングが敵駒を取ったのではない）
        '''
        if (endpos in [(2, 0), (self.kind.size - 2, 0), (2, self.kind.size - 1), (self.kind.size - 2, self.kind.size - 1)]
                and (self.castling_requirements(piece, endpos, 0, self.gameboard)
                    or self.castling_requirements(piece, endpos, 1, self.gameboard))
                and abs(self.kind.placers[1].index(King) - endpos[0]) == 1
                and endpos not in self.gameboard):
            self.confirm_castling = True

    def is_check(self, color, gameboard):
        '''
        color 側がチェックされていれば True を返す

        Parameters
        ----------
        color : str > 'W' or 'B'
            駒色．
        gameboard : dict > {(int, int): obj, ...}
            盤面．
        '''
        kingDict = {}
        pieceDict = {B: [], W: []}
        for position, piece in gameboard.items():
            if piece.abbr == 'K':
                kingDict[piece.color] = position
            pieceDict[piece.color].append((piece, position))
        if self.can_see_king(kingDict[color], pieceDict[opponent[color]], gameboard):
            return True

    def cannot_move(self, color, gameboard):
        '''
        color側が駒を動かせないときTrueを返す

        Parameters
        ----------
        color : str > 'W' or 'B'
            駒色．
        gameboard : dict > {(int, int): obj, ...}
            盤面．
        '''
        for position, piece in gameboard.items():
            if color == piece.color:
                for dest in piece.available_moves(*position, gameboard):
                    gameboardTmp = copy(gameboard)
                    self.renew_gameboard(position, dest, gameboardTmp)
                    if not self.is_check(color, gameboardTmp):
                        return False
        return True

    def can_see_king(self, kingpos, piecelist, gameboard):
        '''
        piecelist の中の駒で kingpos を攻撃する駒があれば True を返す

        Parameters
        ----------
        kingpos : tuple > (int, int)
            キングの座標．
        piecelist : list > [(obj, (int, int)), ...]
            駒とその位置を格納したリスト．
        gameboard : dict > {(int, int): obj, ...}
            盤面．

        Returns
        -------
        bool
        '''
        for piece, position in piecelist:
            if kingpos in piece.available_moves(*position, gameboard):
                return True

    def renew_gameboard(self, startpos, endpos, gameboard):
        '''
        盤面を更新する

        Parameters
        ----------
        startpos, endpos : tuple > (int, int)
            開始位置，終了位置．絶対座標．
        gameboard : dict > {(int, int): obj, ...}
            盤面．
        '''
        color = gameboard[startpos].color
        gameboard[endpos] = gameboard[startpos]
        if startpos != endpos:
            del gameboard[startpos]
        # アンパッサン
        if self.en_passant:
            if (color == W
                    and gameboard.get((endpos[0], endpos[1] - 1))):
                if (gameboard[endpos[0], endpos[1] - 1].name == 'BP'):
                    del gameboard[(endpos[0], endpos[1] - 1)]
            elif (color == B
                    and gameboard.get((endpos[0], endpos[1] + 1))):
                if (gameboard[endpos[0], endpos[1] + 1].name == 'WP'):
                    del gameboard[(endpos[0], endpos[1] + 1)]
        # キャスリング
        # キャスリングできるゲームである
        # キャスリング確認中でない
        # キャスリングできる
        # 終了位置指定がある
        if (self.kind.castling
                and not self.confirm_castling
                and self.do_castling
                and None not in endpos):
            rook_init_pos = [pos for pos, piece in enumerate(self.kind.placers[1])
                if piece == Rook]
            size = self.kind.size
            piece = gameboard[endpos]
            # クイーンサイド
            rook_pos = rook_init_pos[0]
            # 白
            if (endpos == (2, 0)
                    and piece.color == 'W'
                    and (rook_pos, 0) in gameboard):
                if gameboard[(rook_pos, 0)].abbr == 'R':
                    del gameboard[(rook_pos, 0)]
                gameboard[(3, 0)] = Rook('W')
            # 黒
            if (endpos == (2, size - 1)
                    and piece.color == 'B'
                    and (rook_pos, size - 1) in gameboard):
                if gameboard[(rook_pos, size - 1)].abbr == 'R':
                    del gameboard[(rook_pos, size - 1)]
                gameboard[(3, size - 1)] = Rook('B')
            # キングサイド
            rook_pos = rook_init_pos[1]
            # 白
            if (endpos == (size - 2, 0)
                    and piece.color == 'W'
                    and (rook_pos, 0) in gameboard):
                if gameboard[(rook_pos, 0)].abbr == 'R':
                    del gameboard[(rook_pos, 0)]
                gameboard[(size - 3, 0)] = Rook('W')
            # 黒
            if (endpos == (size - 2, size - 1)
                    and piece.color == 'B'
                    and (rook_pos, size - 1) in gameboard):
                if gameboard[(rook_pos, size - 1)].abbr == 'R':
                    del gameboard[(rook_pos, size - 1)]
                gameboard[(size - 3, size - 1)] = Rook('B')


    def parse_mouse(self):
        '''マウスポインタの位置から指定したマス目を出力'''
        a, b = self.mousepos
        file_, rank = None, None
        for i in range(8):
            if abs(a - i) < 0.5:
                file_ = i
        for i in range(8):
            if abs(b - i) < 0.5:
                rank = i
        return (file_, rank)

    def idle_move(self):
        '''駒が動く時のアニメーション'''
        sleep(1.0 / 100)
        self.time += 1
        if self.time >= 10:
            self.moving = False
            glutIdleFunc(None)          # アニメーションの無効化
            glutMouseFunc(self.mouse)   # マウス操作の有効化
        glutPostRedisplay()

    def draw(self):
        '''描画コールバック'''
        glClearColor(0.6, 0.4, 0.2, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)

        if self.kind == None:
            draw_game_menu()
        else:
            if self.time == 1 and not self.confirm_castling:
                self.main()

            draw_squares()
            # 移動開始位置のマスの色を変える
            if None not in self.startpos:
                glColor(0.0, 1.0, 0.0, 0.2)
                square(*self.startpos)
            draw_file()
            draw_rank()
            draw_pieces(self.gameboard, piece_ID)
            if self.moving:
                # 行先の駒を隠す
                if self.endpos in dark_squares_list:
                    glColor(0.82, 0.55, 0.28)
                else:
                    glColor(1.00, 0.81, 0.62)
                if None not in self.endpos:
                    square(*self.endpos)
                # 動き中の駒を描画する
                if self.endpos in self.gameboard:
                    glEnable(GL_TEXTURE_2D)
                    draw_img(self.startpos[0] + ((self.endpos[0] - self.startpos[0]) / 2)
                            * (sin(pi*(self.time - 5) / 10) + 1),
                            self.startpos[1] +
                            ((self.endpos[1] - self.startpos[1]) / 2)
                            * (sin(pi*(self.time - 5) / 10) + 1),
                            piece_ID[self.gameboard[self.startpos if self.time == 0 else self.endpos].name])
                    glDisable(GL_TEXTURE_2D)
            # 可能な移動先の表示
            if self.select_dest and None not in self.startpos:
                piece = self.gameboard[self.startpos]
                draw_available_moves(
                    self.valid_moves(piece, self.startpos, self.gameboard),
                    opponent=self.playersturn != piece.color)
            # プロモーション
            if self.prom:
                draw_balloon(*self.endpos)
                piece_color = self.gameboard[self.endpos].color
                glEnable(GL_TEXTURE_2D)
                draw_img(2.0, 3.5, piece_ID[piece_color + 'N'])
                draw_img(3.0, 3.5, piece_ID[piece_color + 'B'])
                draw_img(4.0, 3.5, piece_ID[piece_color + 'R'])
                draw_img(5.0, 3.5, piece_ID[piece_color + 'Q'])
                glDisable(GL_TEXTURE_2D)
            # キャスリングするかどうかの確認
            if self.confirm_castling:
                draw_castling_confirmation(self.endpos)
            
        glDisable(GL_BLEND)
        glutSwapBuffers()

    def mouse(self, button, state, x, y):
        '''
        マウス入力コールバック

        Parameters
        ----------
        button : GLUT_LEFT_BUTTON, GLUT_MIDDLE_BUTTON, GLUT_RIGHT_BUTTON or int > 0, 1, 2
            マウスボタン．
            GLUT_LEFT_BUTTON, 0 -- 左
            GLUT_MIDDLE_BUTTON, 1 -- 中
            GLUT_RIGHT_BUTTON, 2 -- 右
        state : GLUT_DOWN, GLUT_UP or int > 0, 1
            ボタンの状態．
            GLUT_DOWN, 0 -- 押された
            GLUT_UP, 1 -- 離された
        x, y : int
            ウィンドウ座標．
        '''
        self.mousepos = window2world(x, y, WSIZE)
        # 左クリック
        if (button == GLUT_LEFT_BUTTON
                and state == GLUT_DOWN):
            try:
                # ゲーム種類選択
                if self.kind == None:
                    for i in range(2):
                        for j in range(5):
                            if i in game_dict and j < len(game_dict[i]):
                                if on_square(*self.mousepos, 4.5*i - 0.5, 4.5*i + 3.0, 6.5 - 1.5*j, 7.5 - 1.5*j):
                                    self.kind = game_dict[i][j]()
                                    self.after_deciding_kind()
                                    select_snd.play()
                else:
                    # 行先選択
                    if (self.select_dest
                            and self.parse_mouse() in self.valid_moves(
                                self.gameboard[self.startpos], self.startpos, self.gameboard)):
                        self.select_dest = False
                        self.endpos = self.parse_mouse()
                        self.time = 0
                        self.moving = True
                        glutIdleFunc(self.idle_move)    # アニメーションの有効化
                        glutMouseFunc(None)             # マウス操作の無効化
                        move_snd.play()
                    # 駒選択
                    elif (self.parse_mouse() in self.gameboard
                            and not self.prom and not self.confirm_castling):
                        self.startpos, self.endpos = (None, None), (None, None)
                        self.select_dest = True
                        self.startpos = self.parse_mouse()
            except KeyError:
                pass
            # キャスリングするかしないかの確認
            if self.kind.castling:
                if self.startpos in self.gameboard:
                    self.castle_or_not(
                        self.gameboard[self.startpos], self.endpos)
                if self.confirm_castling:
                    if on_square(*self.mousepos, 1.5, 3.0, 3.0, 4.0):
                        self.do_castling = True
                        self.confirm_castling = False
                        self.time = 0
                        self.moving = True
                        glutIdleFunc(self.idle_move)
                    if on_square(*self.mousepos, 4.0, 5.5, 3.0, 4.0):
                        self.do_castling = False
                        self.confirm_castling = False
                        self.time = 0
                        self.moving = True
                        glutIdleFunc(self.idle_move)
            # プロモーション
            if self.prom:
                piece_color = self.gameboard[self.endpos].color
                if on_square(*self.mousepos, 1.5, 2.5, 3.0, 4.0):
                    self.gameboard[self.endpos] = Knight(piece_color)
                    self.prom = False
                if on_square(*self.mousepos, 2.5, 3.5, 3.0, 4.0):
                    self.gameboard[self.endpos] = Bishop(piece_color)
                    self.prom = False
                if on_square(*self.mousepos, 3.5, 4.5, 3.0, 4.0):
                    self.gameboard[self.endpos] = Rook(piece_color)
                    self.prom = False
                if on_square(*self.mousepos, 4.5, 5.5, 3.0, 4.0):
                    self.gameboard[self.endpos] = Queen(piece_color)
                    self.prom = False

            glutPostRedisplay()

    def glmain(self):
        glutInit(sys.argv)
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA)    # 表示設定
        glutInitWindowSize(WSIZE, WSIZE)                # 画面サイズ
        glutInitWindowPosition(0, 0)                    # 画面の表示位置
        glutCreateWindow(b'Chess')                      # ウィンドウの名前
        glutDisplayFunc(self.draw)                      # 描画
        glutMouseFunc(self.mouse)                       # マウス入力コールバック
        glOrtho(-1.0, 8.0, -1.0, 8.0, -4, 4)

        # 画像の設定
        for name, num in piece_ID.items():
            set_img(name, name[0], num)

        glutMainLoop()


Game()
