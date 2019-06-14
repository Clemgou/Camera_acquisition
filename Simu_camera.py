#!/usr/bin/env python
# -*- coding: utf-8 -*-



#########################################################################################################################
# IMPORTATION
#########################################################################################################################
import matplotlib.pyplot as plt
import cv2


import os


#########################################################################################################################
# FUNCTIONS
#########################################################################################################################





#########################################################################################################################
# CODE
#########################################################################################################################

##### PyQt GUI application #####


class SimuCamera:
    def __init__(self, cam_num=-1):
        self.cam_num = cam_num
        self.cap     = None
        # ---  --- #
        self.initialize()

    def initialize(self):
        self.viewpath = '/home/cgou/ENS/STAGE/M2--stage/CircuitsNetwork_phase_analysis/Camera_views/'
        self.viewlist = os.listdir(self.viewpath)
        self.viewnbr  = len(self.viewlist)
        self.lastindx = 0
        # ---  --- #
        #self.cap = cv2.VideoCapture(self.cam_num)

    def __str__(self):
        print(self.lastindx)
        print(self.viewnbr)
        return None
        # ---  --- #
        print('OpenCV Camera number {}'.format(self.cam_num))
        ret, frame = self.cap.read()
        print(frame.shape)
        return 'OpenCV Camera number {}'.format(self.cam_num)

    def get_frame(self, mode=0):
        #ret, self.last_frame = self.cap.read()
        # ---  --- #
        self.last_frame = cv2.imread(self.viewpath+self.viewlist[self.lastindx])
        self.lastindx = (self.lastindx+1)%self.viewnbr
        # ---  --- #
        if mode != 0:
            if   mode=='Grey' or mode==1:
                self.last_frame = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2GRAY)
            elif mode=='HSV'  or mode==2:
                self.last_frame = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2HSV)
            else:
                print('mode argument not recognised.')
        # ---  --- #
        return self.last_frame

    def acquire_movie(self, num_frames):
        movie = []
        for _ in range(num_frames):
            movie.append(self.get_frame())
        return movie

    def close_camera(self):
        return None




if __name__ == '__main__':
    print('OpenCV 2 version: ',cv2.__version__)
    print('STARTING')
    camera = SimuCamera(0)
    print(camera.get_frame().shape)
    print('FINISHED')
