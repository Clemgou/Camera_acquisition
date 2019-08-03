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
from s_ToolObjects_class              import GaussianFit, SpanObject, PeakPlot, QHLine
from s_CameraDisplay_class            import CameraDisplay
from s_SimuCamera_class               import SimuCamera
from s_Camera_class                   import Camera

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
        self.sepration = ' '
        self.param_peak= [] # a N x 3 array where each line is [x0, a, b] the parameter of the fit, N being the number of peaks.
        self.dicspan   = {}
        self.postprocss_func = None
        self.procssfunc_default = True
        # --- main attriute --- #
        self.camera    = camera
        if not self.camera.isCameraInit:
            self.camera.__init__(cam_id=0, log=self.log)
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
        self.camera_view.image_view.setMinimumWidth(100)
        self.camera_view.image_view.setMinimumHeight(200)

    def initParameterZone(self):
        self.paramFrame = QFrame()
        self.paramFrame.setToolTip('Frame where we control the main parameter for the data sampling.')
        self.paramFrame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.paramFrame.setLineWidth(3)
        self.paramFrame.setMidLineWidth(1)
        # --- widgets --- #
        self.histogram_data = QComboBox()
        self.histogram_data.addItem('raw')
        self.histogram_data.addItem('remove backgrnd')
        self.histogram_data.addItem('normalise')
        self.histogram_data.setCurrentIndex(0)
        self.histrealtime   = QCheckBox()
        self.histrealtime.setTristate(False)
        self.histrealtime.setCheckState(2)
        self.setLinkToCameraTimer()
        self.button_save   = QPushButton('Save sampling data')
        self.button_save.setToolTip('Save the plots in the milti-plot window in a txt file such that each line corresponds to the y-data. Moreover we save the total intensity.')
        self.savefile      = QFileDialog(self)
        self.savefile_name = QLabel('Select a file')
        self.savefile_name.setWordWrap(True)
        self.choosedirectory  = QPushButton('&Change file')
        self.postprocss    = QComboBox()
        self.postprocss.addItem('Max peak')
        self.postprocss.addItem('Sum area span')
        # --- connections --- #
        self.choosedirectory.clicked.connect(self.setNewSaveFile)
        self.button_save.clicked.connect( self.saveDataFromMultiplot )
        self.histrealtime.stateChanged.connect( self.setLinkToCameraTimer )
        self.histogram_data.currentIndexChanged.connect( self.setHistgrmPlotRange )
        self.postprocss.currentIndexChanged.connect( self.setPostProcessFunction )
        # --- make layout --- #
        label_1 = QLabel('Histogram data: ')
        label_1.setWordWrap(True)
        label_1.setToolTip('Set what transformation we operate from the image data to the histogram data.\n"raw" means we integrate over the Y-axis and divide by the number of line.\n"normalise" like "raw" but we normalise to the maximum afterward.')
        label_2 = QLabel('Histogram in continuous mode: ')
        label_2.setWordWrap(True)
        label_2.setToolTip('When unchecked, stop the updating of the histogram. In other words, allow to stop the histogram without stopping the video image.')
        label_3 = QLabel('Sampling post-processing: ')
        label_3.setWordWrap(True)
        label_3.setToolTip('The post-processing refer to the data processing from the vertivcal histogram of the image.')
        grid    = QGridLayout()
        grid.addWidget(label_1               , 1,0)
        grid.addWidget( self.histogram_data  , 1,1)
        grid.addWidget(label_2               , 0,0)
        grid.addWidget( self.histrealtime    , 0,1)
        grid.addWidget(label_3               , 2,0)
        grid.addWidget(self.postprocss       , 2,1)
        grid.addWidget( QHLine()             , 3,0 , 1,2)
        grid.addWidget( self.button_save     , 4,0 , 1,2)
        grid.addWidget( self.choosedirectory , 5,0)
        grid.addWidget(self.savefile_name    , 5,1)
        self.paramFrame.setLayout( grid )

    def initVertHistogram(self):
        self.plot_hist    = pg.PlotWidget()
        self.plot_hist.setMinimumHeight(600)
        self.plot_hist.setMinimumWidth(100)
        plot_viewbox      = self.plot_hist.getViewBox()
        plot_viewbox.invertX(True)
        self.plot_hist.showAxis('right')
        self.plot_hist.hideAxis('left')
        self.plot_hist.showGrid(x=True)
        plot_viewbox.setAspectLocked(False)
        plot_viewbox.enableAutoRange(pg.ViewBox.YAxis, enable=True)
        # --- measured data --- #
        self.data_hist = pg.PlotDataItem()
        self.plot_hist.addItem(self.data_hist)
        # --- widgets --- #
        self.spanNumber     = QSpinBox()#QPushButton('add new span')
        self.spanNumber.setMaximum(20)
        self.spanNumber.setValue(0)
        self.spanNumber.valueChanged.connect( self.makeSpans )
        # --- make layout --- #
        self.histogFrame = QFrame()
        self.histogFrame.setToolTip('Vertical histogram of the image. We integrated over the Y-axis of the image.')
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
        self.plot_max = PeakPlot(name='plot_max', span=None, log=self.log)
        #self.dicmultiplot[self.plot_max.name] = [self.plot_max]
        # ---  --- #
        self.spanNumber.valueChanged.connect( self.updateMultiplots )
        self.samplingtime.valueChanged.connect( self.updatePtNbrLabel )
        self.camera_view.fps_input.valueChanged.connect( self.updatePtNbrLabel )
        # --- make layout --- #
        label_1 = QLabel('Sampling time (s): ')
        label_1.setWordWrap(True)
        label_2 = QLabel('(s) --> pts nbr:')
        label_2.setWordWrap(True)
        self.multiplotFrame = QFrame()
        self.multiplotFrame.setToolTip('Multiplot frame. Each plot correspond to the post-processed data sampling of the corresponding span number.')
        layout = QGridLayout()
        layout.addWidget(label_1 , 0,0)
        layout.addWidget(self.samplingtime                 , 0,1)
        layout.addWidget(label_2     , 0,2)
        layout.addWidget(self.samplingPtNbr                , 0,3)
        layout.addWidget(self.multi_plot                   , 1,0 , 1,4)
        self.multiplotFrame.setLayout( layout )

    def initLissajousPlot(self):
        self.lissajousFrame = QFrame()
        self.lissajousFrame.setToolTip('Lissajous plot. We plot the post processed intensities as expressed below the graph.')
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
        lissjs_viewbox.setRange(xRange=(-1,+1), yRange=(-1,+1))
        self.plot_xaxis  = QComboBox()
        self.plot_yaxis  = QComboBox()
        self.makeLissajousAxisSelection()
        self.button_plot_lissajs = QPushButton('Plot')
        self.button_plot_lissajs.setCheckable(True)
        # --- make layout --- #
        label_equation = QLabel('-    i = (I/I_tot)\n- x,y = [i-(i_Max+i_min)/2]/(i_Max-i_min)/2')
        label_equation.setWordWrap(True)
        layout = QGridLayout()
        layout.addWidget( QLabel('X axis') , 0,1)
        layout.addWidget( QLabel('Y axis') , 0,2)
        layout.addWidget( QLabel('Plot : '), 1,0)
        layout.addWidget( self.plot_xaxis  , 1,1)
        layout.addWidget( self.plot_yaxis  , 1,2)
        layout.addWidget( self.button_plot_lissajs, 2,0 , 1,3)
        layout.addWidget( self.plot_lissjs , 3,0 , 1,3)
        layout.addWidget( QHLine()         , 4,0 , 1,3)
        layout.addWidget( label_equation   , 5,0 , 1,3)
        self.lissajousFrame.setLayout( layout )

    def setNewSaveFile(self):
        # --- stop timers to avoid over load --- #
        wasOn = self.camera_view.isOn
        self.camera_view.stop_continuous_view()
        # ---  --- #
        filename = self.savefile.getSaveFileName(None)
        if filename == '':
            # --- restart processes --- #
            if wasOn:
                self.camera_view.start_continuous_view()
            return False
        dir_path = self.savefile.directory().absolutePath()
        os.chdir(dir_path)
        self.savefile_name.setText( filename[0] )
        # --- restart processes --- #
        if wasOn:
            self.camera_view.start_continuous_view()
        # ---  --- #
        return True

    def saveDataFromMultiplot(self):
        # --- stop timers to avoid over load --- #  # we stop the process because it does not work while timer is running
        wasOn = self.camera_view.isOn
        self.camera_view.stop_continuous_view()
        # --- check if there are spans --- #
        if self.spanNumber.value() == 0:
            # --- restart processes --- #
            if wasOn:
                self.camera_view.start_continuous_view()
            return None
        # --- set file name --- #
        hasWorked = self.setNewSaveFile()
        if not hasWorked:
            # --- restart processes --- #
            if wasOn:
                self.camera_view.start_continuous_view()
            return None
        # ---  open file save --- #
        filename = self.savefile_name.text()
        try:
            f = open(filename, 'w+')
        except:
            err_msg  = 'Error: in saveDataFromMultiplot, not able to open file.'
            err_msg += '\nFilename is: {}'.format(filename)
            self.log.addText( err_msg )
        # --- make save --- #
        min_len   = np.inf
        data_list = []
        for key in self.dicmultiplot: # adding data from each plot in multiplot view
            data_list.append( self.dicmultiplot[key][0].plot.yData )
            min_len = np.min( [min_len, len(data_list[-1])] )
        # --- adding the data fot the total intensity --- #
        data_list.append( self.plot_max.plot.yData )
        min_len = np.min( [min_len, len(data_list[-1])] )
        # ---  --- #
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
        self.setSameYAxisMultiplots()

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

    def setSameYAxisMultiplots(self):
        key_init = list(self.dicmultiplot.keys())[0]
        common_viewBox = self.dicmultiplot[key_init][0].getViewBox()
        common_viewBox.enableAutoRange(pg.ViewBox.YAxis, enable=True)
        for key in self.dicmultiplot:
            plot = self.dicmultiplot[key][0]
            plot.setYLink(common_viewBox)

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

    def setPostProcessFunction(self):
        ind = self.postprocss.currentIndex()
        if   ind == 0:
            func = eval("lambda x_data: np.max(x_data)")
            self.postprocss_func = func
        elif ind == 1:
            func = eval("lambda x_data: np.sum(x_data)")
            self.postprocss_func = func
        return None

    def setFittingRate(self):
        self.fittingtimer.setInterval(1e3/self.frqcyfitting.value())

    def setHistgrmPlotRange(self):
        ind = self.histogram_data.currentIndex()
        if   ind == 0 or ind == 1:
            self.plot_hist.getViewBox().enableAutoRange(pg.ViewBox.XAxis, enable=True)
        elif ind == 2:
            self.plot_hist.setXRange(0, 1.)

    def postProcessLissajous(self, xy_data):
        Max_ = np.max(xy_data)
        min_ = np.min(xy_data)
        A    = (Max_ + min_)*0.5
        B    = (Max_ - min_)*0.5
        return (xy_data-A)/B

    def updatePlotHistogram(self):
        frame = self.camera_view.frame
        if type(frame) == type(None):
            return None
        # --- mode data --- #
        ind = self.histogram_data.currentIndex()
        if   ind == 0: # raw
            ydata = np.sum(frame,axis=0)/frame.shape[0]
        elif ind == 1: # remove background
            frame = frame-np.mean(frame)
            ydata = np.sum(frame,axis=0)/frame.shape[0]
            ydata = ydata + np.abs(np.min([0, np.min(ydata)]))
        elif ind == 2: # normalise
            ydata = np.sum(frame,axis=0)/frame.shape[0]
            ydata = ydata/np.max(ydata)
        # --- plot data --- #
        self.data_hist.setData( ydata, np.arange(len(ydata)) )
        # ---  --- #
        self.updateMultiplots()

    def updateMultiplots(self):
        if type(self.postprocss_func) == type(None):
            self.setPostProcessFunction()
        # ---  --- #
        sum_max_peak = 0
        data = self.data_hist.xData
        for key in self.dicmultiplot:
            plot = self.dicmultiplot[key][0]
            plot.setLengthMax( int(self.samplingtime.value()*self.camera_view.fps) )
            # ---  --- #
            region = plot.span.span.getRegion()
            m , M  = int(np.min(region)), int(np.max(region))
            err_msg  = ''
            cond_1 = type(data) != type(None) and m != M
            cond_2 = len(data) >= m or len(data) >= M
            cond_3 = len(data[m:M]) != 0
            if cond_1 and cond_2 and cond_3:
                try:
                    new_val = self.postprocss_func(data[m:M])# np.max(data[m:M])
                    plot.addDataElement( new_val )
                except:
                    err_msg += 'Error: in updatePlot for object PeakPlot: '+plot.name
                    err_msg += '\nIssue with: self.addDataElement( np.max(self.data[m:M]) ),'
                    err_msg += '\nsample: {}'.format(self.data[m:M])
            else:
                err_msg += '\nOne of the following condition is unsatisfied:\n \
                type(data) != type(None) and m != M: {0}\n \
                len(data) >= m or len(data) >= M: {1}\n \
                len(data[m:M]) != 0: {2}'.format(cond_1,cond_2,cond_3)
                self.log.addText( err_msg )
            # ---  --- #
            sum_max_peak += plot.peakdata[-1]
        self.plot_max.setLengthMax( int(self.samplingtime.value()*self.camera_view.fps) )
        self.plot_max.addDataElement(sum_max_peak)
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
        max_data  = self.plot_max.plot.yData
        if type(xdata) != type(None) and type(ydata) != type(None):
            n = np.min( [len(xdata), len(ydata), len(max_data)] )
            xdata = xdata[-n:]/max_data[-n:]
            ydata = ydata[-n:]/max_data[-n:]
            xdata = self.postProcessLissajous(xdata)
            ydata = self.postProcessLissajous(ydata)
            self.data_lissjs.setData( xdata, ydata )

    def updatePtNbrLabel(self):
        self.samplingPtNbr.setText( str(self.samplingtime.value()*self.camera_view.fps) )

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
    start_window = PhaseNetworkElements(camera)
    start_window.show()
    app.exit(app.exec_())
    print('Close camera')
    camera.close_camera()

    print('FINISHED')
