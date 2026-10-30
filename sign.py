import cv2
import sqlite3
import os
import numpy as np
from insightface.app import FaceAnalysis
from datetime import datetime

FACE_DIR = "./face_db"
DB_PATH = "attendance.db"
SIM_THRESHOLD = 0.65
COOLDOWN_SEC = 30

# 文件夹英文名 -> 显示中文名字，按需增改
name_map = {
    "hzp": "黄祖培",
    "cr": "池锐"
}

app = FaceAnalysis(providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))

# ========== 加载底库：从本地已有的图片加载，不需要摄像头采集 ==========
face_lib = {}
for dir_name in os.listdir(FACE_DIR):
    person_folder = os.path.join(FACE_DIR, dir_name)
    if not os.path.isdir(person_folder):
        continue
    emb_list = []
    for fname in os.listdir(person_folder):
        if fname.lower().endswith((".jpg", ".jpeg", ".png")):
            full_path = os.path.join(person_folder, fname)
            raw = np.fromfile(full_path, dtype=np.uint8)
            img = cv2.imdecode(raw, cv2.IMREAD_COLOR)
            if img is None:
                continue
            faces = app.get(img)
            if len(faces) > 0:
                emb_list.append(faces[0].embedding)
    if len(emb_list) > 0:
        face_lib[dir_name] = np.mean(emb_list, axis=0)

# 签到数据库
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    sign_time TEXT
)
''')
conn.commit()
last_sign = {}

def cos_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def sign_user(name):
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    ts = now.timestamp()
    if name in last_sign and ts - last_sign[name] < COOLDOWN_SEC:
        return False
    cur.execute("INSERT INTO attendance(username, sign_time) VALUES (?,?)", (name, now_str))
    conn.commit()
    last_sign[name] = ts
    print(f"✅ 签到成功：{name}  {now_str}")
    return True

if __name__ == "__main__":
    print("===== 实时摄像头人脸签到【底库为本地图片，无需采集脚本】 =====")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 摄像头打开失败")
        exit()

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        faces = app.get(frame)
        for face in faces:
            feat = face.embedding
            bbox = face['bbox'].astype(int)
            best_key = None
            best_score = 0
            for key, db_feat in face_lib.items():
                score = cos_sim(feat, db_feat)
                if score > SIM_THRESHOLD and score > best_score:
                    best_score = score
                    best_key = key
            if best_key is not None:
                display_name = name_map.get(best_key, best_key)
                sign_user(display_name)
                cv2.putText(frame, display_name, (bbox[0], bbox[1]-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
                cv2.rectangle(frame, (bbox[0],bbox[1]), (bbox[2],bbox[3]), (0,255,0), 2)
            else:
                cv2.putText(frame, "unknown", (bbox[0], bbox[1]-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
                cv2.rectangle(frame, (bbox[0],bbox[1]), (bbox[2],bbox[3]), (0,0,255), 2)

        cv2.imshow("签到画面 | 按 q 退出", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    conn.close()