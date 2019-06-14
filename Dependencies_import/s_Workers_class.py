#!/usr/bin/env python
# -*- coding: utf-8 -*-



#########################################################################################################################
# IMPORTATION
#########################################################################################################################
import sys
sys.path.insert(0, './Dependencies_import')


import time
import numpy as np
import matplotlib.pyplot as plt
import cv2
import pyqtgraph as pg

import PyQt5
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication, QLineEdit, QHBoxLayout, QSpinBox
from PyQt5.QtCore import Qt, QThread, QTimer, QObject, pyqtSignal, pyqtSlot



#########################################################################################################################
# FUNCTIONS
#########################################################################################################################

class ContinuousView(QObject):
    # --- signal perso --- #
    newshot  = pyqtSignal()
    finished = pyqtSignal()
    # ---  --- #
    def __init__(self, fps=2., camera=None, view=None):
        super().__init__()
        self.camera   = camera
        self.view     = view
        self.fps      = fps
        self.acqutime = 10 #s

    @pyqtSlot()
    def startFeed(self):
        self.continue_ = True
        i = 0
        while self.continue_ and i<(self.acqutime*self.fps) :
            time.sleep(1/self.fps)
            self.newshot.emit()
            print(i)
            i += 1
        self.finished.emit()

    def stopFeed(self):
        self.continue_ = False

    def setFPS(self, fps):
        self.fps = fps

#########################################################################################################################
# CODE
#########################################################################################################################
if __name__ == '__main__':
    print('STARTING')
    print('FINISHED')
