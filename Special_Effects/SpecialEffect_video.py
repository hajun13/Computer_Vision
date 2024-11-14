import cv2 as cv
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer
import sys
import os
import time

class VideoSpecialEffect(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('비디오 특수 효과')
        self.setGeometry(600, 300, 500, 150)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                color: #ecf0f1;
                background-color: #3498db;
                border-radius: 10px;
                padding: 10px;
            }
            QComboBox {
                font-size: 14px;
                color: #34495e;
                background-color: #ecf0f1;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c5986;
            }
            QMessageBox {
                font-size: 14px;
                color: #2c3e50;
            }
        """)

        videoButton = QPushButton('비디오 시작', self)
        videoButton.setGeometry(50, 50, 150, 40)

        self.pickCombo = QComboBox(self)
        self.pickCombo.addItems(['엠보싱', '카툰', '연필 스케치(명암)', '연필 스케치(컬러)', '유화'])
        self.pickCombo.setGeometry(210, 50, 140, 40)

        snapshotButton = QPushButton('스냅샷', self)
        snapshotButton.setGeometry(360, 100, 100, 40)

        quitButton = QPushButton('나가기', self)
        quitButton.setGeometry(360, 50, 100, 40)

        videoButton.clicked.connect(self.startVideo)
        quitButton.clicked.connect(self.quitFunction)
        snapshotButton.clicked.connect(self.takeSnapshot)

        self.special_img = None
        self.running = False 
        self.timer = QTimer(self)  
        self.timer.timeout.connect(self.updateFrame)

    def startVideo(self):
        self.cap = cv.VideoCapture(0)
        if not self.cap.isOpened():
            self.cap = cv.VideoCapture(1)
        
        self.running = True

        self.cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)

        if not self.cap.isOpened():
            QMessageBox.critical(self, "Error", "카메라를 열 수 없습니다.")
            self.running = False
            return

        self.timer.start(30)

    def updateFrame(self):
        if not self.running:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.stopVideo()
            return

        pick_effect = self.pickCombo.currentIndex()
        if pick_effect == 0:
            femboss = np.array([[-1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            gray16 = np.int16(gray)
            self.special_img = np.uint8(np.clip(cv.filter2D(gray16, -1, femboss) + 128, 0, 255))
        elif pick_effect == 1:
            self.special_img = cv.stylization(frame, sigma_s=60, sigma_r=0.45)
        elif pick_effect == 2:
            self.special_img, _ = cv.pencilSketch(frame, sigma_s=60, sigma_r=0.07, shade_factor=0.02)
        elif pick_effect == 3:
            _, self.special_img = cv.pencilSketch(frame, sigma_s=60, sigma_r=0.07, shade_factor=0.02)
        elif pick_effect == 4:
            try:
                self.special_img = cv.xphoto.oilPainting(frame, 10, 1, cv.COLOR_BGR2Lab)
            except AttributeError:
                QMessageBox.warning(self, "오류", "유화 효과를 사용할 수 없습니다. OpenCV 설치를 확인하세요.")
                self.special_img = frame

        cv.imshow('Special effect', self.special_img)
        if cv.waitKey(1) & 0xFF == ord('q'):
            self.stopVideo()

    def stopVideo(self):
        self.running = False
        self.timer.stop()
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        cv.destroyAllWindows()

    def takeSnapshot(self):
        if self.special_img is not None:
            snapshot_path = os.path.join(os.getcwd(), "snapshot.png")
            cv.imwrite(snapshot_path, self.special_img)
            QMessageBox.information(self, "스냅샷 저장됨", f"스냅샷이 {snapshot_path}에 저장되었습니다.")
        else:
            QMessageBox.warning(self, "오류", "스냅샷을 찍기 전에 비디오를 시작하세요.")

    def quitFunction(self):
        self.stopVideo()
        self.close()

app = QApplication(sys.argv)
win = VideoSpecialEffect()
win.show()
app.exec_()
