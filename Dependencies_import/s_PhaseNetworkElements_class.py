#!/usr/bin/env python
# -*- coding: utf-8 -*-



#########################################################################################################################
# IMPORTATION
#########################################################################################################################
import sys
sys.path.insert(0, '/home/cgou/ENS/STAGE/M2--stage/CircuitsNetwork_phase_analysis') #for Simu_camera only
import os


import time
import numpy as np
import itertools, operator
import matplotlib.pyplot as plt
import cv2
import pyqtgraph as pg

import PyQt5
from PyQt5.QtWidgets import QWidget, QFrame, QApplication
from PyQt5.QtWidgets import QVBoxLayout,QHBoxLayout,QSplitter, QGridLayout
from PyQt5.QtWidgets import QLabel, QPushButton, QLineEdit, QSpinBox, QComboBox, QCheckBox, QFileDialog, QTableWidget, QTableWidgetItem
from PyQt5.QtCore    import Qt, QThread, QTimer, QObject, pyqtSignal, pyqtSlot, QRect
from PyQt5.QtGui     import QPainter


from s_LogDisplay_class               import LogDisplay
from s_ToolObjects_class              import GaussianFit, SpanObject
from s_CameraDisplay_class            import CameraDisplay
from Simu_camera                      import SimuCamera

#########################################################################################################################
# FUNCTIONS
#########################################################################################################################

class PhaseNetworkElements(QWidget):
    def __init__(self, camera=None, log=None, fps=10.):
        super().__init__()
        # ---  --- #
        if log != None:
            self.log = log
        else:
            self.log = LogDisplay()
        #self.log.showLog()
        # --- default --- #
        self.fps       = fps
        self.cmap      = 'jet'
        self.normalise = True
        self.sepration = ' '
        self.param_peak= [] # a N x 3 array where each line is [x0, a, b] the parameter of the fit, N being the number of peaks.
        self.fittingtimer = pg.QtCore.QTimer()
        self.dicspan   = {}
        # --- main attriute --- #
        self.camera    = camera
        self.timer     = pg.QtCore.QTimer() #QTimer()# pg.QtCore.QTimer()
        self.qlabl_max = QLabel()
        self.dataframe = np.zeros([10,10])
        # ---  --- #
        self.initUI()

    def initUI(self):
        self.splitter      = QSplitter(PyQt5.QtCore.Qt.Horizontal)
        self.fitting_frame = None
        # ---  --- #
        self.layout      = QVBoxLayout(self)
        # --- guassian fit init --- #
        self.gaussianfit     = GaussianFit(log=self.log)
        self.gaussian_plots  = {}
        self.fittingactivate = QCheckBox()
        self.fittingactivate.setTristate(False)
        self.fittingactivate.stateChanged.connect(self.acceptOrNot)
        # --- init frames --- #
        self.initView()
        self.initVertHistogram()
        self.initParameterZone()
        # --- layout --- #
        vsplitter      = QSplitter(PyQt5.QtCore.Qt.Vertical)
        vsplitter.addWidget( self.camera_view )
        self.splitter.addWidget( vsplitter )
        self.splitter.addWidget( self.histogFrame )
        self.splitter.addWidget( self.paramFrame )
        self.layout.addWidget( self.splitter )
        self.setLayout(self.layout)
        # ---  --- #
        self.fittingtimer.start()

    def initView(self):
        self.camera_view     = CameraDisplay(camera=self.camera, log=self.log)
        # ---  --- #
        self.camera_view.image_view.setMinimumWidth(200)
        self.camera_view.image_view.setMinimumHeight(200)

    def initParameterZone(self):
        self.paramFrame = QFrame()
        # --- widgets --- #
        self.normalise_hist = QComboBox()
        self.normalise_hist.addItem('raw')
        self.normalise_hist.addItem('normalise')
        self.normalise_hist.setCurrentIndex(1)
        self.nbrpeak = QSpinBox()
        self.nbrpeak.setRange(1, 20)
        self.nbrpeak.setValue(2)
        self.histrealtime = QCheckBox()
        self.histrealtime.setTristate(False)
        self.histrealtime.setCheckState(2)
        self.setLinkToCameraTimer()
        self.button_addspan = QPushButton('add new span')
        # --- connections --- #
        self.normalise_hist.currentIndexChanged.connect(self.setModeFitting)
        self.nbrpeak.valueChanged.connect(self.updatePlots)
        self.histrealtime.stateChanged.connect( self.setLinkToCameraTimer )
        self.button_addspan.clicked.connect( self.addSpan )
        # --- make layout --- #
        grid    = QGridLayout()
        grid.addWidget(QLabel('Mode for fitting: '), 0,0)
        grid.addWidget( self.normalise_hist        , 0,1)
        grid.addWidget(QLabel('Number maximum of peaks:'), 1,0)
        grid.addWidget( self.nbrpeak                     , 1,1)
        grid.addWidget(QLabel('Continuous mode: ')       , 2,0)
        grid.addWidget( self.histrealtime                 , 2,1)
        grid.addWidget( self.button_addspan                   , 3,0 , 1,2)
        self.paramFrame.setLayout( grid )

    def initVertHistogram(self):
        self.plot_hist    = pg.PlotWidget()
        self.plot_hist.setMinimumHeight(600)
        self.plot_hist.setMinimumWidth(200)
        plot_viewbox      = self.plot_hist.getViewBox()
        plot_viewbox.invertX(True)
        self.plot_hist.showAxis('right')
        self.plot_hist.hideAxis('left')
        plot_viewbox.setAspectLocked(False)
        plot_viewbox.enableAutoRange(pg.ViewBox.YAxis, enable=True)
        # --- measured data --- #
        self.data_hist = pg.PlotDataItem()
        self.plot_hist.addItem(self.data_hist)
        # --- threshold line object --- #
        self.threshold = pg.InfiniteLine(pos=1., angle=0, movable=True)
        self.plot_hist.addItem( self.threshold )
        #self.threshold.sigPositionChangeFinished.connect(  )
        # --- default --- #
        self.plot_hist.setXRange(0, 255)
        if self.normalise:
            self.plot_hist.setXRange(0, 1)
        # --- make layout --- #
        self.histogFrame = QFrame()
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.plot_hist)
        self.histogFrame.setLayout( vlayout )

    def addSpan(self):
        N = len( list(self.dicspan.keys()) )
        newspan = SpanObject()
        self.dicspan[N+1] = newspan
        # ---  --- #
        self.plot_hist.addItem( newspan.bound1 )
        self.plot_hist.addItem( newspan.bound2 )
        self.plot_hist.addItem( newspan.fill  )

    def initMaximaTimeEvolution(self):
        return None

    def setLinkToCameraTimer(self):
        if   self.histrealtime.checkState() == 0:
            self.camera_view.timer.timeout.disconnect(self.updatePlotHistogram)
        elif self.histrealtime.checkState() == 2:
            self.camera_view.timer.timeout.connect(self.updatePlotHistogram)

    def setNewSaveFile(self):
        # --- stop timers to avoid over load --- #
        self.stop_continuous_view()
        self.fittingtimer.stop()
        # ---  --- #
        filename = self.savefile.getSaveFileName()
        dir_path = self.savefile.directory().absolutePath()
        os.chdir(dir_path)
        self.savefile_name.setText( filename[0] )
        # --- restart processes --- #
        self.fittingtimer.start()
        self.start_continuous_view()

    def addDataToFile(self):
        # --- stop timers to avoid over load --- #
        wasOn = self.isOn
        self.stop_continuous_view()
        self.fittingtimer.stop()
        # ---  --- #
        f = open(self.savefile_name.text(), 'a')
        coretxt  = ''
        coretxt += '\n'
        if   self.peakcount == 0:
            pass
        elif self.peakcount == 1:
            coretxt += self.sepration+str(self.param_peak[0][1])
        else:
            for i in range(self.peakcount):
                coretxt += self.sepration+str(self.param_peak[i,1])
        f.write(coretxt)
        f.close()
        # --- restart processes --- #
        if self.fittingactivate.checkState() != 0:
            self.fittingtimer.start()
        if wasOn:
            self.start_continuous_view()

    def acceptOrNot(self, i):
        if type(self.data_hist.xData)==type(None):
            self.fittingactivate.setCheckState(0)
        return None

    def changeMode(self):
        ind = self.modeselect.currentIndex()
        if   ind == 0:
            self.gaussianfit.setMode('all')
        elif ind == 1:
            self.gaussianfit.setMode('pbp')

    def setFittingRate(self):
        self.fittingtimer.setInterval(1e3/self.frqcyfitting.value())

    def setModeFitting(self):
        ind = self.normalise_hist.currentIndex()
        if   ind == 0:
            self.normalise = False
            self.gaussianfit.setMaxAmp(255)
            self.plot_hist.setYRange(0, 255)
            self.threshold.setValue(255)
        elif ind == 1:
            self.normalise = True
            self.gaussianfit.setMaxAmp(1.)
            self.plot_hist.setYRange(0, 1.)
            self.threshold.setValue(1.)
        # ---  --- #
        self.updatePlots()

    def updatePlots(self):
        self.quickPeakCount()
        if self.peakcount > self.nbrpeak.value():
            return None
        if self.fittingactivate.checkState() == 2:
            self.getParamFit()
            self.plotGaussianFit()
            self.updateRelativeHeightMatrix()

    def updatePlotHistogram(self):
        frame = self.camera_view.frame
        if type(frame) == type(None):
            return None
        frame = frame-np.mean(frame)
        ydata = np.sum(frame,axis=0)/frame.shape[0]
        ydata = ydata + np.abs(np.min([0, np.min(ydata)]))
        if self.normalise:
            ydata = ydata/np.max(ydata)
        # --- plot data --- #
        self.data_hist.setData( ydata, np.arange(len(ydata)) )

    def clearGaussianFits(self):
        KEYS = list(self.gaussian_plots.keys())
        for i in reversed(range(len(KEYS))):
            key = KEYS[i]
            #self.plot_hist.removeItem(self.gaussian_plots[key])
            self.gaussian_plots[key].clear()
            del self.gaussian_plots[key]
            #self.log.addText('Deleting plot: {}'.format(key))
        self.gaussian_plots = {}

    def plotGaussianFit(self):
        # ---  remove old gaussian plots --- #
        self.clearGaussianFits()
        # ---  --- #
        for key in self.gaussianfit.dic_gauss:
            x     = self.data_hist.xData
            #self.log.addText('gaussian param before plot: \n'+str(self.gaussianfit.dic_gauss[key]))
            y_fit = self.gaussianfit.gaussian(x, *self.gaussianfit.dic_gauss[key])
            self.gaussian_plots[key] = pg.PlotCurveItem(x=x,y=y_fit, pen='r')
        # ---  --- #
        for key in self.gaussian_plots:
            self.plot_hist.addItem(self.gaussian_plots[key])

    def quickPeakCount(self):
        xdata = self.data_hist.xData
        ydata = self.data_hist.yData
        if type(xdata)==type(None) or type(ydata)==type(None):
            self.peakcount = 0
            return None
        # --- threshold value --- #
        threshold = self.threshold.value()
        self.gaussianfit.setThreshold(self.threshold.value())
        truth_list = (np.abs(ydata-threshold)+(ydata-threshold)).astype(bool)
        # ---  --- #
        block_list = [[i for i,value in it] for key,it in itertools.groupby(enumerate(truth_list), key=operator.itemgetter(1)) if key != 0]
        self.peakcount = len(block_list)
        self.param_peak = np.ones([self.peakcount,3])
        for i in range(self.peakcount):
            x0 = (block_list[i][-1]+block_list[i][0])/2.
            a  = np.max(ydata[block_list[i]])
            b  = (block_list[i][-1]-block_list[i][0])/2.
            if b != 0: b = b**-1
            self.param_peak[i] = [x0,a,b]
        # ---  --- #
        self.peakcount_lab.setText(str(self.peakcount))
        self.updateParamLayout()

    def getParamFit(self):
        #self.quickPeakCount()
        # --- fitting --- #
        self.gaussianfit.setXData(self.data_hist.xData)
        self.gaussianfit.setYData(self.data_hist.yData)
        self.gaussianfit.setPeakNumber( self.peakcount )
        self.gaussianfit.setCenters(    self.param_peak[:,0])
        self.gaussianfit.setAmplitudes( self.param_peak[:,1])
        self.gaussianfit.setSTD(        self.param_peak[:,2])
        # ---  --- #
        self.gaussianfit.makeGaussianFit()

#########################################################################################################################
# CODE
#########################################################################################################################
if __name__ == '__main__':
    print('OpenCV 2 version: ',cv2.__version__)
    print('STARTING')
    camera = SimuCamera(0)
    #camera.__str__()

    app = QApplication([])
    start_window = PhaseNetworkElements(camera)
    start_window.show()
    app.exit(app.exec_())
    print('Close camera')
    camera.close_camera()

    print('FINISHED')
