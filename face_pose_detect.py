# face_pose_detect.py
# forTrace.py から呼び出されるポーズ検知モジュール
# 機能1: キャンバスに2D骨格を重ね描き
# 機能2: 3D座標をPLYファイルに出力

from PySide6.QtGui import QPixmap, QImage

import cv2
import numpy as np

from rtmlib import PoseTracker, Wholebody3d, draw_skeleton
import onnxruntime as ort
ort.set_default_logger_severity(3)

# 3D 用トラッカーは毎回作ると重いので、可能なら関数外で使い回し
rtmw3d_tracker = PoseTracker(
    Wholebody3d,
    det_frequency=1,
    tracking=False,
    to_openpose=False,
    backend="onnxruntime",
    device="cuda",
)

# ─────────────────────────────────────────
# 機能1: コネクションをキャンバスに重ね描き
# ─────────────────────────────────────────

from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QFileDialog
import numpy as np
import cv2
from rtmlib import PoseTracker, Wholebody3d, draw_skeleton
import onnxruntime as ort

ort.set_default_logger_severity(3)

# 3D 用トラッカーは毎回作ると重いので、可能なら関数外で使い回し
rtmw3d_tracker = PoseTracker(
    Wholebody3d,
    det_frequency=1,
    tracking=True,
    to_openpose=False,
    backend="onnxruntime",
    device="cuda",
)

def pixmap_to_bgr(pixmap: QPixmap) -> np.ndarray:
    # QPixmap を QImage に変換
    qimg: QImage = pixmap.toImage()

    # Enumの指定を PySide6 形式に変更
    qimg = qimg.convertToFormat(QImage.Format_RGBA8888)  # または QImage.Format_RGBA8888
    

    w, h = qimg.width(), qimg.height()

    # PySide6 では bits() が memoryview を返すため np.frombuffer を使用
    ptr = qimg.bits()
    arr = np.frombuffer(ptr, dtype=np.uint8).reshape((h, w, 4))  # RGBA

    # OpenCV用 (BGR) に変換
    bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)

    # bgrの色を調べてほぼ真っ白なら None を返す
    threshold = 250
    if np.all(bgr >= threshold):
        return None
    else:
        return bgr

def bgr_to_pixmap(img_bgr: np.ndarray) -> QPixmap:
    h, w = img_bgr.shape[:2]
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    qimg = QImage(img_rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888)
    # QImage は参照なので、コピーしてから使うと安全
    return QPixmap.fromImage(qimg).copy()

def detect_pose_on_canvas(pixmap: QPixmap) -> QPixmap | None:
    # Pixmap -> OpenCV(BGR)
    img_bgr = pixmap_to_bgr(pixmap)

    # 推論
    try:
        keypoints_3d, scores, _, keypoints_2d = rtmw3d_tracker(img_bgr)
    except ValueError:
        return

    # 可視化（2Dプレビュー）
    img_show = img_bgr.copy()
    img_show = draw_skeleton(
        img_show,
        keypoints_2d,
        scores,
        openpose_skeleton=False
    )

    # 戻り値をQPixmapへ
    return bgr_to_pixmap(img_show)

# ─────────────────────────────────────────
# 機能2: 3D座標からPLYファイルの作成保存
# ─────────────────────────────────────────

def export_to_file(pixmap):
    # Pixmap -> OpenCV(BGR)
    img_bgr = pixmap_to_bgr(pixmap)    

    # 推論
    try:
        keypoints_3d, scores, _, keypoints_2d = rtmw3d_tracker(img_bgr)
    except ValueError:
        return False

    # fileダイアログ
    file_path, _ = QFileDialog.getSaveFileName(
        None,               # parent
        "PLY保存先を選択",    # caption
        "pose_result.ply",  # dir
        "PLY Files (*.ply);;All Files (*.*)",   # filter
        )
    
    if not file_path:
        return False

    # 骨格全体の3Dデータ（1人目 [0]）をリスト形式に変換
    pose_data_3d = keypoints_3d[0].tolist()  # 133箇所 × 3座標(X, Y, Z)の配列

    # ply書き出し
    # ヘッダ部分
    writeMe = ["ply\n", "format ascii 1.0\n", "comment www.moonlight-lullaby.info\n"]
    
    comment = "comment pose\n"
    writeMe.append(comment)
    
    dataLength = str(len(pose_data_3d))
    elmVertex = "element vertex " + dataLength + "\n"   # 頂点133個
    writeMe.append(elmVertex)
    
    properties ="property float x\n" + \
                "property float y\n" + \
                "property float z\n"
    writeMe.append(properties)

    # インデックスのペアで線を描く
    # plyテキストに書く整数はこのリストの長さ
    connections= [
                    [ 50,  56], # 頭に見立てる線
                    [  4,   3], # 耳を結ぶ線
                    [  5,   6], # 肩を結ぶ線
                    [ 12,  11], # 腰を結ぶ線
                    [  6,   8], # 上腕右   Arm_R
                    [  8,  10], # 前腕右   Forearm_R
                    [112, 121], # 手右     Hand_R
                    [113, 114], # 親指右1 Thumb1_R
                    [114, 115], # 親指右2 Thumb2_R
                    [115, 116], # 親指右3 Thumb3_R
                    [117, 118], # 人差右1 Index1_R
                    [118, 119], # 人差右2 Index2_R
                    [119, 120], # 人差右3 Index3_R
                    [121, 122], # 中指右1 Middle1_R
                    [122, 123], # 中指右2 Middle2_R
                    [123, 124], # 中指右3 Middle3_R
                    [125, 126], # 薬指右1 Ring1_R
                    [126, 127], # 薬指右2 Ring2_R
                    [127, 128], # 薬指右3 Ring3_R
                    [129, 130], # 小指右1 Pinky1_R
                    [130, 131], # 小指右2 Pinky2_R
                    [131, 132], # 小指右3 Pinky3_R
                    [  5,   7], # 上腕左  Arm_L
                    [  7,   9], # 前腕左  Forearm_L
                    [ 91, 100], # 手左    Hand_L
                    [ 92,  93], # 親指左1 Thumb1_L
                    [ 93,  94], # 親指左2 Thumb2_L
                    [ 94,  95], # 親指左3 Thumb3_L
                    [ 96,  97], # 人差左1 Index1_L
                    [ 97,  98], # 人差左2 Index2_L
                    [ 98,  99], # 人差左3 Index3_L
                    [100, 101], # 中指左1 Middle1_L
                    [101, 102], # 中指左2 Middle2_L
                    [102, 103], # 中指左3 Middle3_L
                    [104, 105], # 薬指左1 Ring1_L
                    [105, 106], # 薬指左2 Ring2_L
                    [106, 107], # 薬指左3 Ring3_L
                    [108, 109], # 小指左1 Pinky1_L
                    [109, 110], # 小指左2 Pinky2_L
                    [110, 111], # 小指左3 Pinky3_L
                    [ 12,  14], # 腿右    Thigh_R
                    [ 11,  13], # 腿左    Thigh_L
                    [ 14,  16], # 脛右    Calf_R
                    [ 13,  15], # 脛左    Calf_L
                    [ 16,  20], # 足右    Foot_R
                    [ 15,  17], # 足左    Foot_L
                    [ 16,  22], # 踵右    Heel_R  要らないかも
                    [ 15,  19], # 踵左    Heel_L  要らないかも
                    [ 20,  21], # 足親指右 Toe_R
                    [ 17,  18], # 足親指左 Toe_L
                ]
    
    elmEdge = "element edge " + str(len(connections)) + "\n"
    writeMe.append(elmEdge)
    properties = "property int vertex1\n" + "property int vertex2\n"
    writeMe.append(properties)
    writeMe.append("end_header\n")
    
    # x y z 座標
    for i in pose_data_3d:
        # Blenderに持って行った時、ちょうどいいサイズ
        bx = i[0] * 0.008
        by = i[2] * 0.45
        bz = i[1] * 0.008 * -1
        
        writeMeLine = '{:.6f}'.format(bx) + ' ' + \
                      '{:.6f}'.format(by) + ' ' + \
                      '{:.6f}'.format(bz) + '\n'
        
        writeMe.append(writeMeLine)

    for j in connections:
        writeMe.append(str(j[0]) + " " + str(j[1]) + "\n")
    
    # PLYテキストファイル書き出し
    with open(file_path, "w", encoding="utf-8") as file:
        file.writelines(writeMe)
        return True
