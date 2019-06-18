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


import numpy as np
import itertools, operator
import matplotlib.pyplot as plt
import pyqtgraph as pg


from s_LogDisplay_class               import LogDisplay
from s_ToolObjects_class              import GaussianFit, SpanObject, PeakPlot
from s_CameraDisplay_class            import CameraDisplay
from s_SimuCamera_class               import SimuCamera

#########################################################################################################################
# FUNCTIONS
#########################################################################################################################

class PhaseNetworkElements(QWidget):
    def __init__(self, camera=None, log=None, fps=10.):
        super().__init__()
        self.feedback = False
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
        self.dicspan   = {}
        # --- main attriute --- #
        self.camera    = camera
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
        self.initParameterZone()
        self.initVertHistogram()
        self.initMultiplotPeak()
        self.initLissajousPlot()
        # --- default --- #
        self.updatePtNbrLabel()
        # --- layout --- #
        vsplitter      = QSplitter(PyQt5.QtCore.Qt.Vertical)
        vsplitter.addWidget( self.camera_view )
        vsplitter.addWidget( self.paramFrame )
        self.splitter.addWidget( vsplitter )
        self.splitter.addWidget( self.histogFrame )
        self.splitter.addWidget( self.multiplotFrame )
        vsplitter      = QSplitter(PyQt5.QtCore.Qt.Vertical)
        vsplitter.addWidget( self.lissajousFrame )
        vsplitter.addWidget( QFrame() )
        self.splitter.addWidget( vsplitter )
        self.layout.addWidget( self.splitter )
        self.setLayout(self.layout)
        # ---  --- #

    def initView(self):
        self.camera_view     = CameraDisplay(camera=self.camera, log=self.log)
        # ---  --- #
        self.camera_view.image_view.setMinimumWidth(200)
        self.camera_view.image_view.setMinimumHeight(200)

    def initParameterZone(self):
        self.paramFrame = QFrame()
        self.paramFrame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.paramFrame.setLineWidth(3)
        self.paramFrame.setMidLineWidth(1)
        # --- widgets --- #
        self.normalise_hist = QComboBox()
        self.normalise_hist.addItem('raw')
        self.normalise_hist.addItem('normalise')
        self.normalise_hist.setCurrentIndex(1)
        self.histrealtime   = QCheckBox()
        self.histrealtime.setTristate(False)
        self.histrealtime.setCheckState(2)
        self.setLinkToCameraTimer()
        self.button_save   = QPushButton('Save Plot data')
        self.savefile      = QFileDialog(self)
        self.savefile_name = QLabel('Select a file')
        self.savefile_name.setWordWrap(True)
        self.choosedirectory  = QPushButton('&New file')
        # --- connections --- #
        self.choosedirectory.clicked.connect(self.setNewSaveFile)
        self.button_save.clicked.connect( self.saveDataFromMultiplot )
        self.normalise_hist.currentIndexChanged.connect(self.setModeFitting)
        self.histrealtime.stateChanged.connect( self.setLinkToCameraTimer )
        # --- make layout --- #
        grid    = QGridLayout()
        grid.addWidget(QLabel('Mode for fitting: ')      , 0,0)
        grid.addWidget( self.normalise_hist              , 0,1)
        grid.addWidget(QLabel('Histogram in continuous mode: ')       , 2,0)
        grid.addWidget( self.histrealtime                , 2,1)
        grid.addWidget( self.choosedirectory  , 3,0)
        grid.addWidget(self.savefile_name     , 3,1)
        grid.addWidget( self.button_save      , 4,0 , 1,2)
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
        # --- default --- #
        self.plot_hist.setXRange(0, 255)
        if self.normalise:
            self.plot_hist.setXRange(0, 1)
        # --- widgets --- #
        self.spanNumber     = QSpinBox()#QPushButton('add new span')
        self.spanNumber.setMaximum(20)
        self.spanNumber.setValue(0)
        self.spanNumber.valueChanged.connect( self.makeSpans )
        # --- make layout --- #
        self.histogFrame = QFrame()
        layout = QGridLayout()
        layout.addWidget(QLabel('Span Number:') , 0,0)
        layout.addWidget( self.spanNumber       , 0,1)
        layout.addWidget(self.plot_hist   , 1,0 , 1,2)
        self.histogFrame.setLayout( layout )

    def initMultiplotPeak(self):
        self.multi_plot   = pg.GraphicsLayoutWidget()
        self.samplingtime = QSpinBox()
        self.samplingtime.setRange(1, 60)
        self.samplingtime.setValue(5)
        self.dicmultiplot = {}
        self.samplingPtNbr  = QLabel()
        # ---  --- #
        self.spanNumber.valueChanged.connect( self.updateMultiplots )
        self.samplingtime.valueChanged.connect( self.updatePtNbrLabel )
        self.camera_view.fps_input.valueChanged.connect( self.updatePtNbrLabel )
        # --- make layout --- #
        self.multiplotFrame = QFrame()
        layout = QGridLayout()
        layout.addWidget(QLabel('Sampling duration (s): ') , 0,0)
        layout.addWidget(self.samplingtime                 , 0,1)
        layout.addWidget(QLabel('(s) --> nbr of pts:')     , 0,2)
        layout.addWidget(self.samplingPtNbr                , 0,3)
        layout.addWidget(self.multi_plot                   , 1,0 , 1,4)
        self.multiplotFrame.setLayout( layout )

    def initLissajousPlot(self):
        self.lissajousFrame = QFrame()
        self.lissajousFrame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.lissajousFrame.setLineWidth(3)
        self.lissajousFrame.setMidLineWidth(1)
        # ---  --- #
        self.plot_lissjs = pg.PlotWidget()
        self.plot_lissjs.setMinimumHeight(300)
        self.plot_lissjs.setMinimumWidth(300)
        self.plot_lissjs.showGrid(x=True, y=True)
        lissjs_viewbox   = self.plot_lissjs.getViewBox()
        self.data_lissjs = pg.ScatterPlotItem() #pg.PlotDataItem()
        #self.data_lissjs.setSymbol('o')
        self.plot_lissjs.addItem(self.data_lissjs)
        # ---  --- #
        lissjs_viewbox.setRange(xRange=(0,1), yRange=(0,1))
        self.plot_xaxis  = QComboBox()
        self.plot_yaxis  = QComboBox()
        self.makeLissajousAxisSelection()
        self.button_plot_lissajs = QPushButton('Plot')
        self.button_plot_lissajs.setCheckable(True)
        # --- make layout --- #
        layout = QGridLayout()
        layout.addWidget( QLabel('X axis'), 0,1)
        layout.addWidget( QLabel('Y axis'), 0,2)
        layout.addWidget( QLabel('Plot : '), 1,0)
        layout.addWidget( self.plot_xaxis  , 1,1)
        layout.addWidget( self.plot_yaxis  , 1,2)
        layout.addWidget( self.button_plot_lissajs, 2,0 , 1,3)
        layout.addWidget( self.plot_lissjs, 3,0 , 1,3)
        self.lissajousFrame.setLayout( layout )

    def setNewSaveFile(self):
        # --- stop timers to avoid over load --- #
        wasOn = self.camera_view.isOn
        self.camera_view.stop_continuous_view()
        # ---  --- #
        filename = self.savefile.getSaveFileName(None)
        dir_path = self.savefile.directory().absolutePath()
        os.chdir(dir_path)
        self.savefile_name.setText( filename[0] )
        # --- restart processes --- #
        if wasOn:
            self.camera_view.start_continuous_view()

    def saveDataFromMultiplot(self):
        # --- stop timers to avoid over load --- #
        wasOn = self.camera_view.isOn
        self.camera_view.stop_continuous_view()
        # ---  --- #
        if self.spanNumber.value() == 0:
            return None
        # ---  --- #
        filename = self.savefile_name.text()
        try:
            f = open(filename, 'w+')
        except:
            err_msg  = 'Error: in saveDataFromMultiplot, not able to open file.'
            err_msg += '\nFilename is: {}'.format(filename)
            self.log.addText( err_msg )
        # ---  --- #
        min_len   = np.inf
        data_list = []
        for key in self.dicmultiplot:
            data_list.append( self.dicmultiplot[key][0].plot.yData )
            min_len = np.min( [min_len, len(data_list[-1])] )
        min_len = int(min_len)
        if len(data_list) == 0:
            return None
        # --- equalise the length of the data, from the end since it is the most recent one --- # 
        for i in range(len(data_list)):
            data_list[i] = data_list[i][-min_len:]
        data_list = np.array(data_list)
        # ---  --- #
        np.savetxt(filename, data_list)
        # --- restart processes --- #
        if wasOn:
            self.camera_view.start_continuous_view()

    def makeLissajousAxisSelection(self):
        nx = self.plot_xaxis.count()
        ny = self.plot_yaxis.count()
        if nx != ny:
            self.log.addText('Error in makeLissajousAxisSelection, the two axis combobox do not have the same item number.')
            return None
        for i in reversed(range(nx)):
            self.plot_xaxis.removeItem(i)
            self.plot_yaxis.removeItem(i)
        for i in range(self.spanNumber.value()):
            self.plot_xaxis.addItem(str(i+1))
            self.plot_yaxis.addItem(str(i+1))

    def toggleLissajousPlot(self):
        if   self.button_plot_lissajs.isChecked():
            self.doLissajous = True
        else:
            self.doLissajous = False

    def addSpan(self):
        N = len( list(self.dicspan.keys()) )
        newspan = SpanObject(name='span_{}'.format(N+1), pos_init=N*50 +1, log=self.log)
        self.dicspan[N+1] = newspan
        # ---  --- #
        self.plot_hist.addItem( newspan.span )
        # --- add label --- #
        #newspan.label.setParentItem(self.plot_hist.getViewBox())
        self.plot_hist.addItem( newspan.label )
        # ---  --- #
        self.addPlot(newspan)

    def removeSpan(self):
        N = len( list(self.dicspan.keys()) )
        if N == 0:
            return None
        # ---  --- #
        self.removePlot( self.dicspan[N] )
        # ---  --- #
        self.plot_hist.removeItem( self.dicspan[N].span )
        self.plot_hist.removeItem( self.dicspan[N].label )
        self.dicspan[N].setParent(None)
        del self.dicspan[N]

    def makeSpans(self):
        n = self.spanNumber.value()
        n_current = len(list(self.dicspan.keys()))
        if   n == n_current:
            pass
        elif n > n_current:
            for i in range(n-n_current):
                self.addSpan()
        elif n < n_current:
            for i in range(n_current-n):
                self.removeSpan()
        self.makeLissajousAxisSelection()

    def addPlot(self, span):
        N = len( list(self.dicspan.keys()) )
        newplot = PeakPlot(name='plot_{}'.format(span.name), span=span, log=self.log)
        self.dicmultiplot[newplot.name] = [newplot]
        # ---  --- #
        span.span.sigRegionChangeFinished.connect( self.updateMultiplots )
        # ---  --- #
        self.multi_plot.nextRow()
        self.multi_plot.addItem( newplot )
        # ---  --- #
        label_item = self.multi_plot.addLabel(newplot.name[10:], angle = -90)
        self.dicmultiplot[newplot.name].append( label_item )

    def removePlot(self, span):
        '''
        In dictionary of plots, we retreive the plot list [plot_item, label_item], associated
        to the span region.
        '''
        N = len( list(self.dicspan.keys()) )
        plot_to_remove = self.dicmultiplot['plot_{}'.format(span.name)]
        # ---  remove plot --- #
        self.multi_plot.removeItem( plot_to_remove[0] )
        plot_to_remove[0].setParent(None)
        # --- remove label --- #
        self.multi_plot.removeItem( plot_to_remove[1] )
        # ---  --- #
        del self.dicmultiplot['plot_{}'.format(span.name)]
        span.setAssigned(False)

    def setLinkToCameraTimer(self):
        if   self.histrealtime.checkState() == 0:
            self.camera_view.timer.timeout.disconnect(self.updatePlotHistogram)
        elif self.histrealtime.checkState() == 2:
            self.camera_view.timer.timeout.connect(self.updatePlotHistogram)

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
            self.plot_hist.setXRange(0, 255)
        elif ind == 1:
            self.normalise = True
            self.plot_hist.setXRange(0, 1.)
        # ---  --- #
        self.updatePlotHistogram()

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
        # ---  --- #
        self.updateMultiplots()

    def updateMultiplots(self):
        for key in self.dicmultiplot:
            plot = self.dicmultiplot[key][0]
            plot.setFullData( self.data_hist.xData ) #!! indeed since the histogram is vertical, the data are in the x axis !!
            plot.setLengthMax( self.samplingtime.value()*self.camera_view.fps )
            plot.updatePlot()
        # ---  --- #
        if self.button_plot_lissajs.isChecked():# if self.doLissajous:
            self.updateLissajousPlot()

    def updateLissajousPlot(self):
        xaxis_ind = self.plot_xaxis.currentText()
        yaxis_ind = self.plot_yaxis.currentText()
        try:
            xplot     = self.dicmultiplot['plot_span_{}'.format(xaxis_ind)][0]
            yplot     = self.dicmultiplot['plot_span_{}'.format(yaxis_ind)][0]
        except:
            if self.feedback:
                err_msg  = 'Error: in updateLissajousPlot. Wrong key for dicmultiplot.'
                self.log.addText( err_msg )
            return None
        xdata     = xplot.plot.yData
        ydata     = yplot.plot.yData
        if type(xdata) != type(None) and type(ydata) != type(None):
            n = np.min( [len(xdata), len(ydata)] )
            self.data_lissjs.setData( xdata[-n:], ydata[-n:] )

    def updatePtNbrLabel(self):
        self.samplingPtNbr.setText( str(self.samplingtime.value()*self.camera_view.fps) )

#########################################################################################################################
# CODE
#########################################################################################################################
if __name__ == '__main__':
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
