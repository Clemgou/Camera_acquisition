#!/usr/bin/env python
# -*- coding: utf-8 -*-



#########################################################################################################################
# IMPORTATION
#########################################################################################################################
import sys
sys.path.insert(0, '/home/cgou/ENS/STAGE/M2--stage/CircuitsNetwork_phase_analysis') #for Simu_camera only


import time
import numpy as np
import matplotlib.pyplot as plt
import cv2
import pyqtgraph as pg

import PyQt5
from PyQt5.QtWidgets import QWidget, QFrame, QApplication
from PyQt5.QtWidgets import QVBoxLayout,QHBoxLayout,QSplitter
from PyQt5.QtWidgets import QLabel, QPushButton, QLineEdit, QSpinBox
from PyQt5.QtCore    import Qt, QThread, QTimer, QObject, pyqtSignal, pyqtSlot, QRect
from PyQt5.QtGui     import QPainter


from s_LogDisplay_class               import LogDisplay
from s_Workers_class                  import *
from Simu_camera                      import SimuCamera

#########################################################################################################################
# FUNCTIONS
#########################################################################################################################

def generatePgColormap(cm_name):
    pltMap = plt.get_cmap(cm_name)
    colors = pltMap.colors
    colors = [c + [1.] for c in colors]
    positions = np.linspace(0, 1, len(colors))
    #print(positions, colors)
    pgMap = pg.ColorMap(positions, colors)
    return pgMap


class Preview(QWidget):
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
        # --- color acuisition --- #
        self.initColorDic()
        # ---  --- #
        self.initUI()

    def initUI(self):
        # ---  --- #
        self.layout      = QVBoxLayout(self)
        self.initView()
        # --- button widget --- #
        self.button_acquire    = QPushButton('Acquire')
        self.button_start_view = QPushButton('Start'  )
        self.button_stop_view  = QPushButton('Stop '  )
        # ---  --- #
        self.fps_input   = QSpinBox()
        self.fps_input.setRange(1, 48)
        self.fps_input.setValue(self.fps)
        # --- connections --- #
        self.button_start_view.clicked.connect(self.start_continuous_view_qtimer)
        self.button_stop_view.clicked.connect(self.stop_continuous_view_qtimer)
        self.fps_input.valueChanged.connect(self.setFPS)
        self.button_acquire.clicked.connect(self.acquireFrame)
        # --- layout --- #
        hlayout1 = QHBoxLayout()
        hlayout1.addWidget( self.button_start_view )
        hlayout1.addWidget( self.button_stop_view )
        hlayout2 = QHBoxLayout()
        hlayout2.addWidget( QLabel('fps :') )
        hlayout2.addWidget( self.fps_input )
        hlayout2.addWidget( QLabel('value max:') )
        hlayout2.addWidget( self.qlabl_max )
        self.layout.addLayout(hlayout1)
        self.layout.addLayout(hlayout2)
        self.layout.addWidget(self.image_view)
        self.layout.addWidget(self.view_layout)
        self.layout.addWidget(self.button_acquire)
        self.setLayout(self.layout)
        # ---  --- #
        self.update_timer = QTimer()

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
        # --- image  widget --- #
        self.image_view     = pg.ImageView()
        # --- plot layout --- #
        self.view_layout    = pg.GraphicsLayoutWidget()
        self.plot_hist      = self.view_layout.addPlot()
        self.plot_hist.setXLink( self.image_view.getView() )
        if self.normalise_hist:
            self.plot_hist.setYRange(0, 1)
        else:
            self.plot_hist.setYRange(0, 255)
        # ---  --- #
        self.data_hist = pg.PlotDataItem()
        self.plot_hist.addItem(self.data_hist)
        # ---  --- #
        self.image_view.setColorMap(self.colordic[self.cmap])
        self.image_view.setLevels(0,255)
        self.hidePlotButtons()
        self.image_view.getHistogramWidget().item.setHistogramRange(0,255) #not working when update
        # ---  --- #
        self.view_layout.setMinimumWidth(800)
        self.view_layout.setMinimumHeight(200)
        self.image_view.setMinimumWidth(800)
        self.image_view.setMinimumHeight(400)
        # ---  --- #

    def hideHistogram(self):
        self.image_view.ui.histogram.hide()

    def hidePlotButtons(self):
        self.image_view.ui.roiBtn.hide()
        self.image_view.ui.menuBtn.hide()

    def setFPS(self):
        self.fps = self.fps_input.value()
        self.contview.setFPS( self.fps )
        self.timer.setInterval(1e3/self.fps)

    @pyqtSlot()
    def update_image(self):
        frame = self.camera.get_frame(mode='Grey')
        self.updatePlotHistogram(frame)
        self.image_view.setImage(frame.T, autoHistogramRange=False, autoLevels=False)
        self.qlabl_max.setText( str(np.max(frame)) )

    def updatePlotHistogram(self, frame):
        bckgrnd = np.mean(frame)
        frame = frame-bckgrnd
        ydata = np.sum(frame,axis=0)/frame.shape[0]
        ydata += np.max([0, np.min(ydata)])
        if self.normalise_hist:
            ydata = ydata/np.max(ydata)
        self.data_hist.setData(ydata)

    def acquireFrame(self):
        frame = self.camera.last_frame
        plt.imshow(frame, cmap=self.cmap)
        plt.show()

    def start_continuous_view(self):
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

    def stop_continuous_view(self):
        self.contview.stopFeed()

    def start_continuous_view_qtimer(self):
        # ---  --- #
        self.timer.timeout.connect(self.update_image)
        self.timer.start(1e3/self.fps) #ms

    def stop_continuous_view_qtimer(self):
        self.timer.stop()

#########################################################################################################################
# CODE
#########################################################################################################################
if __name__ == '__main__':
    print('OpenCV 2 version: ',cv2.__version__)
    print('STARTING')
    camera = SimuCamera(0)
    camera.__str__()

    app = QApplication([])
    start_window = Preview(camera)
    start_window.show()
    app.exit(app.exec_())
    print('Close camera')
    camera.close_camera()

    print('FINISHED')
