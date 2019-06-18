#!/usr/bin/env python
# -*- coding: utf-8 -*-



####################################################################################################################
# IMPORTATION
####################################################################################################################
import sys

import numpy as np
import matplotlib.pyplot as plt
import pyqtgraph as pg

from pyueye import ueye


####################################################################################################################
# FUNCTIONS
####################################################################################################################

def generatePgColormap(cm_name):
    pltMap = plt.get_cmap(cm_name)
    colors = pltMap.colors
    colors = [c + [1.] for c in colors]
    positions = np.linspace(0, 1, len(colors))
    #print(positions, colors)
    pgMap = pg.ColorMap(positions, colors)
    return pgMap

def get_bits_per_pixel(color_mode):
    """
    returns the number of bits per pixel for the given color mode
    raises exception if color mode is not is not in dict
    """
    return {
            ueye.IS_CM_SENSOR_RAW8: 8,
            ueye.IS_CM_SENSOR_RAW10: 16,
            ueye.IS_CM_SENSOR_RAW12: 16,
            ueye.IS_CM_SENSOR_RAW16: 16,
            ueye.IS_CM_MONO8: 8,
            ueye.IS_CM_RGB8_PACKED: 24,
            ueye.IS_CM_BGR8_PACKED: 24,
            ueye.IS_CM_RGBA8_PACKED: 32,
            ueye.IS_CM_BGRA8_PACKED: 32,
            ueye.IS_CM_BGR10_PACKED: 32,
            ueye.IS_CM_RGB10_PACKED: 32,
            ueye.IS_CM_BGRA12_UNPACKED: 64,
            ueye.IS_CM_BGR12_UNPACKED: 48,
            ueye.IS_CM_BGRY8_PACKED: 32,
            ueye.IS_CM_BGR565_PACKED: 16,
            ueye.IS_CM_BGR5_PACKED: 16,
            ueye.IS_CM_UYVY_PACKED: 16,
            ueye.IS_CM_UYVY_MONO_PACKED: 16,
            ueye.IS_CM_UYVY_BAYER_PACKED: 16,
            ueye.IS_CM_CBYCRY_PACKED: 16,
    } [color_mode]

def rgb2gray(rgb):
    r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray

####################################################################################################################
# CODE
####################################################################################################################
if __name__ == '__main__':
    print('STARTING')
    print('FINISHED')
