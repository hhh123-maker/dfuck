import cv2
import os
import numpy as np

# ========== 在这里改学生名字（支持中文） ==========
student_name = "梁宇彬"
# student_name = "池锐"
# ================================================

save_root = "face_db"
save_dir = os.path.join(save_root, student_name)
os.makedirs(save_dir, exist_ok=True)

cap = cv2.VideoCapture(0)
count = 0

print("✅ 摄像头启动成功！")
print("📸 【空格】拍照保存人脸")
print("❌ 【q】退出采集")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ 读取摄像头画面失败！")
        break

    cv2.imshow("Face Capture", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord(' '):
        # 保存，用imencode兼容中文路径
        filename = f"{count}.jpg"
        full_path = os.path.join(save_dir, filename)
        success, buf = cv2.imencode(".jpg", frame)
        if success:
            buf.tofile(full_path)
            print(f"✅ 已保存：{student_name}/{filename} 第{count+1}张")
            count += 1
        else:
            print("❌ 保存失败")

    if key == ord('q'):
        print("📝 采集结束！")
        break

cap.release()
cv2.destroyAllWindows()