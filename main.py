import sys
import cv2
import winsound
import numpy as np
import datetime, time, os
from threading import Thread
from PyQt5.QtWidgets import QSlider
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit, QMessageBox
from PyQt5.QtCore import Qt

# Create folders
os.makedirs("recordings_full", exist_ok=True)
os.makedirs("recordings_focus", exist_ok=True)

running = False

sensitivity = 500
status_label = None 

def start_camera():
    global running
    running = True

    cap = cv2.VideoCapture(0)

    ret, frame = cap.read()
    if not ret:
        return

    h, w = frame.shape[:2]

    box_w, box_h = 200, 150
    x, y = w//2 - box_w//2, h//2 - box_h//2

    bg = None
    recording = False
    record_start = 0
    tail_time = 15
    motion_msg_time = 0

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_full = None
    out_roi = None

    sound_played = False
    while running:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        roi = gray[y:y+box_h, x:x+box_w]

        if bg is None:
            bg = roi.copy().astype("float")
            continue

        cv2.accumulateWeighted(roi, bg, 0.5)
        diff = cv2.absdiff(roi, cv2.convertScaleAbs(bg))
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]

        motion_pixels = cv2.countNonZero(thresh)
        motion_detected = motion_pixels > sensitivity
        
        if not motion_detected:
            sound_played = False
            if status_label:
                status_label.setText("Status: Idle 🟢")
            
        if motion_detected:
            motion_msg_time = time.time()
            # 🔊 Play sound only once
            if not sound_played:
                winsound.Beep(1000, 200)
                winsound.Beep(1500, 200)   # (frequency, duration)
                sound_played = True

            if not recording:
                timestamp = datetime.datetime.now().strftime("%H%M%S")
                out_full = cv2.VideoWriter(f"recordings_full/full_{timestamp}.mp4", fourcc, 20, (w, h))
                out_roi = cv2.VideoWriter(f"recordings_focus/roi_{timestamp}.mp4", fourcc, 20, (box_w, box_h))
                recording = True

            record_start = time.time()

        if recording and time.time() - record_start > tail_time:
            recording = False
            if out_full: out_full.release()
            if out_roi: out_roi.release()

      
        if recording:
            if status_label:
                status_label.setText("Status: Recording 🔴")

        # Save video
            out_full.write(frame)
            out_roi.write(frame[y:y+box_h, x:x+box_w])

            if recording:
        # 🎥 Save video
                out_full.write(frame)
                out_roi.write(frame[y:y+box_h, x:x+box_w])

            # 🕒 Current Time
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                cv2.putText(frame, current_time, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1,
                (0, 255, 0), 2)

            # ⏱ Duration
                duration = int(time.time() - record_start)
                mins = duration // 60
                secs = duration % 60

                cv2.putText(frame, f"REC {mins:02}:{secs:02}", (10, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 0, 255), 2)

                # 🔴 Blinking REC Dot
                if int(time.time()) % 2 == 0:
                    cv2.circle(frame, (150, 65), 8, (0, 0, 255), -1)


        color = (0,255,255) if not motion_detected else (0,0,255)
        cv2.rectangle(frame,(x,y),(x+box_w,y+box_h),color,2)

        if time.time() - motion_msg_time < 3:
            cv2.putText(frame,"MOTION DETECTED",(x,y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,0),2)

        cv2.imshow("SMSS", frame)

        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

def update_sensitivity(value):
    global sensitivity
    sensitivity = value
    slider_label.setText(f"Sensitivity: {value}")

# ✅ FIXED: Proper start function
def start():
    global status_label
    if status_label:
        status_label.setText("Status: Running 🟡")
    Thread(target=start_camera).start()

# ✅ FIXED: stop function
def stop():
    global running, status_label
    running = False
    if status_label:
        status_label.setText("Status: Stopped 🔴")

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.attempts = 0

        self.setWindowTitle("SMSS Login")
        self.setFixedSize(350, 220)

        # 🎨 Main Styling
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                color: white;
                font-family: Arial;
            }
            QLineEdit {
                padding: 8px;
                border-radius: 8px;
                border: 1px solid #555;
                background-color: #2c2c3e;
                color: white;
            }
            QPushButton {
                padding: 8px;
                border-radius: 10px;
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # 🧠 Title
        self.title = QLabel("🔐 Enter Password ")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title)

        # Password field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        # Login Button
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.check_password)
        layout.addWidget(self.login_btn)

        self.setLayout(layout)

        # Press Enter to login
        self.password_input.returnPressed.connect(self.check_password)
 

    def check_password(self):
     entered = self.password_input.text().strip()

     if entered == "1":
        self.close()
        window.show()
     else:
        self.attempts += 1

        if self.attempts >= 3:
            QMessageBox.critical(self, "Blocked", "Too many attempts! ❌")
            sys.exit()
        else:
            QMessageBox.warning(self, "Error", f"Wrong Password ({self.attempts}/3)")
            self.password_input.clear()   # optional (clears field)                  

# ✅ QApplication should be here (only once)
app = QApplication(sys.argv)

window = QWidget()
window.setStyleSheet("""
    background-image: url(bg.jpg);
    background-repeat: no-repeat;
    background-position: center;
""")
window.setWindowTitle("SMSS Application")
window.setGeometry(100, 100, 600, 500)

layout = QVBoxLayout()
layout.addSpacing(120)
label = QLabel("Smart Motion Surveillance System") 
label.setAlignment(Qt.AlignCenter)  
label.setStyleSheet("font-size: 20px; font-weight: bold;")
layout.addWidget(label)
layout.addStretch()

status_label = QLabel("Status: Idle 🟢")
status_label.setAlignment(Qt.AlignCenter)
status_label.setStyleSheet("font-size: 14px; color: lightgreen; font-weight: bold;")
layout.addWidget(status_label)

slider_label = QLabel("Sensitivity: 500")
slider_label.setAlignment(Qt.AlignCenter)
layout.addWidget(slider_label)

slider = QSlider(Qt.Horizontal)
slider.setMinimum(100)
slider.setMaximum(2000)
slider.setValue(500)
layout.addWidget(slider)

slider.valueChanged.connect(update_sensitivity)

btn_start = QPushButton("Start")
btn_start.setFixedSize(200, 45)
btn_start.setStyleSheet("""font-size: 16px; padding: 5px; font-weight: bold;border-radius: 10px;
    background-color: #4CAF50;
    color: white;""")
btn_start.clicked.connect(start)
layout.addWidget(btn_start,alignment=Qt.AlignCenter)

btn_stop = QPushButton("Stop")
btn_stop.setFixedSize(200, 45)
btn_stop.setStyleSheet("""font-size: 16px; padding: 5px; font-weight: bold;border-radius: 10px;
    background-color: #4CAF50;
    color: white;""")
btn_stop.clicked.connect(stop)
layout.addWidget(btn_stop,alignment=Qt.AlignCenter)

window.setLayout(layout)

login = LoginWindow()
login.show()
sys.exit(app.exec_())