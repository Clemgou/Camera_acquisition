#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################################ 
# IMPORTATIONS
################################################################################################
import sys
sys.path.insert(0, './Dependencies_import')
import PyQt5
from PyQt5.QtWidgets import QDesktopWidget, QApplication, QMainWindow, QWidget, QFrame, QTabWidget, QTableWidget
from PyQt5.QtWidgets import QBoxLayout,QGroupBox,QHBoxLayout,QVBoxLayout,QGridLayout,QSplitter,QScrollArea
from PyQt5.QtWidgets import QToolTip, QPushButton, QLabel, QLineEdit, QTextEdit, QCheckBox, QComboBox, QInputDialog
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QAction
from PyQt5.QtGui     import QIcon, QFont
from PyQt5.QtCore    import QDate, QTime, QDateTime, Qt



from s_LogDisplay_class               import LogDisplay
from s_Preview_class                  import Preview
from s_DCMeasurement_class            import DCMeasurement

from Simu_camera import *

import numpy as np
import os

################################################################################################ 
# FUNCTIONS
################################################################################################

class CameraManagementWindow(QMainWindow):
    def __init__(self, camera=None):
        super().__init__()
        self.camera        = camera
        self.layout        = QGridLayout()
        self.centralwidget = QWidget()
        # ---  --- #
        self.centralwidget.setLayout( self.layout )
        self.setCentralWidget(self.centralwidget)
        # ---  --- #
        self.initUI()

    def initUI(self):
        self.cameraname = QLabel()
        self.open_state = QLabel()
        # --- make layout --- #
        self.layout.addWidget( QLabel('Just to display something') )

    def displayCameraProperties(self):
        opened       = self.camera.isOpened()
        pos          = self.camera.get(cv2.CAP_PROP_POS_MSEC)
        frame_width  = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        frame_height = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps          = self.camera.get(cv2.CAP_PROP_FPS)
        format_frame_data = self.camera.get(cv2.CAP_PROP_FORMAT)
        brightness   = self.camera.get(cv2.CAP_PROP_BRIGHTNESS)
        contraste    = self.camera.get(cv2.CAP_PROP_CONTRAST)
        saturation   = self.camera.get(cv2.CAP_PROP_SATURATION)
        color_hue    = self.camera.get(cv2.CAP_PROP_HUE)
        exposure     = self.camera.get(cv2.CAP_PROP_EXPOSURE)
        gain         = self.camera.get(cv2.CAP_PROP_GAIN)
        conversion  = self.camera.get(cv2.CAP_PROP_CONVERT_RGB)



class MainWindow(QMainWindow): # inherits from the QMainWindow class
    def __init__(self):
        super().__init__() # The super() method returns the parent object of the MainWindow class, and we call its constructor. This means that we first initiate the QWidget class constructor.
        #self.app = QApplication([]) # only one per application

        # --- paths --- #
        self.localpath  = os.path.dirname(os.path.realpath(__file__))
        self.importpath = 'Dependencies_import/'
        self.iconpath   = 'IMGdirectory/'
        # --- initialisations --- #
        self.initWindow()
        self.initWindowMenu()

        #self.show()
        #self.app.exec_()

    def initWindow(self):
        '''
        Initialize the MainWindow configuration and display.
        '''
        # --- geometry and position --- #
        x0, y0, w, h = 150, 100, 900, 800
        self.setGeometry(x0, y0, w, h)
        self.setWindToCenter() # use the method defined below to center the window in the screen
        # --- names and titles --- #
        mytitle = "Main window"
        self.setWindowTitle(mytitle)
        mainapp_iconpath = r"./" + self.importpath + self.iconpath + "icon_mainapp.png"
        self.setWindowIcon(QIcon(mainapp_iconpath))
        # --- Parent Widget : central widget --- #
        self.initMainWidget()
        self.initTabLayout()
        # --- make  log display tab --- #
        self.log        = LogDisplay()
        self.insertNewTabLogDisplay(self.log)
        # --- main attributes --- #
        self.camera = SimuCamera(0)
        self.cameraManag = CameraManagementWindow()

    def initWindowMenu(self):
        '''
        Initialize the menu of the MainWindow.
        '''
        self.menubar = self.menuBar() # we define an attribute, menubar, which derives from the method menuBar() that comes from the QMainWindow parent object.
        # --- set the main menus --- #
        self.filemenu     = self.menubar.addMenu('&File')
        self.setupmenu    = self.menubar.addMenu('&Setups')
        self.toolsmenu    = self.menubar.addMenu('&Tools')
        self.cameramenu   = self.menubar.addMenu('&Camera')
        self.statusBar()
        # --- set the actions in the different menues --- #
        self.initFileMenu()
        self.initSetupMenu()
        self.initToolsMenu()
        self.initCameraMenu()
        #self.getFile()

    def initMainWidget(self):
        self.centralwidget = QWidget() # QMainWindow needs a QWidget to display Layouts. Thus we define a central widget so that all

    def initTabLayout(self):
        # ---  --- #
        self.centraltab    = QTabWidget()
        self.centraltab.setTabShape(0)
        self.centraltab.setTabsClosable(True)
        self.centraltab.tabCloseRequested.connect( self.closeTabe )
        self.setCentralWidget(self.centraltab)

    def setWindToCenter(self):
        '''
        Set the MainWindow at the center of the desktop.
        '''
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def closeTabe(self, index):
        '''
        Remove the Tab of index index (integer).
        '''
        self.centraltab.removeTab(index)

    def getFile(self):
        '''
        Set the menue bar such that we can fetch a text file and display
        it on a textEdit widget
        '''
        self.textEdit = QTextEdit()
        grid          = QGridLayout()
        grid.addWidget(self.textEdit,3,1,5,1)
        self.centralwidget.setLayout(grid)

        openFile = QAction('Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open new File')
        openFile.triggered.connect(self.showDialog)

        self.filemenu.addAction(openFile)

    def initFileMenu(self):
        # --- Exit application --- #
        closeapp = QAction('&Exit', self) # QAction(QIcon('incon.png'), '&Exit', self)
        closeapp.triggered.connect(self.closeMainWindow)
        self.filemenu.addAction( '------' )
        self.filemenu.addAction(closeapp)

    def initSetupMenu(self):
        '''
        Make a new tab window with the display of the chosen structure (SWG, BS, ...).
        '''
        # --- Preview --- #
        openNewtab  = QAction('Preview', self)
        openNewtab.triggered.connect(self.insertNewTabPreview)
        self.setupmenu.addAction(openNewtab)
        # --- DC plot tab --- #
        openNewtab  = QAction('Peak comparison (PkComp)', self)
        openNewtab.triggered.connect(self.insertNewTabPeakComparison)
        self.setupmenu.addAction(openNewtab)
        # --- Lissajous plot tab --- #
        openNewtab  = QAction('Lissajous (Li)', self)
        openNewtab.triggered.connect(self.insertNewTabLissajousPlot)
        self.setupmenu.addAction(openNewtab)

    def initToolsMenu(self):
        '''
        Make a new tab window with the display of the chosen structure (SWG, BS, ...).
        '''
        # --- Application diagram --- #
        openNewtab  = QAction('App diagram', self)
        openNewtab.triggered.connect(self.insertNewTabAppDiagram)
        self.toolsmenu.addAction(openNewtab)

    def initCameraMenu(self):
        '''
        Make a new tab window with the display of the chosen structure (SWG, BS, ...).
        '''
        # --- Camera tab --- #
        openNewtab  = QAction('&Camera setup', self)
        openNewtab.triggered.connect(self.cameraManagementWindow)
        self.cameramenu.addAction(openNewtab)

    def cameraManagementWindow(self):
        self.cameraManag.show()

    def showDialog(self):
        '''
        Generate the window where we can browse for the wanted text file.
        '''
        fname = QFileDialog.getOpenFileName(self, 'Open file', './') #'/home/cgou')
        if fname[0]:
            f = open(fname[0], 'r')
            with f:
                data = f.read()
                self.textEdit.setText(data)

    def insertNewTabLogDisplay(self, log_objct):
        newtabindex = self.centraltab.addTab(log_objct,"Log")
        currentTbaBar = self.centraltab.tabBar()
        currentTbaBar.setTabButton(newtabindex, PyQt5.QtWidgets.QTabBar.RightSide, QLabel('')) # hide the close button
        self.centraltab.setCurrentIndex( newtabindex )

    def insertNewTabMainWidget(self):
        newtabindex = self.centraltab.addTab( self.centralwidget, "Main" ) # also: addTab(QWidget , QIcon , QString )
        self.centraltab.setCurrentIndex( newtabindex )

    def insertNewTabPreview(self):
        newtabindex = self.centraltab.addTab( Preview(camera=self.camera, log=self.log), "Preview" ) # also: addTab(QWidget , QIcon , QString )
        self.centraltab.setCurrentIndex( newtabindex )

    def insertNewTabAppDiagram(self):
        newtabindex = self.centraltab.addTab( self.centralwidget, "Main" ) # also: addTab(QWidget , QIcon , QString )
        self.centraltab.setCurrentIndex( newtabindex )

    def insertNewTabPeakComparison(self):
        newtabindex = self.centraltab.addTab( DCMeasurement(camera=self.camera, log=self.log), "PkComp" ) # also: addTab(QWidget , QIcon , QString )
        self.centraltab.setCurrentIndex( newtabindex )

    def insertNewTabLissajousPlot(self):
        newtabindex = self.centraltab.addTab( self.centralwidget, "Lissa" ) # also: addTab(QWidget , QIcon , QString )
        self.centraltab.setCurrentIndex( newtabindex )

    def closeMainWindow(self):
        self.close()

################################################################################################
# CODE
################################################################################################
if __name__=='__main__':
    appMain = QApplication(sys.argv)
    wind  = MainWindow()
    wind.show()
    sys.exit(appMain.exec_())

