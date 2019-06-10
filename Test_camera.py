#!/usr/bin/env python
# -*- coding: utf-8 -*-



#########################################################################################################################
# IMPORTATION
#########################################################################################################################

import numpy as np
import cv2
print('OpenCV 2 version: ',cv2.__version__)

import PyQt5


#########################################################################################################################
# Code
#########################################################################################################################
print('STARTING')

##### Camera communication #####

cap = cv2.VideoCapture(0)
ret, frame = cap.read()
cap.release()

print(np.min(frame))
print(np.max(frame))


# --- continuous feed --- #

cap = cv2.VideoCapture(0)


while False:#(True):
    # Capture frame-by-frame
    ret, frame = cap.read()

    # Our operations on the frame come here
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Display the resulting frame
    cv2.imshow('frame',gray)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()




##### PyQt GUI application #####
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton





class Camera:
    def __init__(self, cam_num=-1):
        self.cam_num = cam_num
        self.cap     = None
        # ---  --- #
        self.initialize()

    def initialize(self):
        self.cap = cv2.VideoCapture(self.cam_num)

    def __str__(self):
        return 'OpenCV Camera number {}'.format(self.cam_num)

    def get_frame(self):
        ret, self.last_frame = self.cap.read()
        return self.last_frame

    def acquire_movie(self, num_frames):
        movie = []
        for _ in range(num_frames):
            movie.append(self.get_frame())
        return movie

    def set_brightness(self, value):
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, value)

    def get_brightness(self):
        return self.cap.get(cv2.CAP_PROP_BRIGHTNESS)

    def close_camera(self):
        self.cap.release()



from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication
from pyqtgraph import ImageView

class StartWindow(QMainWindow):
    def __init__(self, camera = None):
        super().__init__()
        # --- camera related attriute --- #
        self.camera     = camera
        # --- image aquisition --- #
        self.image_view = ImageView()
        # ---  --- #
        self.initUI()

    def initUI(self):
        self.central_widget = QWidget()
        # --- button widget --- #
        self.button_min     = QPushButton('Get Minimum', self.central_widget)
        self.button_max     = QPushButton('Get Maximum', self.central_widget)
        self.button_frame   = QPushButton('Acquire Frame', self.central_widget)
        self.button_movie   = QPushButton('Start Movie', self.central_widget)
        # --- layout --- #
        self.layout = QVBoxLayout(self.central_widget)
        #self.layout.addWidget(self.button_min)
        #self.layout.addWidget(self.button_max)
        self.layout.addWidget(self.button_frame)
        self.layout.addWidget(self.button_movie)
        self.setCentralWidget(self.central_widget)
        self.layout.addWidget(self.image_view)
        # --- connections --- #
        self.button_max.clicked.connect(self.button_clicked)
        self.button_frame.clicked.connect(self.update_image)

    def button_clicked(self):
        print('Button Clicked')

    def update_image(self):
        frame = self.camera.get_frame()
        self.image_view.setImage(frame.T)




if __name__ == '__main__':
    camera = Camera(0)
    camera.initialize()

    app = QApplication([])
    start_window = StartWindow(camera)
    start_window.show()
    app.exit(app.exec_())

print('FINISHED')
