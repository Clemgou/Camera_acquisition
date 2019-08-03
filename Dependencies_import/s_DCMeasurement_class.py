#!/usr/bin/env python
# -*- coding: utf-8 -*-



#########################################################################################################################
# IMPORTATION
#########################################################################################################################
import os
import sys
import PyQt5
from PyQt5.QtWidgets import QWidget, QFrame, QApplication
from PyQt5.QtWidgets import QVBoxLayout,QHBoxLayout,QSplitter, QGridLayout
from PyQt5.QtWidgets import QLabel, QPushButton, QLineEdit, QSpinBox, QComboBox, QCheckBox, QFileDialog, QTableWidget, QTableWidgetItem
from PyQt5.QtCore    import Qt, QThread, QTimer, QObject, pyqtSignal, pyqtSlot, QRect
from PyQt5.QtGui     import QPainter


import time
import itertools, operator
import numpy             as np
import matplotlib.pyplot as plt
import pyqtgraph         as pg
from   PIL               import Image


from s_LogDisplay_class               import LogDisplay
from s_Workers_class                  import *
from s_ToolObjects_class              import GaussianFit, SpanObject
from s_CameraDisplay_class            import CameraDisplay
from s_SimuCamera_class               import SimuCamera
from s_Camera_class                   import Camera

#########################################################################################################################
# FUNCTIONS
#########################################################################################################################

class DCMeasurement(QWidget):
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
        self.param_peak   = [] # a N x 3 array where each line is [x0, a, b] the parameter of the fit, N being the number of peaks.
        self.measured_max = []
        self.power_peak   = []
        self.fittingtimer = pg.QtCore.QTimer()
        # --- main attriute --- #
        self.camera    = camera
        if not self.camera.isCameraInit:
            self.camera.__init__(cam_id=0, log=self.log)
        self.contview  = ContinuousView(fps=self.fps)
        self.qlabl_max = QLabel()
        # ---  --- #
        self.initUI()

    def initUI(self):
        self.splitter      = QSplitter(PyQt5.QtCore.Qt.Horizontal)
        self.fitting_frame = None
        # ---  --- #
        self.layout      = QVBoxLayout(self)
        # --- guassian fit init --- #
        self.dic_spanfitting = {}
        self.gaussianfit     = GaussianFit(log=self.log)
        self.gaussian_plots  = {}
        self.fittingactivate = QCheckBox()
        self.fittingactivate.setTristate(False)
        self.fittingactivate.stateChanged.connect(self.acceptOrNot)
        self.fittingactivate.stateChanged.connect(self.fittingActivationDeactivation)
        # --- init frames --- #
        self.initView()
        self.initDisplayFittingFrame()
        self.initParameterFittingFrame()
        self.relativeHeightsLayout()
        # --- layout --- #
        self.splitter.addWidget( self.viewFrame )
        vsplitter = QSplitter(PyQt5.QtCore.Qt.Vertical)
        vsplitter.addWidget( self.fittingFrame )
        vsplitter.addWidget( self.paramfittingframe )
        vsplitter.addWidget( self.matrelatFrame )
        self.splitter.addWidget( vsplitter )
        self.layout.addWidget( self.splitter )
        self.setLayout(self.layout)
        # ---  --- #
        self.fittingtimer.start()
        self.setXdataPoints()
        self.setFittingMethod()

    def initView(self):
        self.camera_view     = CameraDisplay(camera=self.camera, log=self.log)
        # ---  --- #
        self.camera_view.image_view.setMinimumWidth(600)
        self.camera_view.image_view.setMinimumHeight(200)
        # ---  --- #
        self.viewFrame = QFrame()
        self.viewFrame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.viewFrame.setLineWidth(3)
        self.viewFrame.setMidLineWidth(1)
        layout = QVBoxLayout()
        layout.addWidget( self.camera_view )
        self.viewFrame.setLayout( layout )

    def initDisplayFittingFrame(self):
        self.plot_hist    = pg.PlotWidget()
        self.plot_hist.setMinimumWidth(800)
        plot_viewbox      = self.plot_hist.getViewBox()
        plot_viewbox.setAspectLocked(False)
        plot_viewbox.enableAutoRange(pg.ViewBox.XAxis, enable=True)
        # --- measured data --- #
        self.data_hist = pg.PlotDataItem()
        self.plot_hist.addItem(self.data_hist)
        # --- threshold line object --- #
        self.threshold = pg.InfiniteLine(pos=1., angle=0, movable=True)
        self.plot_hist.addItem( self.threshold )
        # --- widgets --- #
        self.normalise_hist = QComboBox()
        self.normalise_hist.addItem('raw')
        self.normalise_hist.addItem('normalise')
        self.normalise_hist.setCurrentIndex(0)
        self.nbrpeak = QSpinBox()
        self.nbrpeak.setRange(1, 20)
        self.nbrpeak.setValue(2)
        self.histrealtime = QCheckBox()
        self.histrealtime.setTristate(False)
        self.histrealtime.setCheckState(2)
        self.setLinkToCameraTimer()
        # --- connections --- #
        self.threshold.sigPositionChangeFinished.connect(self.updatePlots)
        self.normalise_hist.currentIndexChanged.connect(self.setModeFitting)
        self.nbrpeak.valueChanged.connect(self.updatePlots)
        self.histrealtime.stateChanged.connect( self.setLinkToCameraTimer )
        # --- default --- #
        self.setModeFitting()
        plot_viewbox.enableAutoRange(pg.ViewBox.YAxis, enable=True)
        if self.normalise:
            self.plot_hist.setYRange(0, 1)
        # --- make layout --- #
        self.fittingFrame = QFrame()
        vlayout = QVBoxLayout()
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel('mode fitting:'))
        hlayout.addWidget( self.normalise_hist )
        hlayout.addWidget(QLabel('Number maximum of peaks:'))
        hlayout.addWidget( self.nbrpeak )
        hlayout.addWidget(QLabel('Continuous mode:'))
        hlayout.addWidget( self.histrealtime )
        vlayout.addLayout(hlayout)
        vlayout.addWidget(self.plot_hist)
        self.fittingFrame.setLayout( vlayout )

    def initParameterFittingFrame(self):
        # --- widgets --- #
        self.peakcount_lab    = QLabel('#')
        self.modeselect       = QComboBox()
        self.modeselect.addItem('all')
        self.modeselect.addItem('peak by peak')
        self.choosedirectory  = QPushButton('&New file')
        self.savefile_name    = QLabel('Select a file')
        self.savefile_name.setWordWrap(True)
        self.savefile         = QFileDialog()
        self.button_addData   = QPushButton('Add data')
        self.button_addData.setStyleSheet("background-color: green")
        self.button_makefit   = QPushButton('Make fit')
        self.frqcyfitting     = QSpinBox()
        self.frqcyfitting.setRange(1,12)
        self.frqcyfitting.setValue(10)
        self.fitting_xdataNbre= QSpinBox()
        self.fitting_xdataNbre.setRange(100, 5e3)
        self.fitting_xdataNbre.setValue(10**3)
        self.fitting_param_dspl= QTableWidget()
        self.fitting_param_dspl.setRowCount(5)
        self.saving_state      = QLabel('###')
        self.saving_state.setWordWrap(True)
        self.save_count        = QSpinBox()
        self.save_count.setRange(0, 1e4)
        self.save_count.setValue(0)
        self.button_test       = QPushButton('TEST')
        # ---  --- #
        self.fittingtimer.setInterval(self.frqcyfitting.value())
        # --- connections --- #
        self.modeselect.currentIndexChanged.connect(self.setFittingMethod)
        self.choosedirectory.clicked.connect(self.setNewSaveFile)
        self.button_addData.clicked.connect(self.addDataToFile)
        self.frqcyfitting.valueChanged.connect(self.setFittingRate)
        self.fittingtimer.timeout.connect(self.updatePlots)
        self.fitting_xdataNbre.valueChanged.connect( self.setXdataPoints )
        self.button_makefit.clicked.connect(self.singleShotFittingPlot)
        self.nbrpeak.valueChanged.connect(self.initPeakByPeakFitting)
        # --- make layout --- #
        self.paramfittingframe = QFrame()
        self.param_grid        = QGridLayout()
        self.param_grid.addWidget(QLabel('Activate fitting '), 0,0)
        self.param_grid.addWidget( self.fittingactivate      , 0,1)
        self.param_grid.addWidget(QLabel('Fitting rate:')    , 0,2)
        self.param_grid.addWidget( self.frqcyfitting         , 0,3)
        self.param_grid.addWidget(QLabel('Fitting Sampling number'), 0,4)
        self.param_grid.addWidget( self.fitting_xdataNbre    , 0,5)
        self.param_grid.addWidget(QLabel('Peak nbr:')        , 1,0)
        self.param_grid.addWidget( self.peakcount_lab        , 1,1)
        self.param_grid.addWidget(QLabel('Fitting method:')  , 1,2)
        self.param_grid.addWidget( self.modeselect           , 1,3)
        self.param_grid.addWidget( self.button_makefit       , 1,4 , 1,2)
        self.param_grid.addWidget( self.fitting_param_dspl   , 2,0 , 4,6)
        self.param_grid.setRowMinimumHeight(2, 35)
        self.param_grid.setRowMinimumHeight(3, 35)
        self.param_grid.setRowMinimumHeight(4, 35)
        self.param_grid.setRowMinimumHeight(5, 35)
        self.updateParamLayout()
        self.param_grid.addWidget(self.choosedirectory       , 6,0)
        self.param_grid.addWidget( self.savefile_name        , 6,1 , 1,6)
        self.param_grid.addWidget( self.button_addData       , 7,0 , 1,4)
        self.param_grid.addWidget(self.saving_state          , 7,4)
        self.param_grid.addWidget(self.save_count            , 7,5)
        for i in range(self.param_grid.rowCount()+1):
            self.param_grid.setRowStretch(i, 1)
        # ---  --- #
        self.paramfittingframe.setLayout( self.param_grid )

    def initPeakByPeakFitting(self):
        if self.modeselect.currentIndex() != 1:
            return None
        # --- reset spans --- #
        self.removeAllSpans()
        # ---  --- #
        for i in range( self.nbrpeak.value() ):
            newspan = SpanObject(name='span_{}'.format(i), orientation='vertical', log=self.log, pos_init=i*50 +1)
            newspan.span.sigRegionChangeFinished.connect(self.updatePowerPeak)
            self.dic_spanfitting[newspan.name] = newspan
            self.plot_hist.addItem( newspan.span )
            self.plot_hist.addItem( newspan.label )
        self.gaussianfit.setSpanDictionary( self.dic_spanfitting )
        # ---  --- #
        self.power_peak = np.zeros(self.nbrpeak.value())

    def initPowerEstimation(self):
        if self.modeselect.currentIndex() != 2:
            return None
        # --- reset spans --- #
        self.removeAllSpans()
        # ---  --- #
        for i in range( self.nbrpeak.value() ):
            newspan = SpanObject(name='span_{}'.format(i), orientation='vertical', log=self.log, pos_init=i*50 +1)
            newspan.span.sigRegionChangeFinished.connect(self.updatePowerPeak)
            self.dic_spanfitting[newspan.name] = newspan
            self.plot_hist.addItem( newspan.span )
        # ---  --- #
        self.power_peak = np.zeros(self.nbrpeak.value())

    def removeAllSpans(self):
        KEYS = list( self.dic_spanfitting.keys() )
        for key in KEYS:
            self.plot_hist.removeItem( self.dic_spanfitting[key].span )
            self.dic_spanfitting[key].setParent(None)
            del self.dic_spanfitting[key]

    def removeAllLabels(self):
        KEYS = list( self.dic_spanfitting.keys() )
        for key in KEYS:
            self.plot_hist.removeItem( self.dic_spanfitting[key].label )

    def addDataToFile(self):
        # --- stop timers to avoid over load --- #
        wasOn = self.camera_view.isOn
        self.camera_view.stop_continuous_view()
        self.fittingtimer.stop()
        # ---  --- #
        self.saving_state.setText('Saving ...')
        self.button_addData.setStyleSheet("background-color: red")
        time.sleep(.5)
        self.img_count = self.save_count.value()
        # ---  --- #
        if len(self.param_peak) == 0:
            # --- restart processes --- #
            if self.fittingactivate.checkState() != 0:
                self.fittingtimer.start()
            if wasOn:
                self.camera_view.start_continuous_view()
            # ---  --- #
            self.saving_state.setText('Save unsuccessful: param of length 0.')
            return None
        elif len(self.power_peak) == 0:
            self.power_peak = np.zeros(self.nbrpeak.value())
        # ---  --- #
        N = self.param_peak.shape[0]
        try:
            open(self.savefile_name.text(), 'r')
        except:
            f = open(self.savefile_name.text(), 'a')
            header = ''
            for i in range(N):
                header += 'Peak_measured_{}'.format(i)+self.sepration
                header += 'Peak_power_{}'.format(i)   +self.sepration
                header += 'Peak_fitted_{}'.format(i)  +self.sepration
            f.write(header)
            f.close()
            self.log.addText('Creating new file')
        # ---  --- #
        f = open(self.savefile_name.text(), 'a')
        coretxt  = ''
        coretxt += '\n'
        for i in range(N):
            coretxt += str(self.measured_max[i])+self.sepration
            coretxt += str(self.power_peak[i]  )+self.sepration
            coretxt += str(self.param_peak[i,1])+self.sepration
        f.write(coretxt)
        f.close()
        # --- save coresponding frame as tif --- #
        img_to_save = Image.fromarray( self.camera_view.frame )
        if self.savefile_name.text()[:-4] == '.':
            img_to_save.save( self.savefile_name.text()[:-4]+'_{0:03d}.tif'.format(self.img_count) )
        else:
            img_to_save.save( self.savefile_name.text()     +'_{0:03d}.tif'.format(self.img_count) )
        self.img_count += 1
        # ---  --- #
        self.saving_state.setText('Saved No:')
        self.save_count.setValue(self.img_count)
        self.button_addData.setStyleSheet("background-color: green")
        time.sleep(0.5)
        # --- restart processes --- #
        if self.fittingactivate.checkState() != 0:
            self.fittingtimer.start()
        if wasOn:
            self.camera_view.start_continuous_view()

    def acceptOrNot(self, i):
        if type(self.data_hist.xData)==type(None):
            self.fittingactivate.setCheckState(0)
        # ---  --- #
        self.setXdataPoints()

    def clearGaussianFits(self):
        KEYS = list(self.gaussian_plots.keys())
        for i in reversed(range(len(KEYS))):
            key = KEYS[i]
            #self.plot_hist.removeItem(self.gaussian_plots[key])
            self.gaussian_plots[key].clear()
            del self.gaussian_plots[key]
            #self.log.addText('Deleting plot: {}'.format(key))
        self.gaussian_plots = {}

    def clearLayout(self, layout):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            layout.removeItem( item )

    def fittingActivationDeactivation(self, i):
        if   self.fittingactivate.checkState() == 0:
            self.fittingtimer.stop()
        elif self.fittingactivate.checkState() == 2:
            self.fittingtimer.start()

    def getParamFit(self):
        # --- fitting --- #
        self.gaussianfit.setXData(self.data_hist.xData)
        self.gaussianfit.setYData(self.data_hist.yData)
        self.gaussianfit.setPeakNumber( self.peakcount )
        self.gaussianfit.setCenters(    self.param_peak[:,0])
        self.gaussianfit.setAmplitudes( self.param_peak[:,1])
        self.gaussianfit.setSTD(        self.param_peak[:,2])
        # ---  --- #
        self.gaussianfit.makeGaussianFit()
        # ---  --- #
        self.param_peak   = self.gaussianfit.param
        if self.modeselect.currentIndex() == 1:
            self.measured_max = self.gaussianfit.maximums

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
        self.param_peak   = np.ones([self.peakcount,3])
        self.measured_max = np.ones(self.peakcount)
        for i in range(self.peakcount):
            x0 = (block_list[i][-1]+block_list[i][0])/2.
            a  = np.max(ydata[block_list[i]])
            b  = (block_list[i][-1]-block_list[i][0])/2.
            if b != 0: b = b**-1
            self.param_peak[i]   = [x0,a,b]
            self.measured_max[i] = a
        # ---  --- #
        self.peakcount_lab.setText(str(self.peakcount))
        self.updateParamLayout()

    def plotGaussianFit(self):
        # ---  remove old gaussian plots --- #
        self.clearGaussianFits()
        # ---  --- #
        for key in self.gaussianfit.dic_gauss:
            x     = self.xdataFit #self.data_hist.xData
            y_fit = self.gaussianfit.gaussian(x, *self.gaussianfit.dic_gauss[key])
            self.gaussian_plots[key] = pg.PlotCurveItem(x=x,y=y_fit, pen='r')
        # ---  --- #
        for key in self.gaussian_plots:
            self.plot_hist.addItem(self.gaussian_plots[key])

    def relativeHeightsLayout(self):
        self.matrelatFrame = QFrame()
        self.matrelat_layout = QGridLayout()
        self.matrelat_layout.setColumnMinimumWidth(0, 200)
        n = 0
        self.matrelat = np.zeros([n,n])
        numbering = np.arange(n)
        # --- with qtable --- #
        self.table = QTableWidget()
        self.matrelat_layout.addWidget(self.table)
        # ---  --- #
        self.matrelatFrame.setLayout( self.matrelat_layout )

    def removeAllSpans(self):
        KEYS = list( self.dic_spanfitting.keys() )
        for key in KEYS:
            span_to_remove = self.dic_spanfitting[key]
            self.plot_hist.removeItem( span_to_remove.span )
            del self.dic_spanfitting[key]

    def setNewSaveFile(self):
        # --- stop timers to avoid over load --- #
        wasOn = self.camera_view.isOn
        self.camera_view.stop_continuous_view()
        self.fittingtimer.stop()
        # ---  --- #
        filename = self.savefile.getSaveFileName()
        dir_path = self.savefile.directory().absolutePath()
        os.chdir(dir_path)
        self.savefile_name.setText( filename[0] )
        # --- set image count --- #
        self.img_count = 0
        # --- restart processes --- #
        if self.fittingactivate.checkState() != 0:
            self.fittingtimer.start()
        if wasOn:
            self.camera_view.start_continuous_view()

    def setXdataPoints(self):
        if type(self.data_hist.xData) != type(None):
            self.xdataFit = np.linspace( np.min(self.data_hist.xData), np.max(self.data_hist.xData), self.fitting_xdataNbre.value())
        else:
            self.xdataFit = np.linspace( 0,100, self.fitting_xdataNbre.value() )

    def setFittingMethod(self):
        ind = self.modeselect.currentIndex()
        if   ind == 0:
            self.gaussianfit.setMode('all')
            self.button_makefit.setEnabled(False)
            self.button_makefit.setFlat(True)
            self.fittingactivate.setCheckState(2)
            self.removeAllLabels()
            self.removeAllSpans()
            self.power_peak = []
        elif ind == 1:
            self.gaussianfit.setMode('pbp')
            self.button_makefit.setEnabled(True)
            self.button_makefit.setFlat(False)
            self.fittingactivate.setCheckState(0)
            self.initPeakByPeakFitting()
            self.initPowerEstimation()

    def setFPS(self):
        self.fps = self.fps_input.value()
        self.contview.setFPS( self.fps )
        self.timer.setInterval(1e3/self.fps)

    def setFittingRate(self):
        self.fittingtimer.setInterval(1e3/self.frqcyfitting.value())

    def setModeFitting(self):
        ind = self.normalise_hist.currentIndex()
        if   ind == 0:
            self.normalise = False
            self.gaussianfit.setMaxAmp(255)
            #self.plot_hist.setYRange(0, 255)
            self.plot_hist.getViewBox().enableAutoRange(pg.ViewBox.YAxis, enable=True)
            #self.threshold.setValue(255)
        elif ind == 1:
            self.normalise = True
            self.gaussianfit.setMaxAmp(1.)
            self.plot_hist.setYRange(0, 1.)
            self.threshold.setValue(1.)
        # ---  --- #
        self.updatePlots()

    def setLinkToCameraTimer(self):
        if   self.histrealtime.checkState() == 0:
            self.camera_view.frame_updated.disconnect(self.updatePlotHistogram)
        elif self.histrealtime.checkState() == 2:
            self.camera_view.frame_updated.connect(self.updatePlotHistogram)

    def singleShotFittingPlot(self):
        self.quickPeakCount()
        self.getParamFit()
        self.plotGaussianFit()
        self.updatePowerPeak()
        self.updateParamLayout()
        self.updateRelativeHeightMatrix()

    def updatePowerPeak(self):
        if len(self.power_peak) != len(list(self.dic_spanfitting.keys())):
            self.log.addText('Error: in updatePowerPeak, length of power_peak list and number of span do not coincide.')
            return None
        # ---  --- #
        for i in range(len(self.power_peak)):
            region = self.dic_spanfitting['span_{}'.format(i)].span.getRegion()
            m , M  = int(np.min(region)), int(np.max(region))
            self.power_peak[i] = np.sum(self.data_hist.yData[m:M])
        # ---  --- #
        self.updateParamLayout()

    def updateParamLayout(self):
        try:
            n = self.param_peak.shape[0]
        except:
            self.log.addText('self.peakcount most likely not defined yet')
            return None
        self.fitting_param_dspl.clear()
        self.fitting_param_dspl.setItem(0,0 , QTableWidgetItem( 'Peak position' ) )
        self.fitting_param_dspl.setItem(1,0 , QTableWidgetItem( 'Peak amplitudes' ) )
        self.fitting_param_dspl.setItem(2,0 , QTableWidgetItem( 'STD' ) )
        self.fitting_param_dspl.setItem(3,0 , QTableWidgetItem( 'Measured max' ) )
        self.fitting_param_dspl.setItem(4,0 , QTableWidgetItem( 'Peak power' ) )
        self.fitting_param_dspl.setColumnCount(n+1)
        # ---  --- #
        if not n >=1:
            return None
        for i in range(n):
                try:
                    self.fitting_param_dspl.setItem(0,i+1 , QTableWidgetItem( '{:.3f}'.format(self.param_peak[i,0]) ) )
                    self.fitting_param_dspl.setItem(1,i+1 , QTableWidgetItem( '{:.3f}'.format(self.param_peak[i,1]) ) )
                    self.fitting_param_dspl.setItem(2,i+1 , QTableWidgetItem( '{:.3f}'.format(self.param_peak[i,2]) ) )
                    self.fitting_param_dspl.setItem(3,i+1 , QTableWidgetItem( '{:.3f}'.format(self.measured_max[i]) ) )
                    if len(self.power_peak) != 0:
                        self.fitting_param_dspl.setItem(4,i+1 , QTableWidgetItem( '{:.3f}'.format(self.power_peak[i]) ) )
                except:
                    pass

    def updateRelativeHeightMatrix(self):
        n = self.param_peak.shape[0]
        self.table.clear()
        self.table.setRowCount(n)
        self.table.setColumnCount(n)
        self.matrelat = np.zeros([n,n])
        # ---  --- #
        if not n >=1:
            return None
        for i in range(n):
            for j in range(n):
                try:
                    self.table.setItem(i,j , QTableWidgetItem( str(round(self.param_peak[i,1]/self.param_peak[j,1], 3)) ) )
                except:
                    pass
        #self.matrelat_layout.setRowMinimumHeight(0, 35*n)

    def updatePlots(self):
        self.quickPeakCount()
        if self.peakcount > self.nbrpeak.value():
            return None
        if self.fittingactivate.checkState() == 2:
            self.getParamFit()
            self.plotGaussianFit()
            self.updateParamLayout()
            self.updateRelativeHeightMatrix()

    def updatePlotHistogram(self):
        frame = self.camera_view.frame
        if type(frame) == type(None):
            return None
        # ---  --- #
        # ---  --- #
        ydata = np.sum(frame,axis=0)/frame.shape[0]
        if self.normalise:
            try:
                ydata = ydata/np.max(ydata)
            except:
                err_msg  = 'Error: in updatePlotHistogram. ydata/np.max(ydata) does not work.'
                err_msg += '\nydata max: {}'.format(np.max(ydata))
                self.log.addText(err_msg)
        # --- plot data --- #
        self.data_hist.setData(ydata)

#########################################################################################################################
# CODE
#########################################################################################################################
if __name__ == '__main__':
    print('STARTING')
    dir_path = '/home/cgou/ENS/STAGE/M2--stage/Camera_acquisition/Miscellaneous/Camera_views/'
    camera   = Camera(cam_id=0)
    if not camera.isCameraInit:
        camera = SimuCamera(0, directory_path=dir_path)
        camera.__info__()

    app = QApplication([])
    start_window = DCMeasurement(camera)
    start_window.show()
    app.exit(app.exec_())
    print('Close camera')
    camera.close_camera()

    print('FINISHED')
