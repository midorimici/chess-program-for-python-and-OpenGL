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
                self.renew_gameboard(startpos, endpos, self.gameboard)
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
