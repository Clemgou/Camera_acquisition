#!/usr/bin/env python
# -*- coding: utf-8 -*-



#########################################################################################################################
# IMPORTATION
#########################################################################################################################
import sys
import PyQt5
from PyQt5.QtWidgets import QWidget, QFrame, QApplication
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QSplitter, QGridLayout
from PyQt5.QtWidgets import QLabel, QPushButton, QLineEdit, QSpinBox, QProgressBar, QComboBox, QFileDialog, QSlider
from PyQt5.QtCore    import Qt, QThread, QTimer, QObject, pyqtSignal, pyqtSlot, QRect
from PyQt5.QtGui     import QPainter


import numpy             as np
import matplotlib.pyplot as plt
import pyqtgraph         as pg
from PIL        import Image


from s_LogDisplay_class               import LogDisplay
from s_Workers_class                  import *
from s_Miscellaneous_functions        import *
from s_SimuCamera_class               import SimuCamera
from s_Camera_class                   import Camera


import time
#########################################################################################################################
# FUNCTIONS
#########################################################################################################################

class Preview(QWidget):
    def __init__(self, camera=None, log=None, fps=10.):
        super().__init__()
        # ---  --- #
        if log != None:
            self.log = log
        else:
            self.log = LogDisplay()
        self.log.show()
        # --- default --- #
        self.fps       = fps
        self.normalise_hist = True
        self.cmap      = 'jet'
        # --- main attriute --- #
        self.camera    = camera
        if self.camera == None:
            dir_path = '/home/cgou/ENS/STAGE/M2--stage/Camera_acquisition/Miscellaneous/Camera_views/'
            self.camera   = Camera(cam_id=0, log=self.log)
            if not self.camera.isCameraInit:
                self.camera = SimuCamera(0, directory_path=dir_path, log=self.log)
                self.camera.__str__()
        # ---  --- #
        self.contview  = ContinuousView(fps=self.fps)
        self.timer     = pg.QtCore.QTimer() #QTimer()# pg.QtCore.QTimer()
        self.qlabl_max = QLabel()
        self.isOn      = False
        # --- color acuisition --- #
        self.initColorDic()
        self.initCamera()
        # ---  --- #
        self.initUI()

    def initUI(self):
        # ---  --- #
        self.layout      = QVBoxLayout(self)
        self.initView()
        # --- button widget --- #
        self.button_acquire   = QPushButton('Acquire frame')
        self.button_acquire.setStyleSheet("background-color: orange")
        self.button_acq_movie = QPushButton('Acquire movie')
        self.button_acq_movie.setStyleSheet("background-color: orange")
        self.button_startstop = QPushButton('Start/Stop')
        self.button_startstop.setStyleSheet("background-color: red")
        self.button_nextFrame = QPushButton('Next frame')
        # ---  --- #
        self.fps_input        = QSpinBox()
        self.fps_input.setRange(1, 48)
        self.fps_input.setValue(self.fps)
        self.movie_frameNbre  = QSpinBox()
        self.movie_frameNbre.setMinimum(0)
        self.movie_frameNbre.setMaximum(1000)
        self.movie_frameNbre.setValue(200)
        self.dir_save         = QFileDialog()
        self.dir_save_label   = QLabel('No file selected')
        self.dir_save_label.setWordWrap(True)
        self.name_save        = QLineEdit()
        self.name_save.setText('img_data')
        self.progressbar      = QProgressBar()
        self.progressbar.setValue(0)
        self.format_save      = QComboBox()
        self.format_save.addItem('png')
        self.format_save.addItem('tif')
        self.format_save.addItem('tiff')
        self.format_save.addItem('jpg')
        self.histogram_mode   = QComboBox()
        self.histogram_mode.addItem('Normalise')
        self.histogram_mode.addItem('Raw')
        self.exposure_slider  = QSlider(Qt.Horizontal)
        self.exposure_slider.setRange(0.10, 99.00)
        self.exposure_slider.setValue(1.)
        self.exposure_label   = QLabel('Exposure time: {: 2.2f} ms'.format(self.exposure_slider.value()))
        # --- connections --- #
        self.button_startstop.clicked.connect(self.startStop_continuous_view)
        self.fps_input.valueChanged.connect(self.setFPS)
        self.button_acquire.clicked.connect(self.acquireFrame)
        self.button_nextFrame.clicked.connect( self.nextFrame )
        self.button_acq_movie.clicked.connect( self.acquireMovie )
        self.histogram_mode.currentIndexChanged.connect( self.setHistogramMode )
        self.exposure_slider.valueChanged.connect( self.update_exposure )
        # --- layout --- #
        grid     = QGridLayout()
        grid.addWidget( self.button_startstop , 0,0 , 1,3)
        grid.addWidget( self.button_nextFrame , 0,3 , 1,3)
        grid.addWidget( QLabel('Mode histogram:'), 1,0)
        grid.addWidget( self.histogram_mode   , 1,1)
        grid.addWidget( QLabel('fps :')       , 1,2)
        grid.addWidget( self.fps_input        , 1,3)
        grid.addWidget( QLabel('value max:')  , 1,4)
        grid.addWidget( self.qlabl_max        , 1,5)
        grid.addWidget( self.exposure_label   , 2,0)
        grid.addWidget( self.exposure_slider  , 2,1 , 1,5)
        self.layout.addLayout(grid)
        self.layout.addWidget(self.image_view)
        self.layout.addWidget(self.view_layout)
        grid      = QGridLayout()
        grid.addWidget(self.button_acquire      , 0,0 , 1,3)
        grid.addWidget(QLabel('Number of frame'), 1,0)
        grid.addWidget(self.movie_frameNbre     , 1,1)
        grid.addWidget(self.button_acq_movie    , 1,2)
        grid.addWidget( QLabel('Filemane prefix:') , 2,0)
        grid.addWidget( self.name_save          , 2,1)
        grid.addWidget( self.format_save        , 2,2)
        grid.addWidget( QLabel('Directory:')    , 3,0)
        grid.addWidget( self.dir_save_label     , 3,1 , 1,2)
        grid.addWidget( self.progressbar        , 4,0 , 1,3)
        self.layout.addLayout( grid )
        self.setLayout(self.layout)
        # ---  --- #
        self.update_timer = QTimer()

    def initCamera(self):
        self.camera.set_colormode()
        self.camera.set_aoi(0,0, 1280,1024)
        self.camera.alloc()

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
            self.plot_hist.enableAutoRange(y=True)
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

    def setHistogramMode(self, indx):
        val = self.histogram_mode.currentText()
        if   val == 'Normalise':
            self.normalise_hist = True
            self.plot_hist.setYRange(0, 1)
        elif val == 'Raw':
            self.normalise_hist = False
            self.plot_hist.enableAutoRange(y=True)

    def nextFrame(self):
        wasOn = self.isOn
        if not self.isOn:
            self.camera.capture_video()
        # ---  --- #
        self.update_image()
        # ---  --- #
        if not wasOn:
            self.camera.capture_video()

    def update_image(self):
        frame = self.camera.get_frame()
        if type(frame) != type(None):
            self.updatePlotHistogram(frame)
            self.qlabl_max.setText( str(np.max(frame)) )
            self.image_view.setImage(frame.T, autoHistogramRange=False, autoLevels=False)

    def updatePlotHistogram(self, frame):
        if self.normalise_hist:
            bckgrnd = np.mean(frame)
            frame  = frame-bckgrnd
        ydata  = np.sum(frame,axis=0)/frame.shape[0]
        if self.normalise_hist:
            ydata -= np.min([0, np.min(ydata)])
            ydata = ydata/np.max(ydata)
        self.data_hist.setData(ydata)

    def update_exposure(self):
        exp_val = self.exposure_slider.value()
        self.camera.setExposure( exp_val )
        self.exposure_label.setText( 'Exposure time: {: 2.2f} ms'.format(self.exposure_slider.value()) )

    def acquireFrame(self):
        wasOn = self.isOn
        if self.isOn:
            self.startStop_continuous_view()
        # ---  --- #
        frame = self.camera.frame
        if type(frame) != type(None):
            plt.imshow(frame, cmap=self.cmap)
            plt.show()
        # ---  --- #
        if wasOn:
            self.startStop_continuous_view()

    def acquireMovie(self):
        wasOn = self.isOn
        if self.isOn:
            self.startStop_continuous_view()
        # ---  --- #
        dir_save_path = self.dir_save.getExistingDirectory() + '/'
        self.dir_save_label.setText( dir_save_path )
        filename      = self.name_save.text()
        format_       = self.format_save.currentText()
        # ---  --- #
        self.progressbar.setValue(0)
        self.progressbar.setMaximum( self.movie_frameNbre.value() )
        # ---  --- #
        movie = self.camera.acquire_movie( self.movie_frameNbre.value() )
        try:
            img_to_save = Image.fromarray( movie[0] )
            img_to_save.save( dir_save_path+filename+'_{0:03d}.{1}'.format(0, format_) )
            self.progressbar.setValue(1)
        except:
            err_msg  = 'Error: in acquireMovie. The filename is not accepted\nFilename: {0}\nDirectory path: {1}'.format(filename, dir_save_path)
            self.log.addText( err_msg )
            return None
        for i in range(1, len(movie) ):
            img_to_save = Image.fromarray( movie[i] )
            img_to_save.save( dir_save_path+filename+'_{0:03d}.{1}'.format(i, format_) )
            self.progressbar.setValue(i+1)
        # ---  --- #
        if wasOn:
            self.startStop_continuous_view()

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
        self.camera.capture_video()
        if   True:
            self.start_continuous_view_qtimer()
        elif False:
            self.start_continuous_view_qthread()
        # ---  --- #
        self.isOn = True

    def stop_continuous_view(self):
        self.camera.stop_video()
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
        self.timer.timeout.connect(self.update_image)
        self.timer.start(1e3/self.fps) #ms

    def stop_continuous_view_qtimer(self):
        self.timer.stop()

#########################################################################################################################
# CODE
#########################################################################################################################
if __name__ == '__main__':
    print('STARTING')
    app = QApplication([])
    start_window = Preview()
    start_window.show()
    app.exit(app.exec_())
    print('Close camera')
    start_window.camera.close_camera()
    print('FINISHED')
