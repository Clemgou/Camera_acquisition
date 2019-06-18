#!/usr/bin/env python
# -*- coding: utf-8 -*-



#########################################################################################################################
# IMPORTATION
#########################################################################################################################
import sys
import PyQt5
from PyQt5.QtWidgets import QWidget, QFrame, QApplication
from PyQt5.QtWidgets import QVBoxLayout,QHBoxLayout,QSplitter,QGridLayout
from PyQt5.QtWidgets import QLabel, QPushButton, QLineEdit, QSpinBox
from PyQt5.QtCore    import Qt, QThread, QTimer, QObject, pyqtSignal, pyqtSlot, QRect
from PyQt5.QtGui     import QPainter


import numpy as np
import pyqtgraph as pg


from s_LogDisplay_class               import LogDisplay
from s_Workers_class                  import *
from s_Miscellaneous_functions        import *
from s_SimuCamera_class               import SimuCamera


import time
#########################################################################################################################
# FUNCTIONS
#########################################################################################################################

class CameraDisplay(QWidget):
    def __init__(self, camera=None, log=None, fps=10.):
        super().__init__()
        # ---  --- #
        if log != None:
            self.log = log
        else:
            self.log = LogDisplay()
        # --- default --- #
        self.fps       = fps
        self.normalise_hist = True
        self.cmap      = 'jet'
        # --- main attriute --- #
        self.camera    = camera
        self.contview  = ContinuousView(fps=self.fps)
        self.timer     = pg.QtCore.QTimer() #QTimer()# pg.QtCore.QTimer()
        self.qlabl_max = QLabel()
        self.isOn      = False
        self.frame     = None
        # --- color acuisition --- #
        self.initColorDic()
        # ---  --- #
        self.initUI()

    def initUI(self):
        # ---  --- #
        self.layout      = QVBoxLayout(self)
        self.initView()
        # --- button widget --- #
        self.button_startstop = QPushButton('Start/Stop')
        self.button_startstop.setStyleSheet("background-color: red")
        self.button_nextFrame = QPushButton('Next frame')
        # ---  --- #
        self.fps_input   = QSpinBox()
        self.fps_input.setRange(1, 48)
        self.fps_input.setValue(self.fps)
        # --- connections --- #
        self.button_startstop.clicked.connect(self.startStop_continuous_view)
        self.fps_input.valueChanged.connect(self.setFPS)
        self.button_nextFrame.clicked.connect( self.update_frame )
        # --- layout --- #
        grid = QGridLayout()
        grid.addWidget( self.button_startstop, 0,0)
        grid.addWidget( self.button_nextFrame, 0,1)
        grid.addWidget( QLabel('fps :')      , 0,2)
        grid.addWidget( self.fps_input       , 0,3)
        grid.addWidget( QLabel('value max:') , 0,5)
        grid.addWidget( self.qlabl_max       , 0,6)
        self.layout.addLayout(grid)
        self.layout.addWidget(self.image_view)
        self.setLayout(self.layout)
        # ---  --- #

    def initColorDic(self):
        self.colordic = {}
        # --- jet-like cmap --- #
        alpha     = 1.0
        positions = [0.2, 0.5, 0.75, 1.0]
        colors    = [[0,0,1.,alpha],[0,1.,1.,alpha],[1.,1.,0,alpha],[170/255,0,0,alpha]] #colors    = ['#0000ff', '#00ffff', '#ffff00', '#aa0000']
        self.colordic['jet'] = pg.ColorMap(positions, colors)
        # --- jet reversed cmap --- #
        positions_r = [1-p_ for p_ in positions]
        self.colordic['jet_r'] = pg.ColorMap(positions_r, colors)
        # --- plasma cmap --- #
        self.colordic['plasma'] = generatePgColormap('plasma')

    def initView(self):
        self.image_view     = pg.ImageView()
        # ---  --- #
        self.image_view.setColorMap(self.colordic[self.cmap])
        self.image_view.setLevels(0,255)
        self.image_view.getHistogramWidget().item.setHistogramRange(0,255)
        # ---  --- #
        self.image_view.setMinimumWidth(800)
        self.image_view.setMinimumHeight(600)

    def hideHistogram(self):
        self.image_view.ui.histogram.hide()

    def hidePlotButtons(self):
        self.image_view.ui.roiBtn.hide()
        self.image_view.ui.menuBtn.hide()

    def setFPS(self):
        self.fps = self.fps_input.value()
        self.contview.setFPS( self.fps )
        self.timer.setInterval(1e3/self.fps)

    def update_frame(self):
        self.frame = self.camera.get_frame(mode='Grey')
        self.image_view.setImage(self.frame.T, autoHistogramRange=False, autoLevels=False)
        self.qlabl_max.setText( str(np.max(self.frame)) )

    def startStop_continuous_view(self):
        if  self.isOn:
            self.stop_continuous_view()
            self.button_startstop.setStyleSheet("background-color: red")
            self.button_nextFrame.setFlat(False)
            self.button_nextFrame.setEnabled(True)
        else:
            self.start_continuous_view()
            self.button_startstop.setStyleSheet("background-color: green")
            self.button_nextFrame.setFlat(True)
            self.button_nextFrame.setEnabled(False)

    def start_continuous_view(self):
        if   True:
            self.start_continuous_view_qtimer()
        elif False:
            self.start_continuous_view_qthread()
        # ---  --- #
        self.isOn = True

    def stop_continuous_view(self):
        if   True:
            self.stop_continuous_view_qtimer()
        elif False:
            self.stop_continuous_view_qthread()
        # ---  --- #
        self.isOn = False

    def start_continuous_view_qthread(self):
        # ---  --- #
        self.thread = QThread()
        self.thread.setTerminationEnabled(True)
        # --- connect --- #
        self.contview.moveToThread(self.thread)
        self.thread.started.connect(self.contview.startFeed)
        self.contview.newshot.connect(self.update_image)
        self.contview.finished.connect(self.thread.quit)
        # ---  --- #
        self.thread.start()

    def stop_continuous_view_qthread(self):
        self.contview.stopFeed()

    def start_continuous_view_qtimer(self):
        # ---  --- #
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1e3/self.fps) #ms

    def stop_continuous_view_qtimer(self):
        self.timer.stop()

#########################################################################################################################
# CODE
#########################################################################################################################
if __name__ == '__main__':
    print('STARTING')
    dir_path = '/home/cgou/ENS/STAGE/M2--stage/Camera_acquisition/Micellaneous/Camera_views/'
    camera   = Camera(cam_id=0)
    if not camera.isCameraInit:
        camera = SimuCamera(0, directory_path=dir_path)
        camera.__str__()

    app = QApplication([])
    start_window = CameraDisplay(camera)
    start_window.show()
    app.exit(app.exec_())
    print('Close camera')
    camera.close_camera()

    print('FINISHED')
