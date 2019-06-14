#!/usr/bin/env python
# -*- coding: utf-8 -*-



#########################################################################################################################
# IMPORTATION
#########################################################################################################################
import sys
sys.path.insert(0, './Dependencies_import')


import time
import numpy as np
import matplotlib.pyplot as plt
import cv2
import pyqtgraph as pg

import PyQt5
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication, QLineEdit, QHBoxLayout, QSpinBox
from PyQt5.QtCore import Qt, QThread, QTimer, QObject, pyqtSignal, pyqtSlot


from s_LogDisplay_class               import LogDisplay
from Simu_camera                      import SimuCamera

#########################################################################################################################
# FUNCTIONS
#########################################################################################################################

class Movie(QObject):
    # --- signal perso --- #
    newshot  = pyqtSignal()
    finished = pyqtSignal()
    # ---  --- #
    def __init__(self, fps=2., camera=None, view=None):
        super().__init__()
        self.camera   = camera
        self.view     = view
        self.fps      = fps
        self.acqutime = 10 #s

    def run(self):
        self.camera.acquire_movie(200)

    @pyqtSlot()
    def continuous_view(self):
        self.continue_ = True
        i = 0
        while self.continue_ and i<(self.acqutime*self.fps) :
            time.sleep(1/self.fps)
            self.newshot.emit()
            print(i)
            i += 1
        self.finished.emit()

    def stopMovie(self):
        self.continue_ = False

class StartWindow(QMainWindow):
    def __init__(self, camera=None, log=None):
        super().__init__()
        # --- camera related attriute --- #
        self.camera     = camera
        # --- image aquisition --- #
        self.image_view = pg.ImageView()
        # --- color acuisition --- #
        self.colordic = {}
        self.colordic['grey'] = cv2.COLOR_BGR2GRAY
        # ---  --- #
        if log != None:
            self.log = log
        else:
            self.log = LogDisplay()
        # ---  --- #
        self.initUI()

    def initUI(self):
        self.central_widget = QWidget()
        self.central_widget.setMinimumWidth(400)
        self.central_widget.setMinimumHeight(400)
        #self.initView()
        # --- button widget --- #
        self.button_min     = QPushButton('Get Minimum')
        self.button_max     = QPushButton('Get Maximum')
        self.button_frame   = QPushButton('Acquire Frame', self.central_widget)
        self.button_movie   = QPushButton('Start Movie', self.central_widget)
        self.button_movie_stop = QPushButton('Stop  Movie', self.central_widget)
        # ---  --- #
        self.fps         = 10
        self.fps_input   = QSpinBox()
        self.fps_input.setRange(1, 48)
        self.fps_input.setValue(self.fps)
        # --- layout --- #
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.addWidget(self.button_frame)
        hlayout = QHBoxLayout()
        hlayout.addWidget( self.button_movie )
        hlayout.addWidget( self.fps_input )
        hlayout.addWidget( self.button_movie_stop )
        self.layout.addLayout(hlayout)
        self.layout.addWidget(self.image_view)
        self.setCentralWidget(self.central_widget)
        # --- connections --- #
        self.button_max.clicked.connect(self.button_clicked)
        self.button_frame.clicked.connect(self.update_image)
        self.button_movie.clicked.connect(self.start_movie)
        self.button_movie_stop.clicked.connect(self.stop_movie)
        self.fps_input.valueChanged.connect(self.setFPS)
        # ---  --- #
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_movie)

    def initView(self):
        self.image_view.setColorMap(self.cmap_view)

    def button_clicked(self):
        print('Button Clicked')

    def setFPS(self):
        self.fps = self.fps_input.value()

    @pyqtSlot()
    def update_image(self):
        frame = self.camera.get_frame()
        self.image_view.setImage(frame.T)

    def update_movie(self):
        self.image_view.setImage(self.camera.last_frame.T)

    def start_movie(self):
        # ---  --- #
        self.thread = QThread()
        self.thread.setTerminationEnabled(True)
        self.movie  = Movie(fps=self.fps)
        self.image_view.play(self.fps)
        # --- connect --- #
        self.movie.moveToThread(self.thread)
        self.thread.started.connect(self.movie.continuous_view)
        self.movie.newshot.connect(self.update_image)
        self.movie.finished.connect(self.thread.quit)
        # ---  --- #
        self.thread.start()

    def stop_movie(self):
        self.movie.stopMovie()

#########################################################################################################################
# CODE
#########################################################################################################################

##### PyQt GUI application #####





if __name__ == '__main__':
    print('OpenCV 2 version: ',cv2.__version__)
    print('STARTING')
    camera = SimuCamera(0)
    camera.__str__()

    app = QApplication([])
    start_window = StartWindow(camera)
    start_window.show()
    app.exit(app.exec_())
    print('Close camera')
    camera.close_camera()

    print('FINISHED')
