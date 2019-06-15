#!/usr/bin/env python
# -*- coding: utf-8 -*-



####################################################################################################################
# IMPORTATION
####################################################################################################################
import sys
sys.path.insert(0, './Dependencies_import')

import numpy as np
import matplotlib.pyplot as plt
import pyqtgraph as pg


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

####################################################################################################################
# CODE
####################################################################################################################
if __name__ == '__main__':
    print('STARTING')
    print('FINISHED')
