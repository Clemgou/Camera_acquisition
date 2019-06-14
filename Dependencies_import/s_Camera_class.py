#!/usr/bin/env python
# -*- coding: utf-8 -*-



#########################################################################################################################
# IMPORTATION
#########################################################################################################################
import time
import numpy as np
import matplotlib.pyplot as plt
import cv2


#########################################################################################################################
# FUNCTIONS
#########################################################################################################################


def generatePgColormap(cm_name):
    pltMap = plt.get_cmap(cm_name)
    colors = pltMap.colors
    colors = [c + [1.] for c in colors]
    positions = np.linspace(0, 1, len(colors))
    pgMap = pg.ColorMap(positions, colors)
    return pgMap




class Camera:
    def __init__(self, cam_num=-1):
        self.cam_num = cam_num
        self.cap     = None
        # ---  --- #
        self.initialize()

    def initialize(self):
        self.cap = cv2.VideoCapture(self.cam_num)

    def __str__(self):
        print('OpenCV Camera number {}'.format(self.cam_num))
        ret, frame = self.cap.read()
        print(frame.shape)
        return 'OpenCV Camera number {}'.format(self.cam_num)

    def get_frame(self):
        ret, self.last_frame = self.cap.read()
        return self.last_frame

    def acquire_movie(self, num_frames):
        movie = []
        for _ in range(num_frames):
            movie.append(self.get_frame())
        return movie

    def set_brightness(self, value):
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, value)

    def get_brightness(self):
        return self.cap.get(cv2.CAP_PROP_BRIGHTNESS)

    def close_camera(self):
        self.cap.release()






#########################################################################################################################
# CODE
#########################################################################################################################

if __name__ == '__main__':
    print('STARTING')
    camera = Camera(0)
    camera.__str__()
    camera.close_camera()
    print('FINISHED')
