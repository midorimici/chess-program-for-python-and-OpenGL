from math import pi, sin, cos
from OpenGL.GL import *
from OpenGL.GLUT import *

from PIL import Image


def set_img(name, path, imgID):
    '''画像の設定: name.pngを読み込む

    Parameters
    ----------
    name : str
            画像のファイル名．
    path : str > 'W', 'B'
            画像があるフォルダ名．
    imgID : int
            指定する画像ID．
    '''
    img = Image.open(f'../img/{path}/{name}.png')   # 画像を読み込む
    w, h = img.size                                 # 画像の横幅、縦幅
    glBindTexture(GL_TEXTURE_2D, imgID)             # imgID のテクスチャを有効化する
	# 画像とテクスチャを関連づける
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0,
        GL_RGBA, GL_UNSIGNED_BYTE, img.tobytes())
	# テクスチャの設定
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)


def draw_img(x, y, imgID):
    '''
	画像を描画する

    Parameters
    ----------
    x, y : float
        描画する座標．
    imgID : int
        画像ID．
    '''
    glPushMatrix()          # 変形範囲の開始
    glBindTexture(GL_TEXTURE_2D, imgID)     # imgID のテクスチャを有効化する
    glTranslate(x, y, 0)    # 平行移動
    glColor(1, 1, 1)        # 色指定

	# テクスチャ座標を指定する
    glBegin(GL_QUADS)
    glTexCoord(0.0, 1.0)
    glVertex(-1.0 / 2, -1.0 / 2)
    glTexCoord(1.0, 1.0)
    glVertex(1.0 / 2, -1.0 / 2)
    glTexCoord(1.0, 0.0)
    glVertex(1.0 / 2, 1.0 / 2)
    glTexCoord(0.0, 0.0)
    glVertex(-1.0 / 2, 1.0 / 2)
    glEnd()

    glPopMatrix()           # 変形範囲の終了


def window2world(x, y, wsize):
    '''
    ウィンドウ座標を世界座標に変換する

    Parameters
    ----------
    x, y : int
        変換するもとの座標．
    wsize : int
        画面の大きさ．

    Returns
    -------
    list > [float, float]
        変換先の座標．
    '''
    return [9*x / wsize - 1, 7 - (9*y / wsize - 1)]


def draw_pieces(gameboard, imgID_dict, size=8):
    '''
	駒を描画する

    Parematers
    ----------
    gameboard : dict > {(int, int): obj, ...}
    盤面．
    imgID : int
        画像ID．
    size : int, default 8
        盤面の大きさ．
    '''
    glEnable(GL_TEXTURE_2D)		# テクスチャマッピングを有効化
    for i in range(size):
        for j in range(size):
            piece = gameboard.get((i, j))  # (i, j)にある駒オブジェクトを取得
            if piece:
                draw_img(i, j, imgID_dict[piece.name])
    glDisable(GL_TEXTURE_2D)  # テクスチャマッピングを無効化


def draw_str(x, y, string, font=GLUT_BITMAP_HELVETICA_18, gap=0.25):
    '''
	文字列を描画する

	Parameters
	----------
	x, y : float
		描画する座標．
	string : str
		描画する文字列．
	font : , default GLUT_BITMAP_HELVETICA_18
		フォント．以下から指定．
		GLUT_BITMAP_8_BY_13
		GLUT_BITMAP_9_BY_15
		GLUT_BITMAP_TIMES_ROMAN_10
		GLUT_BITMAP_TIMES_ROMAN_24
		GLUT_BITMAP_HELVETICA_10
		GLUT_BITMAP_HELVETICA_12
		GLUT_BITMAP_HELVETICA_18
	gap : float, default 0.25
		文字間隔．
	'''
    for k in range(len(string)):
        glRasterPos2f(x + gap*k, y)                 # 描画位置指定
        glutBitmapCharacter(font, ord(string[k]))   # 文字列描画


def square(x, y):
    '''
    正方形を描画する

    Parameters
    ----------
    x, y : float
        中心の座標．
    '''
    glPushMatrix()                  # 変形が及ぶ範囲の開始
    glTranslate(x, y, 0)            # 以下の対象を平行移動
    glBegin(GL_QUADS)               # 四角形の描画を宣言
    glVertex(-1.0 / 2, -1.0 / 2)    # 頂点１の座標
    glVertex(1.0 / 2, -1.0 / 2)     # 頂点２
    glVertex(1.0 / 2, 1.0 / 2)      # 頂点３
    glVertex(-1.0 / 2, 1.0 / 2)     # 頂点４
    glEnd()                         # 描画終了
    glPopMatrix()                   # 変形が及ぶ範囲の終了


def circle(x, y, opponent, r=0.25):
    '''
    円を描画する

    Parameters
    ----------
    x, y : float
        中心の座標．
    opponent : bool
        True のとき，赤色で描画する．
    r : float, default 0.25
    	半径．
    '''
    glPushMatrix()
    glTranslate(x, y, 0)
    if opponent:
        glColor(1.0, 0.5, 0.5, 0.7)
    else:
        glColor(0.5, 0.5, 1.0, 0.7)
    glBegin(GL_POLYGON)
    for k in range(12):
        xr = r * cos(2 * pi * k / 12)
        yr = r * sin(2 * pi * k / 12)
        glVertex(xr, yr, 0)
    glEnd()
    glPopMatrix()


def draw_balloon(x, y, num=4):
    '''
    プロモーションのときの吹き出しを描画する

    Parameters
    ----------
    x, y : int
        駒の座標．
    num : int, default 4
        プロモーション選択肢数．
    '''
    glColor(0.5, 0.5, 0.5)  # 色の指定
    glBegin(GL_QUADS)       # 四角形を描画
    glVertex(1.0, 2.5 - ((num - 1) // 4) / 2)
    glVertex(1.0, 4.5 + ((num - 1) // 4) / 2)
    glVertex(2.0 + num if num <= 4 else 6.0, 4.5 + ((num - 1) // 4) / 2)
    glVertex(2.0 + num if num <= 4 else 6.0, 2.5 - ((num - 1) // 4) / 2)
    glEnd()
    glBegin(GL_TRIANGLES)   # 三角形を描画
    glVertex(3.0, 3.5)
    glVertex(4.0, 3.5)
    glVertex(x, y)
    glEnd()


def on_square(x, y, left, right, bottom, top):
	'''
	left < x < right かつ bottom < y < top のとき，True
	
	Parameters
	----------
	x, y : float
		測定する座標．
	left, right, bottom, top : float
		ボタンの左右下上端の座標．

	Returns
	-------
	bool
	'''
	if left < x < right and bottom < y < top:
		return True


def draw_button(left, right, bottom, top,
        letter, back_color=(1.00, 0.81, 0.62), font_color=(0.82, 0.55, 0.28)):
    '''ボタンを描画する

    Parameters
    ----------
    left, right, bottom, top : float
        ボタンの左右下上端の座標．
    letter : str
        ボタン上に描画する文字．
    back_color : tuple or list, default (1.00, 0.81, 0.62)
        ボタンの色．
    font_color : tuple or list, default (0.82, 0.55, 0.28)
        文字の色．
    '''
    glColor(*back_color)
    glBegin(GL_QUADS)
    glVertex(left, bottom)
    glVertex(left, top)
    glVertex(right, top)
    glVertex(right, bottom)
    glEnd()
    glColor(*font_color)
    draw_str((left + right) / 2 - 0.1 * len(letter), (bottom + top) / 2, letter, gap=0.2)


# ゲーム選択画面に表示するゲーム名
game_name_dict = {0: ('Normal Chess', 'Chess 960', 'Unicorn')}


def draw_game_menu():
	'''ゲーム選択メニューを描画する'''
	for i in range(2):
		for j in range(5):
			if i in game_name_dict and j < len(game_name_dict[i]):
				draw_button(4.5*i - 0.5, 4.5*i + 3.0, 6.5 - 1.5*j, 7.5 - 1.5*j,
                    game_name_dict[i][j])


dark_squares_list = ([(i, j) for i in range(0, 8, 2) for j in range(0, 8, 2)]
    + [(i, j) for i in range(1, 8, 2) for j in range(1, 8, 2)])


def draw_squares():
    '''マス目を描画する'''
    for i in range(8):
        for j in range(8):
            if (i, j) in dark_squares_list:
                glColor(0.82, 0.55, 0.28)
                square(i, j)
            else:
                glColor(1.00, 0.81, 0.62)
                square(i, j)


def draw_file():
    '''ファイルの文字を描画する'''
    glColor(1.0, 1.0, 1.0)
    for x in range(8):
        draw_str(x, -0.75, chr(x + 97))


def draw_rank():
    '''ランクの文字を描画する'''
    glColor(1.0, 1.0, 1.0)
    for y in range(8):
        draw_str(-0.75, y, str(y + 1))


def draw_available_moves(poslist, opponent=None):
    '''動かせる位置を描画する

    Parameters
    ----------
    poslist : list > [(int, int), ...]
        移動先の座標のリスト．
    opponent : bool or None, default None
        True のとき，赤色で描画する．
    '''
    for pos in poslist:
        circle(*pos, opponent)


def draw_castling_confirmation(endpos):
    '''キャスリング確認ダイアログを表示する'''
    draw_balloon(*endpos)
    glColor(1.0, 1.0, 1.0)
    draw_str(2.0, 4.0, 'Castling?')
    draw_button(1.5, 3.0, 3.0, 3.5, 'Yes',
                (1.0, 1.0, 1.0), (0.0, 0.0, 0.0))
    draw_button(4.0, 5.5, 3.0, 3.5, 'No',
                (1.0, 1.0, 1.0), (0.0, 0.0, 0.0))