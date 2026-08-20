# forTrace.py 2026.08.20
# 手頃なアプリがないので自分で作ることにした。


import os, sys, subprocess, shlex
import cv2

os.environ["QT_LOGGING_RULES"] = "qt.svg*=false"

from PySide6.QtCore import  Qt, QPoint, QSize, QEvent, QSettings
from PySide6.QtGui  import  (QPainter, QImage, QPen, QColor, QIcon, QBrush,
                            QKeySequence, QPixmap, QMouseEvent,QClipboard,
                            QWheelEvent, QPainterPath, QAction, QShortcut,
                            QCursor, QGuiApplication, QTabletEvent)
from PySide6.QtWidgets import (QMainWindow, QApplication, QMenu, QMenuBar,
                            QFileDialog, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLabel,
                            QMessageBox, QGraphicsView, QGraphicsScene)

import face_pose_detect as fpd

# 色リスト
COLORS = [
# 17 undertones https://lospec.com/palette-list/17undertones
'#000000', '#ffffff', '#35e3e3', '#141923', '#414168', '#3a7fa7', '#8fd970',
'#5ebb49', '#458352', '#dcd37b', '#fffee5', '#ffd035', '#cc9245', '#a15c3e',
'#a42f3b', '#f45b7a', '#c24998', '#81588d', '#bcb0c2'
]

# View: QGraphicsViewを継承するクラス。ズームとパンのロジックを実装できる。
'''
class CustomGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        #self.setRenderHint(QPainter.Antialiasing)  # アンチエイリアシングを有効にして描画を滑らかにする
        self.setDragMode(QGraphicsView.DragMode.NoDrag) #Qt6
        self.panning = False
        self.pan_start_point = QPoint()
        self.shit_key_pressed = False

    #--- Wacomのペンタブとマウスが競合するため、マウス無しの時にキーボードで代用する処理を追加 ---#
    def keyPressEvent(self, event):
        # +/-キーでズーム
        # ズーム係数を設定（wheelEventと同じ）
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        if event.key() == Qt.Key.Key_Plus:
            # キー操作の場合はマウス位置ではなく、ビューの中心を基準にズームするのが一般的
            self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
            self.scale(zoom_in_factor, zoom_in_factor)
            event.accept()  # イベントを処理したことをシステムに通知
            return

        if event.key() == Qt.Key.Key_Minus:
            self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
            self.scale(zoom_out_factor, zoom_out_factor)
            event.accept()
            return

        # Escキーを押すと元のサイズに戻る
        if event.key() == Qt.Key.Key_Escape:
            self.panning = False
            QApplication.restoreOverrideCursor()
            self.resetTransform()   # ズームが取り消され、元のスケールに戻る
            event.accept()
            return
        
        # 上記以外のキーは、本来のQGraphicsViewの挙動に任せる
        super().keyPressEvent(event)
    #--- キーボードで代用処理ここまで ---#

    def mousePressEvent(self, event):
        # 中ボタンでパン開始
        if event.button() == Qt.MouseButton.MiddleButton:
            self.panning = True
            self.pan_start_point = event.position().toPoint()
            QApplication.setOverrideCursor(Qt.CursorShape.ClosedHandCursor)
            QApplication.processEvents()   # カーソル変更をすぐに反映
            event.accept() # イベントを消費
            return # super()に行くと通常の左クリック（選択など）が動いてしまうのを防ぐ
            
        # 右ボタンでリセット
        elif event.button() == Qt.MouseButton.RightButton:
            self.resetTransform()
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # 移動処理は既存のロジック（self.panning が True なら動く）でそのまま機能する
        if self.panning:
            delta = self.mapToScene(event.position().toPoint()) - self.mapToScene(self.pan_start_point)
            self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
            self.translate(delta.x(), delta.y())
            self.pan_start_point = event.position().toPoint()
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        # 中ボタン、または左ボタンが離されたときにパンを終了
        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.LeftButton):
            if self.panning:
                self.panning = False
                QApplication.restoreOverrideCursor()
                event.accept()
                return

        super().mouseReleaseEvent(event)

    # マウスホィールイベントwheelEvent()をオーバーライドしてズーム機能を実装する
    # このメソッドはマウスホイールが回転したときに呼び出される。
    def wheelEvent(self, event):
        # ズーム係数を設定
        zoom_in_factor = 1.1    #1.25
        zoom_out_factor = 1 / zoom_in_factor

        # アンカーを設定（これだけでマウス位置を中心にズームしてくれる）
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # ズーム処理
        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

    # mousePressEvent()、mouseMoveEvent()、mouseReleaseEvent() をオーバーライド
    def mousePressEvent(self, event):
        # 中ボタンでのパン機能
        if event.button() == Qt.MouseButton.MiddleButton:
            self.panning = True
            self.pan_start_point = event.position().toPoint()
            # カーソルを掴んだ手に変更
            QApplication.setOverrideCursor(Qt.CursorShape.ClosedHandCursor)
            QApplication.processEvents()   # カーソル変更をすぐに反映
        # 右ボタンでリセット
        elif event.button() == Qt.MouseButton.RightButton:
            self.resetTransform()
        super().mousePressEvent(event)
'''

class CustomGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.panning = False
        self.pan_start_point = QPoint()
        self.shift_key_pressed = False

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # タブレットのトラッキングを有効化(必要に応じて)
        self.setAttribute(Qt.WidgetAttribute.WA_TabletTracking, True)

    def keyPressEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        if event.key() == Qt.Key.Key_Plus:
            self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
            self.scale(zoom_in_factor, zoom_in_factor)
            event.accept()
            return

        if event.key() == Qt.Key.Key_Minus:
            self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
            self.scale(zoom_out_factor, zoom_out_factor)
            event.accept()
            return

        if event.key() == Qt.Key.Key_Escape:
            self.panning = False
            QApplication.restoreOverrideCursor()
            self.resetTransform()
            event.accept()
            return

        if event.key() == Qt.Key.Key_Shift:
            self.shift_key_pressed = True
            event.accept()
            return

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Shift and not event.isAutoRepeat():
            self.shift_key_pressed = False
            if self.panning:
                self.panning = False
                QApplication.restoreOverrideCursor()
            event.accept()
            return

        super().keyReleaseEvent(event)

    # --- ペン入力はここで処理する ---
    def tabletEvent(self, event: QTabletEvent):
        pos = event.position().toPoint()

        if event.type() == QTabletEvent.Type.TabletPress:
            if self.shift_key_pressed:
                self.panning = True
                self.pan_start_point = pos
                QApplication.processEvents()
                event.accept()  # ここで消費し、マウスイベントへの変換・Scene側への伝播を防ぐ
                return
            # シフトが押されていなければ通常の描画処理へ
            event.ignore()  # ignoreしてQGraphicsSceneの通常処理(描画)に渡す
            super().tabletEvent(event)
            return

        if event.type() == QTabletEvent.Type.TabletMove:
            if self.panning:
                delta = self.mapToScene(pos) - self.mapToScene(self.pan_start_point)
                self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
                self.translate(delta.x(), delta.y())
                self.pan_start_point = pos
                event.accept()
                return
            event.ignore()
            super().tabletEvent(event)
            return

        if event.type() == QTabletEvent.Type.TabletRelease:
            if self.panning:
                self.panning = False
                QApplication.restoreOverrideCursor()
                event.accept()
                return
            event.ignore()
            super().tabletEvent(event)
            return

        super().tabletEvent(event)

    # --- 中ボタン・右ボタンなど、マウス由来の操作はそのまま維持 ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.panning = True
            self.pan_start_point = event.position().toPoint()
            QApplication.setOverrideCursor(Qt.CursorShape.ClosedHandCursor)
            QApplication.processEvents()
            event.accept()
            return

        elif event.button() == Qt.MouseButton.RightButton:
            self.resetTransform()
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.panning:
            delta = self.mapToScene(event.position().toPoint()) - self.mapToScene(self.pan_start_point)
            self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
            self.translate(delta.x(), delta.y())
            self.pan_start_point = event.position().toPoint()
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            if self.panning:
                self.panning = False
                QApplication.restoreOverrideCursor()
                event.accept()
                return

        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        zoom_in_factor = 1.1
        zoom_out_factor = 1 / zoom_in_factor
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

# Canvas: QPainterで描画機能を持つカスタムQLabelクラス
class Canvas(QLabel):
    # 初期化
    def __init__(self):
        super().__init__()
        width = 1196
        height = 830
        self.setGeometry(0, 0, width, height)
        QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
        QApplication.processEvents()   # カーソル変更をすぐに反映

        # 描画用のQPixmapを初期化
        self.image = QPixmap(width, height)
        self.image.fill(QColor("white"))
        self.setPixmap(self.image)

        # モード設定
        # "paint", "fill", "draw"
        self.mode = "paint"   # デフォルトはペイントモード

        # 初期値
        self.last_x, self.last_y = None, None
        self.pen_color = QColor('#000000')
        self.pen_size = 5
        self.drawing = False

        # Undo履歴
        self.undo_stack = []
        self.max_undo = 256

        # クリップボード
        self.clip = QApplication.clipboard()

        # ショートカット登録
        QShortcut(QKeySequence("Ctrl+Z"), self, activated=self.undo)
        QShortcut(QKeySequence("Ctrl+V"), self, activated=self.pasted)
        QShortcut(QKeySequence("Ctrl+C"), self, activated=self.copied)

    # ブラシ、フィルの色を変える
    def set_pen_color(self, c):
        self.pen_color = QColor(c)

    # ブラシの太さ
    def set_pen_size(self, pix):
        self.mode = "paint"
        self.pen_size = pix
        QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
        QApplication.processEvents()   # カーソル変更をすぐに反映

    # フィルモードのフラグ
    def setFillMode(self):
        self.mode = "fill"
        QApplication.setOverrideCursor(Qt.CursorShape.CrossCursor)
        QApplication.processEvents()   # カーソル変更をすぐに反映

    # ドローモードのフラグ
    def setDrawMode(self):
        self.mode = "draw"
        QApplication.setOverrideCursor(Qt.CursorShape.DragCopyCursor)
        QApplication.processEvents()   # カーソル変更をすぐに反映
        # 描画するすべてのQPainterPathを保持するリスト
        self.paths = []
        # 最後にクリックされた点 (新しい線の始点となる)
        self.last_point = None

    # ブラシの初期値に戻す(色と幅はそのままの方がいいかな）
    def brushAgain(self):
        self.mode = "paint"
        QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
        QApplication.processEvents()   # カーソル変更をすぐに反映
        #self.set_pen_size(5)
        #self.set_pen_color(QColor('#000000'))

    # マウスボタンを押した時...モードによってツールを使い分ける
    def mousePressEvent(self, e):
        # モードが"fill"なら
        if e.buttons() == Qt.MouseButton.LeftButton and self.mode == "fill":
            self.flood_fill(e.pos(), self.pen_color)

        # モードが"draw"なら
        if e.buttons() == Qt.MouseButton.LeftButton and self.mode == "draw":
            self.draw_path(e.pos())

        # Ctrlが押されているか確認 (クリックした点の色を拾う）
        if e.modifiers() == Qt.KeyboardModifier.ControlModifier:
            x = e.position().x()
            y = e.position().y()
            # QPixmapをQImageに変換
            img = self.image.toImage()
            # 座標が有効な範囲内かチェック
            if 0 <= x < img.width() and 0 <= y < img.height():
                # pixelColor()メソッドで色を取得
                color = img.pixelColor(int(x), int(y))
                # ペンの色を変更
                self.set_pen_color(color)
                # 画面を再描画して、新しいペンの色を反映させる
                self.update()

    # 線を引く処理（ペイント、パス）
    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.MiddleButton:
            return

        # QPainterをwith構文で安全に開く
        # self.image (QPixmap) に対して描画を行う
        painter = QPainter(self.image)
        try:
            p = painter.pen()
            p.setWidth(self.pen_size)
            p.setColor(self.pen_color)
            p.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(p)

            # ブラシで描線
            if self.mode == "paint" and not e.modifiers() == Qt.KeyboardModifier.ControlModifier:
                if self.last_x is None:
                    self.saveUndo()
                    self.last_x = int(e.position().x())
                    self.last_y = int(e.position().y())
                    return
                try:
                    painter.drawLine(self.last_x, self.last_y, int(e.position().x()), int(e.position().y()))
                except TypeError:
                    print(self.last_x, self.last_y, e.position().x(), e.position().y())

                self.last_x = int(e.position().x())
                self.last_y = int(e.position().y())

            # パスで描線
            elif self.mode == "draw":
                for path in self.paths:
                    painter.drawPath(path)

        finally:
            painter.end() # 確実に終了させる

        self.setPixmap(self.image) # 描画結果を反映
        self.update()

    # マウスボタンをリリースしたらペイントの描線を終了
    def mouseReleaseEvent(self, e):
        if self.mode == "draw":
            pass
        else:
            self.last_x = None
            self.last_y = None

    # Escかスペースを押したらパス描線を終了
    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape or e.key() == Qt.Key.Key_Space:
            self.paths = []
            self.last_point = None
            self.last_x = None  # 新しいペイント位置
            self.last_y = None
            if e.key() == Qt.Key.Key_Escape:
                self.brushAgain()

    # Undo保存
    def saveUndo(self):
        if len(self.undo_stack) >= self.max_undo:
            self.undo_stack.pop(0)      # 最大数を超えたら古いのから削除
        self.undo_stack.append(self.pixmap().copy())  # QPixmap.copy()でOK

    # Undo実行
    def undo(self):
        if self.undo_stack:
            prev_pixmap = self.undo_stack.pop()
            self.image = prev_pixmap
            self.setPixmap(self.image)
            self.update()

    # ペーストフラグ
    def pasted(self):
        self.mode = "paint"
        QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
        QApplication.processEvents()   # カーソル変更をすぐに反映
        self.load_image_to_canvas("pasted")

    # コピーフラグ
    def copied(self):
        self.mode = "paint"
        QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
        QApplication.processEvents()   # カーソル変更をすぐに反映
        self.copy_image_to_clipboard("copied")

    # 画像をクリップボードへ
    def copy_image_to_clipboard(self, path):
        if path == "copied":
            clipboard = QGuiApplication.clipboard()
            image = self.image.toImage()
            clipboard.setImage(image)

    # 外部画像をキャンバスに設定する
    def load_image_to_canvas(self, path):
        self.mode = "paint"
        QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
        QApplication.processEvents()   # カーソル変更をすぐに反映
        if path == "pasted":
            mime_data = self.clip.mimeData()

            # クリップボードに画像データがない時は白紙を表示
            loaded_pixmap = QPixmap(self.size())
            loaded_pixmap.fill(QColor("white")) # 背景を白で塗りつぶす

            if mime_data.hasImage():
                loaded_pixmap = QPixmap.fromImage(mime_data.imageData())
        else:
            loaded_pixmap = QPixmap(path)

        if not loaded_pixmap.isNull():
            # 新しいQPixmapを作成し、キャンバスのサイズに合わせる
            new_image = QPixmap(self.size())
            new_image.fill(QColor("white")) # 背景を白で塗りつぶす

            # QPainterを使用して、読み込んだ画像を新しいQPixmapに描画
            painter = QPainter(new_image)

            # 画像をキャンバスのサイズに合わせてスケール
            scaled_pixmap = loaded_pixmap.scaled(self.size(),
                                                Qt.AspectRatioMode.KeepAspectRatio,
                                                Qt.TransformationMode.FastTransformation)

            # 描画開始位置を計算して中央に配置
            x_offset = (new_image.width() - scaled_pixmap.width()) // 2
            y_offset = (new_image.height() - scaled_pixmap.height()) // 2

            painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
            painter.end()

            self.image = new_image
            self.setPixmap(self.image)
            self.update()
            return True
        return False

    # キャンバスをクリア
    def clear_canvas(self):
        # QPixmapオブジェクトを新しく作成して、白で塗りつぶす
        self.image = QPixmap(self.size())
        self.image.fill(QColor("white"))
        self.setPixmap(self.image)
        self.update()
        self.brushAgain()

    # クリック位置から同じ色の領域を塗りつぶす
    def flood_fill(self, start_pos, new_color):
        if self.mode == 'draw':
            self.paths = []
            self.last_point = None

        #1 開始ピクセル、new_color、および空のリスト「have_seen」と「queue」を用意する
        image = self.pixmap().toImage()
        w, h = image.width(), image.height()
        x, y = start_pos.x(), start_pos.y()
        w, h = image.width(), image.height()
        have_seen = set()
        queue = [(x, y)]    # 初期位置
        if not (0 <= x < w and 0 <= y < h):
            # クリック位置がキャンバス内になければ何もしない
            return

        #2 現在のピクセルの色を確認。これが塗りつぶしの対象となる。
        target_color = image.pixelColor(x, y)
        if target_color == new_color:
            # 塗り色（new_color)と同色なら何もしない
            return

        while queue:
            #3 キューから直近のアイテムを取り出す（初期状態では開始位置 x, y）。その位置を囲む4つのピクセル（四方位）を取得
            cx, cy = queue.pop()  # popでキュー・リストから抜き出される
            neighbors = [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]    # 右・左・上・下

            #4 四方位のピクセルについて確認
            #  未確認であって、nxが0以上w未満、nyが0以上h未満の時に次の処理をする
            #  そのピクセルの色とtarget_colorを比較
            for nx, ny in neighbors:
                if (nx, ny) not in have_seen and 0 <= nx < w and 0 <= ny < h:
                    current_color = image.pixelColor(nx, ny)
                    if current_color == target_color:
                        #5 target_colorと同色であれば(x,y)の位置をキューに追加し、そのピクセルをnew_colorで更新
                        queue.append((nx, ny))
                        image.setPixelColor(nx, ny, new_color)
                        #6 (x,y)の位置を「have_seen」に追加し、確認済みの場所を記録 再度確認するオーバーヘッドを回避
                        have_seen.add((nx, ny))

                        #7 ステップ3から繰り返し、キューが空になるまで続ける

        self.image = QPixmap.fromImage(image)
        self.setPixmap(self.image)
        self.update()
        self.saveUndo()     # Undoスタックにコピーを追加

    # クリックごとに線を引く
    def draw_path(self, start_pos):
        #1 開始ピクセル、空のリスト「have_seen」と「queue」を用意する
        image = self.pixmap().toImage()
        w, h = image.width(), image.height()
        x, y = start_pos.x(), start_pos.y()
        w, h = image.width(), image.height()
        have_seen = set()
        queue = [(x, y)]    # 初期位置
        if not (0 <= x < w and 0 <= y < h):
            # クリック位置がキャンバス内になければ何もしない
            return

        current_point = start_pos   # 現在のクリック位置
        # まだ点が打たれていない (=最初のクリック)
        if self.last_point is None:
            # 現在の点を始点として記憶するだけで、線は引かない
            #print(f"最初の点: {current_point.x()}, {current_point.y()} を始点に設定")
            pass
        # 既に前の点がある場合 (2回目以降のクリック)
        else:
            start_point = self.last_point # 1つ前の点が新しい線の始点
            end_point = current_point     # 現在のクリック位置が終点

            # QPainterPathを作成
            path = QPainterPath(start_point.toPointF())
            # moveTo() で始点に移動した後、lineTo() で終点まで線を追加
            path.lineTo(end_point.toPointF())

            # 描画対象のリストに追加
            self.paths.append(path)
            #print(f"線を追加: ({start_point.x()}, {start_point.y()}) -> ({end_point.x()}, {end_point.y()})")

            # 再描画を要求 (paintEventが呼ばれる)
            self.update()
            self.saveUndo()     # Undoスタックにコピーを追加

        # 現在の点を「最後の点」として保存し、次回のクリックの始点にする
        self.last_point = current_point

# Paletteクラス
class QPaletteButton(QPushButton):
    def __init__(self, color):
        super().__init__()
        self.setFixedSize(QSize(32,32))
        self.color = color
        self.setStyleSheet("background-color: %s;" % color)

# メインウィンドウ
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ウィンドウの初期サイズを指定
        self.resize(1234, 920)

        # タイトルとアイコン
        title = "forTrace"
        icon = "icons/face-button.png"
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(icon))

        # QGraphicsViewとQGraphicsSceneのセットアップ
        self.view = CustomGraphicsView()
        self.scene = QGraphicsScene()

        # シーンのサイズをセット (Canvasのサイズに合わせて設定)
        canvas_width = 1196
        canvas_height = 830
        self.scene.setSceneRect(0, 0, canvas_width, canvas_height)

        # ビューにシーンを設定
        self.view.setScene(self.scene)

        # キャンバスを作成
        self.canvas = Canvas()
        self.canvas.setFixedSize(canvas_width, canvas_height)

        # QGraphicsSceneにCanvasウィジェットを追加
        self.proxy_widget = self.scene.addWidget(self.canvas)

        # ウィジェット配置
        w = QWidget()
        l = QVBoxLayout()

        # パレット
        palette = QHBoxLayout()
        self.add_palette_buttons(palette)
        l.addLayout(palette)

        # QGraphicsViewをレイアウトに追加
        l.addWidget(self.view)

        w.setLayout(l)
        self.setCentralWidget(w)

        # ズームとパンの機能を有効にするために、フォーカスを設定
        self.view.setFocusPolicy(Qt.FocusPolicy.WheelFocus)

        # メニュー
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu("画面")
        brushes  = mainMenu.addMenu("ツール")
        poseMenu = mainMenu.addMenu("検知")

        # アクション登録
        loadAction = QAction(QIcon("icons/load-button.svg"), "読込",self)
        loadAction.setShortcut("L")
        fileMenu.addAction(loadAction)
        loadAction.triggered.connect(self.load)

        saveAction = QAction(QIcon("icons/save-button.svg"), "保存",self)
        saveAction.setShortcut("S")
        fileMenu.addAction(saveAction)
        saveAction.triggered.connect(self.save)

        clearAction = QAction(QIcon("icons/delete-button.png"), "クリア", self)
        clearAction.setShortcut("C")
        fileMenu.addAction(clearAction)
        clearAction.triggered.connect(self.clear)

        # Ctrl+C, Ctrl+V
        copiedAction = QAction("バッファにコピー", self)
        #copiedAction.setShortcut("Ctrl+C") ショートカットは登録済み
        fileMenu.addAction(copiedAction)
        copiedAction.triggered.connect(self.canvas.copied)  # canvasのメソッドを直接接続

        pastedAction = QAction("バッファから貼付け", self)
        #pastedAction.setShortcut("Ctrl+V")
        fileMenu.addAction(pastedAction)
        pastedAction.triggered.connect(self.canvas.pasted)  # canvasのメソッドを直接接続

        # ツールメニュー
        pix1Action = QAction( QIcon("icons/pixel-1.svg"), "1px", self)
        pix1Action.setShortcut("1")
        brushes.addAction(pix1Action)

        pix3Action = QAction( QIcon("icons/pixel-3.svg"), "3px", self)
        pix3Action.setShortcut("3")
        brushes.addAction(pix3Action)

        pix5Action = QAction( QIcon("icons/pixel-5.svg"), "5px", self)
        pix5Action.setShortcut("Q")
        brushes.addAction(pix5Action)

        pix10Action = QAction( QIcon("icons/pixel-10.svg"), "10px", self)
        pix10Action.setShortcut("W")
        brushes.addAction(pix10Action)

        pix20Action = QAction( QIcon("icons/pixel-20.svg"), "20px", self)
        pix20Action.setShortcut("E")
        brushes.addAction(pix20Action)

        fillAction = QAction( QIcon("icons/fill.svg"), "フィル", self)
        fillAction.setShortcut("F")
        brushes.addAction(fillAction)

        drawAction = QAction( QIcon("icons/path.svg"), "パス", self)
        drawAction.setShortcut("D")
        brushes.addAction(drawAction)

        pix1Action.triggered.connect(lambda: self.canvas.set_pen_size(1))   # 極細
        pix3Action.triggered.connect(lambda: self.canvas.set_pen_size(3))   # 細１
        pix5Action.triggered.connect(lambda: self.canvas.set_pen_size(5))   # 細２
        pix10Action.triggered.connect(lambda: self.canvas.set_pen_size(10)) # 太
        pix20Action.triggered.connect(lambda: self.canvas.set_pen_size(20)) # 極太
        fillAction.triggered.connect(self.canvas.setFillMode)
        drawAction.triggered.connect(self.canvas.setDrawMode)

        # ポーズ検知メニュー
        # 機能1: 2D骨格・顔メッシュ・手をキャンバスに重ね描き
        pose2dAction = QAction( QIcon("icons/poseDetect.svg"), "画像に重ね描き", self)
        pose2dAction.setShortcut("A")
        poseMenu.addAction(pose2dAction)
        pose2dAction.triggered.connect(self.detect_pose_2d)

        # 機能2: 3D座標をPLYに出力
        pose3dAction = QAction(QIcon("icons/save-button.svg"), "3D座標をPLY出力", self)
        pose3dAction.setShortcut("X")
        poseMenu.addAction(pose3dAction)
        pose3dAction.triggered.connect(self.export_to_file)

        # ヒント表示
        hintAction = QAction("ヒント", self)
        hintAction.triggered.connect(self.showHint)
        mainMenu.addAction(hintAction)

    # 読込
    def load(self, file_path):

        # 直前のブラシ／フィルにかかわらずブラシを初期化
        QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
        QApplication.processEvents()   # カーソル変更をすぐに反映
        self.canvas.brushAgain()

        if file_path:
            filePath = file_path
        else:
            # ファイルダイアログを開き、画像ファイルを選択
            settings = QSettings("forTrace", "settings")
            #last_open_dir = settings.value("last_open_img_dir", os.getcwd())
            last_path = settings.value("last_open_img_dir", "")
            filePath, _ = QFileDialog.getOpenFileName(
                self,
                "画像を読み込む",
                os.path.dirname(last_path),
                "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*.*)",
            )

        if not filePath:
            return

        # 読込みが成功したらディレクトリを保存
        settings = QSettings("forTrace", "settings")
        settings.setValue("last_open_img_dir", filePath)
        #settings.sync()

        if not self.canvas.load_image_to_canvas(filePath):
            QMessageBox.warning(self, "エラー", "画像の読み込みに失敗しました。")

    
    # 保存
    def save(self):
        # 直前のブラシ／フィルにかかわらずブラシを初期化
        QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
        QApplication.processEvents()   # カーソル変更をすぐに反映
        self.canvas.brushAgain()

        # ファイルダイアログが出るのを回避（上書き保存もどき。下の外部コマンド実行時に便利）
        #filePath = 'trace.bmp'
        filePath, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG(*.png);;JPEG(*.jpg *.jpeg);;BMP(*.bmp);;All Files(*.*) ")
        if filePath == "":
            return

        # キャンバスからQPixmapを取得
        pixmap = self.canvas.pixmap()
        if pixmap.isNull():
            # pixmapが存在しない場合は警告を表示して終了
            QMessageBox.warning(self, "エラー", "保存する画像がありません。")
            return
        pixmapSmall = pixmap.scaled(598, 415, Qt.AspectRatioMode.KeepAspectRatio)
        pixmapSmall.save(filePath)   # 元サイズはトレースした時ギザギザが多すぎるので縮小して保存

        '''
        2026.07.29
        バッファ経由でInkscapeに持って行くことにしたので、トレース用中間ファイルは作成しないことにした
        # 外部コマンド（potrace, sed, autotrace）でトレース実行
        # potrace 実行
        cmd = 'potrace --svg --output trace1.svg trace.bmp'
        subprocess.call(shlex.split(cmd))
        # サイズ単位をpxに変更
        subprocess.call(['sed', '-i', 's/pt"/px"/g', 'trace1.svg'])

        # jpg...ペン入れ後のビットマップ
        cmd = 'magick trace.bmp trace.jpg'
        subprocess.call(shlex.split(cmd))

        # autotrace
        cmd = 'autotrace -centerline -output-format svg -output-file trace2.svg trace.bmp'
        subprocess.call(shlex.split(cmd))
        '''

    # クリア
    def clear(self):
        self.canvas.clear_canvas()

    # パレット
    def add_palette_buttons(self, layout):
        for c in COLORS:
            b = QPaletteButton(c)
            b.pressed.connect(lambda c=c: self.canvas.set_pen_color(c))
            layout.addWidget(b)

    # ポーズ検知: 2D骨格をキャンバスに重ね描き -------------------------------
    def detect_pose_2d(self):
        """現在のキャンバス画像を2D骨格を重ねた絵に入れ替える"""
        pixmap = self.canvas.pixmap()

        # 実行中はカーソルを待機状態に（rtmlibは数秒かかる場合がある）
        #QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        #QApplication.processEvents()   # カーソル変更をすぐに反映

        try:
            result_pixmap = fpd.detect_pose_on_canvas(pixmap)
        finally:
            QApplication.restoreOverrideCursor()

        if result_pixmap is not None:
            self.canvas.saveUndo()          # 骨格描画前の状態を Undo 履歴に保存
            self.canvas.image = result_pixmap
            self.canvas.setPixmap(result_pixmap)
            self.canvas.update()
        else:
            QMessageBox.information(
                self, "失敗",
                "検知できません。"
            )

    # ポーズ検知: 3D座標をFileに出力 → Blender -----------------------------
    def export_to_file(self):
        ''' ファイル書き出し'''
        pixmap = self.canvas.pixmap()
        success = fpd.export_to_file(pixmap)

        # 実行中はカーソルを待機状態に（rtmlibは数秒かかる場合がある）
        #QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        #QApplication.processEvents()   # カーソル変更をすぐに反映

        if success:
            QMessageBox.information(
                self, "PLY出力完了",
                "Blenderで auto_skeleton.py が実行できます。"
            )
        else:
            QMessageBox.warning(self, "失敗", "検知/書出しができません。")

    def showHint(self):
        QMessageBox.information(
            self,
            "ヒント",  # タイトル
            "Ctrlキーとの組合せで以下の操作ができます。\n"
            "・Ctrl + C  クリップボードへ画像をコピー\n"
            "・Ctrl + V  クリップボードから画像貼付け\n"
            "・Ctrl + Z  描画を取り消して直前に戻る\n"
        )

#.......................................................................#
# アプリケーションのエントリーポイント
if __name__ == "__main__":
    # コマンドライン引数にファイルパスが指定されているか確認
    app = QApplication(sys.argv)
    window = MainWindow()
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        window.load(file_path)
    window.show()
    #sys.exit(app.exec_())
    sys.exit(app.exec())
