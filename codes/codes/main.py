import sys
from copy import copy
from time import sleep
from math import pi, sin

from OpenGL.GL import *
from OpenGL.GLUT import *

from utils import *
from pieces import *

WSIZE = 720     # 画面サイズ

opponent = {WHITE: BLACK, BLACK: WHITE}


class Game:
    def __init__(self):
        self.playersturn = WHITE
        self.message = "this is where prompts will go"
        self.gameboard = {}
        self.place_pieces()
        print("chess program. enter moves in algebraic notation separated by space")

        # アンパッサン
        self.advanced2_pos = None
        # プロモーション
        self.prom = False
        # キャスリング
        # キャスリングのポテンシャルが残っているか
        self.can_castling = {'W': [True, True], 'B': [True, True]}

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

    def place_pieces(self):
        for i in range(0, 8):
            self.gameboard[(i, 1)] = Pawn(WHITE, 'WP', 1)
            self.gameboard[(i, 6)] = Pawn(BLACK, 'BP', -1)

        placers = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]

        for i in range(0, 8):
            self.gameboard[(i, 0)] = placers[i](WHITE, 'W' + placers[i].abbr)
            self.gameboard[(i, 7)] = placers[i](BLACK, 'B' + placers[i].abbr)

    def main(self):
        print(self.message)
        self.message = ""
        startpos, endpos = self.startpos, self.endpos
        if None not in startpos + endpos:
            try:
                target = self.gameboard[startpos]
            except:
                self.message = "could not find piece; index probably out of range"
                target = None

            if target and target.color == self.playersturn:
                print("found "+str(target))
                self.message = "that is a valid move"

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
                    self.message = f"{target.color} player is in check"
                if self.cannot_move(target.color, self.gameboard):
                    if self.is_check(target.color, self.gameboard):
                        self.message = f"Checkmate! {opponent[target.color]} player won!"
                        sys.exit()
                    else:
                        self.message = "Stalemate! It's draw."
                        sys.exit()
                if self.playersturn == BLACK:
                    self.playersturn = WHITE
                else:
                    self.playersturn = BLACK
            else:
                self.message = "there is no piece in that space"

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
        result = piece.available_moves(*startpos, gameboard, color=piece.color)
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
            if self.castling_requirements(piece, endpos, 1, gameboard):
                result += [endpos]
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
        if piece.abbr == 'P':
            return (self.advanced2_pos
                    and startpos[1] == endpos[1] - piece.direction
                    and startpos[1] == self.advanced2_pos[1]
                    and endpos[1] == self.advanced2_pos[1] + piece.direction
                    and abs(startpos[0] - endpos[0]) == 1
                    and abs(startpos[0] - self.advanced2_pos[0]) == 1
                    and endpos[0] == self.advanced2_pos[0])
        else:
            return False

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
            if (4, startpos_y) in gameboard_tmp:
                gameboard_tmp[endpos] = gameboard_tmp[(4, startpos_y)]
                del gameboard_tmp[(4, startpos_y)]
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
                and (7*side, 0) in gameboard
                and gameboard[(7*side, 0)].name == 'WR')
            # クイーンサイド
            if side == 0:
                special_req = (endpos == (2, 0)
                    # キングとルークの間に駒がない
                    and (1, 0) not in self.gameboard
                    and (2, 0) not in self.gameboard
                    and (3, 0) not in self.gameboard
                    # キングが通過するマスが敵に攻撃されていない
                    and path_is_not_attacked(0, [2, 3])
                    )
            # キングサイド
            if side == 1:
                special_req = (endpos == (6, 0)
                    # キングとルークの通過するマスに駒がない
                    and (6, 0) not in self.gameboard
                    and (5, 0) not in self.gameboard
                    # キングが通過するマスが敵に攻撃されていない
                    and path_is_not_attacked(0, [6, 5])
                    )
        # 黒のキャスリング
        if piece.color == 'B':
            piece_req = (piece.name == 'BK'
                and (7*side, 7) in gameboard
                and gameboard[(7*side, 7)].name == 'BR')
            # クイーンサイド
            if side == 0:
                special_req = (endpos == (2, 7)
                    # キングとルークの通過するマスに駒がない
                    and (1, 7) not in self.gameboard
                    and (2, 7) not in self.gameboard
                    and (3, 7) not in self.gameboard
                    # キングが通過するマスが敵に攻撃されていない
                    and path_is_not_attacked(7, [2, 3])
                    )
            # キングサイド
            if side == 1:
                special_req = (endpos == (6, 7)
                    # キングとルークの通過するマスに駒がない
                    and (6, 7) not in self.gameboard
                    and (5, 7) not in self.gameboard
                    # キングが通過するマスが敵に攻撃されていない
                    and path_is_not_attacked(7, [6, 5])
                    )

        return common_req and piece_req and special_req

    def is_check(self, color, gameboard):
        '''
        color 側がチェックされていれば True を返す
        
        Parameters
        ----------
        color : str > 'white' or 'black'
            駒色．
        gameboard : dict > {(int, int): obj, ...}
            盤面．
        '''
        kingDict = {}
        pieceDict = {BLACK: [], WHITE: []}
        for position, piece in gameboard.items():
            if type(piece) == King:
                kingDict[piece.color] = position
            pieceDict[piece.color].append((piece, position))
        if self.can_see_king(kingDict[color], pieceDict[opponent[color]], gameboard):
            return True

    def cannot_move(self, color, gameboard):
        '''
        color側が駒を動かせないときTrueを返す
        
        Parameters
        ----------
        color : str > 'white' or 'black'
            駒色．
        gameboard : dict > {(int, int): obj, ...}
            盤面．
        '''
        for position, piece in gameboard.items():
            if color == piece.color:
                for dest in piece.available_moves(*position, gameboard, color=color):
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
            if piece.is_valid(position, kingpos, piece.color, gameboard):
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
        del gameboard[startpos]
        # アンパッサン
        if self.en_passant:
            if (color == WHITE
                    and gameboard.get((endpos[0], endpos[1] - 1))):
                del gameboard[(endpos[0], endpos[1] - 1)]
            elif (color == BLACK
                    and gameboard.get((endpos[0], endpos[1] + 1))):
                del gameboard[(endpos[0], endpos[1] + 1)]
        # キャスリング
        if (gameboard[endpos].abbr == 'K'
                and abs(startpos[0] - endpos[0]) == 2):
            # クイーンサイド
            # 白
            if endpos == (2, 0):
                del gameboard[(0, 0)]
                gameboard[(3, 0)] = Rook('W', 'WR')
            # 黒
            if endpos == (2, 7):
                del gameboard[(0, 7)]
                gameboard[(3, 7)] = Rook('B', 'BR')
            # キングサイド
            # 白
            if endpos == (6, 0):
                del gameboard[(7, 0)]
                gameboard[(5, 0)] = Rook('W', 'WR')
            # 黒
            if endpos == (6, 7):
                del gameboard[(7, 7)]
                gameboard[(5, 7)] = Rook('B', 'BR')

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

        if self.time == 1:
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
                # 駒選択
                elif (self.parse_mouse() in self.gameboard):
                    self.startpos, self.endpos = (None, None), (None, None)
                    self.select_dest = True
                    self.startpos = self.parse_mouse()
            except KeyError:
                pass
            # プロモーション
            if self.prom:
                piece_color = self.gameboard[self.endpos].color
                if on_square(*self.mousepos, 1.5, 2.5, 3.0, 4.0):
                    self.gameboard[self.endpos] = Knight(piece_color, piece_color + 'N')
                    self.prom = False
                if on_square(*self.mousepos, 2.5, 3.5, 3.0, 4.0):
                    self.gameboard[self.endpos] = Bishop(piece_color, piece_color + 'B')
                    self.prom = False
                if on_square(*self.mousepos, 3.5, 4.5, 3.0, 4.0):
                    self.gameboard[self.endpos] = Rook(piece_color, piece_color + 'R')
                    self.prom = False
                if on_square(*self.mousepos, 4.5, 5.5, 3.0, 4.0):
                    self.gameboard[self.endpos] = Queen(piece_color, piece_color + 'Q')
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
