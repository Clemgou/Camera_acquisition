#! usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################################
# IMPORTATION
################################################################################################

import numpy as np
import pyqtgraph as pg
import scipy
from scipy.optimize import curve_fit



################################################################################################
# FUNCTIONS
################################################################################################

class GaussianFit():
    def __init__(self, xdata=[], ydata=[], N=1, x0=[], a=[], b=[], mode='all', peakthreshold=1., max_=1., log=None):
        '''
        Parameters:
            - N: number of gaussian to fit
            - x0: list of estimated peak centers
            - mode: gives the type of method to use: 'all' we optimize the supperposition of all the fit, 'pbp' (peak by peak) we optimize each fit individually.
        '''
        self.log       = log
        self.fit_nbr   = N
        self.x0        = x0
        self.a         = a
        self.b         = b
        self.dic_gauss = {}
        self.mode      = mode
        self.max       = max_
        self.threshold = peakthreshold
        # ---  --- #
        self.xdata = xdata
        self.ydata = ydata
        # ---  --- #
        self.makeParam()

    def gaussian(self, x, x0,a,b):
        return a*np.exp(-b*(x-x0)**2)

    def makeParam(self):
        self.param = np.ones([self.fit_nbr, 3])
        if len(self.x0)==self.fit_nbr:
            for i in range(self.fit_nbr):
                self.param[i,0] = self.x0[i]
        if len(self.a)==self.fit_nbr:
            for i in range(self.fit_nbr):
                self.param[i,1] = self.a[i]
        if len(self.b)==self.fit_nbr:
            for i in range(self.fit_nbr):
                self.param[i,2] = self.b[i]
        # --- bounds --- #
        self.bounds = ((0,2000),(0,self.max),(1e-3,1e2))*self.fit_nbr

    def sumGaussian(self, x, *param):
        n = self.fit_nbr
        #self.log.addText('Param in sumGaussian:'+str(param)+'\nsize param: '+str(len(param)))
        # --- checking if parameter and peak number are consistent --- #
        if not (n*3 == len(param)):
            self.log.addText('None consistency in sumGaussian, number of peak greater that parameter space.')
            return None
        # ---  --- #
        SUM = self.gaussian(x, *param[0:3])
        for i in range(1,n):
            SUM += self.gaussian(x, *param[3*i:3*(i+1)])
            #self.log.addText('Except in sumGaussian, parameter:'+str(param))
        return SUM

    def fitAlltogether(self):
        param_guess = self.param.reshape([self.param.shape[0]*3])
        try:
            popt, pcov = curve_fit(self.sumGaussian, self.xdata, self.ydata, p0=param_guess)
            self.param = popt.reshape([self.fit_nbr,3])
        except:
            err_msg = 'Error: in fitAlltogether. Something is wrong with curve_fit implementation.\nparam_guess: {}'.format(param_guess)
            self.log.addText(err_msg)

    def fitPeakByPeak(self):
        return None

    def fitMethod(self):
        if   self.mode == 'all':
            self.fitAlltogether()
        elif self.mode == 'pbp':
            self.fitPeakByPeak()
            pass
        # --- verification everything went normally --- #
        if self.param.shape[0] != self.fit_nbr:
            err_msg = 'Error: in fitMethod, the number of fitting parameter do not match the number of peaks.'
            print(err_msg)
            return None

    def makeGaussianFit(self):
        if self.fit_nbr == 0:
            return None
        # ---  --- #
        self.makeParam()
        self.fitMethod()
        # ---  --- #
        self.resetDicGauss()
        for i in range(self.param.shape[0]):
            self.dic_gauss['gauss_{}'.format(i)] = self.param[i]

    def resetDicGauss(self):
        self.dic_gauss = {}

    def setXData(self, xdata):
        self.xdata = xdata

    def setYData(self, ydata):
        self.ydata = ydata

    def setPeakNumber(self, N):
        self.fit_nbr = N

    def setCenters(self, x0):
        self.x0 = x0

    def setAmplitudes(self, a):
        self.a = a

    def setSTD(self, b):
        self.b = b

    def setMode(self, mode):
        self.mode = mode

    def setMaxAmp(self, max_):
        self.max = max_

    def setThreshold(self, thresh):
        self.threshold = thresh

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

class SpanObject(pg.GraphicsWidget):
    def __init__(self, alignement='horizontal', color='y', clickable=True):
        super().__init__()
        # ---  --- #
        self.aligmt = alignement
        self.color  = pg.mkColor(color)
        self.clickbl= clickable
        # ---  --- #
        self.bound1 = pg.InfiniteLine()
        self.bound2 = pg.InfiniteLine()
        self.fill   = pg.FillBetweenItem()
        self.boundarybox = [[0,1],[1,1]]
        self.bound1.setMovable(True)
        self.bound2.setMovable(True)
        # ---  --- #
        if   self.aligmt=='horizontal':
            self.bound1.setAngle(0)
            self.bound2.setAngle(0)
        elif self.aligmt=='vertical':
            self.bound1.setAngle(90)
            self.bound2.setAngle(90)
        # ---  --- #
        self.makeFilling()
        self.viewbox = pg.ViewBox()
        self.viewbox.addItem(self.bound1)
        self.viewbox.addItem(self.bound2)
        #self.viewbox.addItem(self.fill)

    def makeFilling(self):
        line1 = pg.PlotCurveItem()
        line1.setData(x=[0,0] , y=[0,1])
        line2 = pg.PlotCurveItem()
        line2.setData(x=[1,1] , y=[0,1])
        self.fill.setCurves(curve1=line1, curve2=line2)
        self.color.setAlpha(20)
        self.fill.setBrush( self.color )

    def moveSpan(self):
        return None

################################################################################################
# CODE
################################################################################################
if __name__=='__main__':
    print('STARTING')
    objct = GaussianFit()
    print(objct.param)
    objct.fitAlltogether()
    print('FINNISHED')
