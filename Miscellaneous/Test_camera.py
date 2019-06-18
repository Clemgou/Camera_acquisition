#!/usr/bin/env python
# -*- coding: utf-8 -*-



#########################################################################################################################
# IMPORTATION
#########################################################################################################################
import sys
import time
import cv2
import numpy as np
import matplotlib.pyplot as plt

#########################################################################################################################
# FUNCTIONS
#########################################################################################################################

def Test_frame():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    # ---  --- #
    print(np.min(frame))
    print(np.max(frame))
    # ---  --- #
    if type(frame) != type(None):
        plt.imshow(frame)
        plt.show()

def Camera_test():
    cap = cv2.VideoCapture(0)
    # ---  --- #
    while(True):
        # Capture frame-by-frame
        ret, frame = cap.read()

        # Our operations on the frame come here
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Display the resulting frame
        cv2.imshow('frame',gray)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    # ---  --- #
    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

#########################################################################################################################
# CODE
#########################################################################################################################
if __name__ == '__main__':
    print('OpenCV 2 version: ',cv2.__version__)
    print('STARTING')
    Test_frame()
    #Camera_test()
    print('FINISHED')
