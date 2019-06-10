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


import numpy as np
import pyqtgraph as pqtg
import os

################################################################################################ 
# FUNCTIONS
################################################################################################

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
        self.insertMainWidget()

    def initWindowMenu(self):
        '''
        Initialize the menu of the MainWindow.
        '''
        self.menubar = self.menuBar() # we define an attribute, menubar, which derives from the method menuBar() that comes from the QMainWindow parent object.
        # --- set the main menus --- #
        self.filemenu       = self.menubar.addMenu('&File')
        self.structuresmenu = self.menubar.addMenu('&Structures')
        self.statusBar()
        # --- set the actions in the different menues --- #
        self.newStructureItem()
        self.newFilemenuItem()
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

    def newFilemenuItem(self):
        # --- Exit application --- #
        closeapp = QAction('&Exit', self) # QAction(QIcon('incon.png'), '&Exit', self)
        closeapp.triggered.connect(self.closeMainWindow)
        self.filemenu.addAction( '------' )
        self.filemenu.addAction(closeapp)

    def newStructureItem(self):
        '''
        Make a new tab window with the display of the chosen structure (SWG, BS, ...).
        '''
        # --- Main Tab --- #
        openNewtab  = QAction('Main', self)
        openNewtab.triggered.connect(self.insertMainWidget)
        self.structuresmenu.addAction(openNewtab)
        # --- Lissajous plot tab --- #
        openNewtab  = QAction('Lissajous (Li)', self)
        openNewtab.triggered.connect(self.insertNewTabLissajousPlot)
        self.structuresmenu.addAction(openNewtab)

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

    def closeMainWindow(self):
        self.close()

    def insertMainWidget(self):
        newtabindex = self.centraltab.addTab( self.centralwidget, "Main" ) # also: addTab(QWidget , QIcon , QString )
        self.centraltab.setCurrentIndex( newtabindex )

    def insertNewTabLissajousPlot(self):
        newtabindex = self.centraltab.addTab( StraightWaveGuide(self.simuobjct), "Lissa" ) # also: addTab(QWidget , QIcon , QString )
        self.centraltab.setCurrentIndex( newtabindex )

################################################################################################
# CODE
################################################################################################
if __name__=='__main__':
    appMain = QApplication(sys.argv)
    wind  = MainWindow()
    wind.show()
    sys.exit(appMain.exec_())

