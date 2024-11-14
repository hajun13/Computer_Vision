from PyQt5.QtWidgets import * 
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QImage, QIcon, QPixmap
import cv2 as cv
import numpy as np 
import sys
import platform

class Panorama(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('파노라마 영상')
        self.setGeometry(200, 200, 800, 500)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        self.label = QLabel("환영합니다! 파노라마 영상을 생성해 보세요.")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 16px; padding: 10px;")
        main_layout.addWidget(self.label)

        self.thumbnailList = QListWidget()
        self.thumbnailList.setFixedHeight(120)
        self.thumbnailList.setViewMode(QListWidget.IconMode)
        self.thumbnailList.setIconSize(QSize(100, 100))
        self.thumbnailList.setSpacing(10)
        main_layout.addWidget(self.thumbnailList)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        self.collectButton = QPushButton("영상 수집")
        self.autoCaptureButton = QPushButton("자동 수집 시작")
        self.showButton = QPushButton("영상 보기")
        self.stitchButton = QPushButton("봉합")
        self.saveButton = QPushButton("저장")
        self.quitButton = QPushButton("나가기")

        button_style = """
            QPushButton {
                font-size: 14px;
                padding: 10px 20px;
                border: 1px solid #555;
                border-radius: 10px;
                background-color: #4CAF50;
                color: white;
            }
            QPushButton:disabled {
                background-color: #A5D6A7;
            }
        """
        for button in [self.collectButton, self.autoCaptureButton, self.showButton, self.stitchButton, self.saveButton, self.quitButton]:
            button.setStyleSheet(button_style)

        button_layout.addWidget(self.collectButton)
        button_layout.addWidget(self.autoCaptureButton)
        button_layout.addWidget(self.showButton)
        button_layout.addWidget(self.stitchButton)
        button_layout.addWidget(self.saveButton)
        button_layout.addWidget(self.quitButton)
        main_layout.addLayout(button_layout)

        self.showButton.setEnabled(False)
        self.stitchButton.setEnabled(False)
        self.saveButton.setEnabled(False)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.autoCapture)

        self.collectButton.clicked.connect(self.collectFunction)
        self.autoCaptureButton.clicked.connect(self.toggleAutoCapture)
        self.showButton.clicked.connect(self.showFunction)
        self.stitchButton.clicked.connect(self.stitchFunction)
        self.saveButton.clicked.connect(self.saveFunction)
        self.quitButton.clicked.connect(self.quitFunction)

        self.imgs = []

    def collectFunction(self):
        self.showButton.setEnabled(False)
        self.stitchButton.setEnabled(False)
        self.saveButton.setEnabled(False)
        self.label.setText('c를 여러번 눌러 수집하고 끝나면 q를 눌러 비디오를 끕니다.')

        if platform.system() == "Windows":
            self.cap = cv.VideoCapture(0, cv.CAP_DSHOW)
        else:
            self.cap = cv.VideoCapture(0)
        
        if not self.cap.isOpened(): 
            sys.exit('카메라 연결 실패')

        self.imgs = []
        while True:
            ret, frame = self.cap.read()
            if not ret: 
                break

            cv.imshow('video display', frame)

            key = cv.waitKey(1)
            if key == ord('c'):
                self.addThumbnail(frame)
                self.imgs.append(frame)

            elif key == ord('q'):
                self.cap.release()
                cv.destroyWindow('video display')
                break

        if len(self.imgs) >= 2:
            self.showButton.setEnabled(True)
            self.stitchButton.setEnabled(True)
            self.saveButton.setEnabled(True)

    def toggleAutoCapture(self):
        if self.timer.isActive():
            self.timer.stop()
            self.autoCaptureButton.setText("자동 수집 시작")
        else:
            # Windows에서는 CAP_DSHOW 사용, macOS/Linux에서는 사용하지 않음
            if platform.system() == "Windows":
                self.cap = cv.VideoCapture(0, cv.CAP_DSHOW)
            else:
                self.cap = cv.VideoCapture(0)

            if not self.cap.isOpened():
                sys.exit('카메라 연결 실패')
            self.timer.start(2000) 
            self.autoCaptureButton.setText("자동 수집 중지")

    def autoCapture(self):
        ret, frame = self.cap.read()
        if ret:
            self.addThumbnail(frame)
            self.imgs.append(frame)
            self.label.setText(f"자동 수집 중... 수집된 이미지: {len(self.imgs)}장")
            if len(self.imgs) >= 2:
                self.showButton.setEnabled(True)
                self.stitchButton.setEnabled(True)
                self.saveButton.setEnabled(True)

    def addThumbnail(self, image):
        height, width, channel = image.shape
        bytesPerLine = 3 * width
        qImg = QImage(image.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()
        icon = QIcon(QPixmap.fromImage(qImg).scaled(100, 100, Qt.KeepAspectRatio))
        item = QListWidgetItem(icon, "")
        self.thumbnailList.addItem(item)

    def showFunction(self):
        self.label.setText(f'수집된 영상은 {len(self.imgs)}장입니다.')
        stack = cv.resize(self.imgs[0], dsize=(0, 0), fx=0.25, fy=0.25)
        for i in range(1, len(self.imgs)):
            stack = np.hstack((stack, cv.resize(self.imgs[i], dsize=(0, 0), fx=0.25, fy=0.25)))
        cv.imshow("Image collection", stack)

    def stitchFunction(self):
        stitcher = cv.Stitcher_create()
        status, self.img_stitched = stitcher.stitch(self.imgs)
        if status == cv.STITCHER_OK:
            cv.imshow("Image stitched panorama", self.img_stitched)
        else:
            if platform.system() == "Windows":
                import winsound
                winsound.Beep(1000, 500)
            else:
                QMessageBox.warning(self, "Error", "파노라마 제작에 실패했습니다. 다시 시도하세요.")
            self.label.setText('파노라마 제작에 실패했습니다. 다시 시도하세요.')

    def saveFunction(self):
        fname, _ = QFileDialog.getSaveFileName(self, "파일 저장", './', "Images (*.png *.xpm *.jpg)")
        if fname: 
            cv.imwrite(fname, self.img_stitched)

    def quitFunction(self):
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        cv.destroyAllWindows()
        self.close()

app = QApplication(sys.argv)
win = Panorama()
win.show()
app.exec_()
