#!/usr/bin/env python
# -*- coding: utf-8 -*-



###################################################################################################################
# IMPORTATION
###################################################################################################################
import matplotlib.pyplot as plt
import cv2


import os


###################################################################################################################
# FUNCTIONS
###################################################################################################################

class SimuCamera:
    def __init__(self, cam_num=-1, directory_path=None, log=None, color_mode='Grey'):
        self.cam_num = cam_num
        self.cap     = None
        self.colorMode = color_mode
        self.viewpath = directory_path
        self.log     = log
        # ---  --- #
        self.initialize()

    def initialize(self):
        try:
            self.viewlist = os.listdir(self.viewpath)
            self.viewnbr  = len(self.viewlist)
            self.isCameraInit = True
        except:
            self.addToLog('Error: no valid path given.\nCurrent path is: {}'.format(self.viewpath))
            self.close_camera()
            self.isCameraInit = False
            return None
        # ---  --- #
        if self.viewnbr == 0:
            self.addToLog('Error: directory empty.')
            self.close_camera()
        # ---  --- #
        self.lastindx   = 0
        self.last_frame = None

    def addToLog(self, txt):
        if self.log != None:
            self.log.addText(txt)
        else:
            print(txt)

    def __str__(self):
        self.addToLog('Current directory path      : {}'.format(self.viewpath))
        self.addToLog('Current image index         : {}'.format(self.lastindx))
        self.addToLog('Number of image in directory: {}'.format(self.viewnbr))
        return None

    def change_colormode(self, colormode):
        self.colorMode = colormode

    def get_frame(self):
        self.last_frame = cv2.imread(self.viewpath+self.viewlist[self.lastindx])
        self.lastindx   = (self.lastindx+1)%self.viewnbr
        # ---  --- #
        if self.colorMode != 0:
            if   self.colorMode=='Grey' or self.colorMode==1:
                self.last_frame = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2GRAY)
            elif self.colorMode=='HSV'  or self.colorMode==2:
                self.last_frame = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2HSV)
            else:
                self.addToLog('mode argument not recognised.')
        # ---  --- #
        return self.last_frame

    def acquire_movie(self, num_frames):
        movie = []
        for _ in range(num_frames):
            movie.append(self.get_frame())
        return movie

    def capture_video(self):
        return None

    def stop_video(self):
        return None

    def close_camera(self):
        self.isCameraInit = False
        return None

    def set_aoi(self, x,y,w,h):
        return None

    def set_colormode(self):
        return None

    def alloc(self):
        return None

    def setExposure(self, exp_val):
        return None

    def setHarwareGain(self, gain_val):
        return None

###################################################################################################################
# CODE
###################################################################################################################

if __name__ == '__main__':
    print('OpenCV 2 version: ',cv2.__version__)
    print('STARTING')
    #camera = SimuCamera(0)
    #print(camera.get_frame().shape)
    print('FINISHED')
