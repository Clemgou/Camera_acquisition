#!/usr/bin/env python
# -*- coding: utf-8 -*-



#########################################################################################################################
# IMPORTATION
#########################################################################################################################
import sys
import PyQt5
from PyQt5.QtWidgets import QWidget, QFrame, QApplication
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QSplitter, QGridLayout
from PyQt5.QtWidgets import QLabel, QPushButton, QLineEdit, QSpinBox, QProgressBar, QComboBox, QFileDialog, QSlider, QDoubleSpinBox
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
from s_CameraDisplay_class            import CameraDisplay


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
        #self.log.show()
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
                self.camera.__info__()
        elif not self.camera.isCameraInit:
            self.camera.__init__(cam_id=0, log=self.log)
        # ---  --- #
        self.contview  = ContinuousView(fps=self.fps)
        self.timer     = pg.QtCore.QTimer() #QTimer()# pg.QtCore.QTimer()
        self.qlabl_max = QLabel()
        self.isOn      = False
        # ---  --- #
        self.initUI()
        # ---  --- #
        self.camera.setExposure( self.image_widget.exposure.value() )

    def initUI(self):
        # ---  --- #
        self.layout      = QVBoxLayout(self)
        self.initView()
        # --- button widget --- #
        self.button_acquire   = QPushButton('Acquire frame')
        self.button_acquire.setStyleSheet("background-color: orange")
        self.button_acq_movie = QPushButton('Acquire movie')
        self.button_acq_movie.setStyleSheet("background-color: orange")
        # ---  --- #
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
        self.format_save.addItem('tif')
        self.format_save.addItem('tiff')
        self.format_save.addItem('png')
        self.format_save.addItem('jpg')
        self.histogram_mode   = QComboBox()
        self.histogram_mode.addItem('Normalise')
        self.histogram_mode.addItem('Raw')
        # --- connections --- #
        self.button_acquire.clicked.connect(self.acquireFrame)
        self.button_acq_movie.clicked.connect( self.acquireMovie )
        self.histogram_mode.currentIndexChanged.connect( self.setHistogramMode )
        # --- layout --- #
        self.layout.addWidget( self.view_layout )
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

    def initView(self):
        self.image_widget = CameraDisplay(camera=self.camera, log=self.log)
        self.image_view   = self.image_widget.image_view
        # --- histogram --- #
        self.hist_layWidget = pg.GraphicsLayoutWidget()
        self.plot_hist      = self.hist_layWidget.addPlot()
        self.plot_hist.setXLink( self.image_view.getView() )
        if self.normalise_hist:
            self.plot_hist.setYRange(0, 1)
        else:
            self.plot_hist.enableAutoRange(y=True)
        # ---  --- #
        self.data_hist = pg.PlotDataItem()
        self.plot_hist.addItem(self.data_hist)
        # --- link histogram to image view --- #
        self.image_widget.frame_updated.connect( self.updatePlotHistogram )
        # ---  --- #
        self.image_view.setLevels(0,255)
        self.image_view.getHistogramWidget().item.setHistogramRange(0,255) #not working when update
        self.image_view.ui.roiBtn.hide()
        self.image_view.ui.menuBtn.hide()
        # ---  --- #
        self.image_view.setMinimumWidth(400)
        self.image_view.setMinimumHeight(200)
        self.hist_layWidget.setMinimumWidth(400)
        self.hist_layWidget.setMinimumHeight(100)
        # ---  --- #
        self.view_layout = QSplitter(PyQt5.QtCore.Qt.Vertical)
        self.view_layout.addWidget(self.image_widget)
        self.view_layout.addWidget(self.hist_layWidget)

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

    def updatePlotHistogram(self):
        frame = self.image_widget.frame
        if self.normalise_hist:
            bckgrnd = np.mean(frame)
            frame  = frame-bckgrnd
        ydata  = np.sum(frame,axis=0)/frame.shape[0]
        if self.normalise_hist:
            ydata -= np.min([0, np.min(ydata)])
            ydata = ydata/np.max(ydata)
        self.data_hist.setData(ydata)

    def update_slider(self):
        self.exposure_slider.setValue(self.exposure_spinb.value()*100)
        self.update_exposure()

    def update_spinbox(self):
        self.exposure_spinb.setValue(float(self.exposure_slider.value())/100)
        self.update_exposure()

    def update_exposure(self):
        exp_val = self.exposure_spinb.value()
        self.camera.setExposure( exp_val )

    def acquireFrame(self):
        wasOn = self.isOn
        if self.isOn:
            self.startStop_continuous_view()
        # ---  --- #
        try:
            frame = self.camera.frame
            plt.imshow(frame, cmap=self.cmap)
            plt.show()
        except:
            pass
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
