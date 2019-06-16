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
    def __init__(self, name='span_', orientation='horizontal', color='y', clickable=True, alpha=.2, pos_init=0, init_width=40, assigned=False, log=None):
        super().__init__()
        # ---  --- #
        self.name   = name
        self.orient = orientation
        self.color  = pg.mkColor(color)
        self.clickbl= clickable
        self.alpha  = alpha * 255
        self.isAssigned = assigned
        self.log    = log
        # ---  --- #
        if   self.orient=='horizontal':
            self.span = pg.LinearRegionItem(orientation=pg.LinearRegionItem.Horizontal)
        elif self.orient=='vertical':
            self.span = pg.LinearRegionItem(orientation=pg.LinearRegionItem.Vertical)
        # --- label --- #
        self.label       = pg.TextItem(text=self.name[5:])
        self.text_width  = np.abs( self.label.textItem.textWidth() )
        self.text_height = self.text_width/len(self.name) *3 #here we get the width of one character, and suppose that its height is 3 time the width.
        self.span.sigRegionChanged.connect( self.updateTextPos )
        # ---  --- #
        self.color.setAlpha(self.alpha)
        self.span.setBrush( self.color )
        self.span.setMovable(True)
        self.span.setRegion( [pos_init+0 , pos_init+init_width] )
        self.span.setBounds([0,2000])

    def setAssigned(self, bool_):
        self.isAssigned = bool_

    def updateTextPos(self):
        self.label.setPos( 0.  ,   np.mean(self.span.getRegion())+self.text_height*0.2  )
        # --- feed back --- #
        #self.log.addText( 'TEXt POSITION: {}'.format(self.label.pos()) )

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

class PeakPlot(pg.PlotItem):
    def __init__(self, name='peakplot_', clickable=True, span=None, data=[], color='r', len_max=1, log=None):
        super().__init__()
        self.feedback = False
        # ---  --- #
        self.plot = pg.PlotDataItem()
        self.peakdata = None
        self.name = name
        self.data = data
        self.span = span
        self.color= pg.mkColor(color)
        self.lengthmax = len_max
        self.log  = log
        # ---  --- #
        self.addItem( self.plot )
        self.plot.setPen( self.color )
        self.showGrid(y=True)
        # ---  --- #
        if  self.span != None:
            self.span.setAssigned(True)
        else:
            self.span = None

    def setFullData(self, data ):
        self.data = data

    def setLengthMax(self, newlen):
        self.lengthmax = newlen

    def updatePlot(self):
        region = self.span.span.getRegion()
        m , M  = int(np.min(region)), int(np.max(region))
        err_msg  = ''
        if type(self.data) != type(None) and m != M:
            if len(self.data) >= m or len(self.data) >= M:
                if len(self.data[m:M]) != 0:
                    try:
                        self.addDataElement( np.max(self.data[m:M]) )
                    except:
                        err_msg += 'Error: in updatePlot for object PeakPlot: '+self.name
                        err_msg += '\nIssue with: self.addDataElement( np.max(self.data[m:M]) ),'
                        err_msg += '\nsample: {}'.format(self.data[m:M])
                else:
                    err_msg += 'Plot {0}, span sampled size: {1}\ndata before sampling: {2}'.format(self.name, len(self.data[m:M]), self.data)
            else:
                err_msg += 'Plot {0}, datat len: {1}, min-max: {2}-{3}'.format(self.name, len(self.data), m,M)
        else:
            err_msg += 'Plot {0}, datat type: {1}'.format(self.name, type(self.data))
        if self.feedback:
            self.log.addText( err_msg )
        return None

    def addDataElement(self, y):
        if type(self.peakdata) == type(None):
            self.peakdata = [y]
        else:
            self.peakdata.append(y)
        if len(self.peakdata) > self.lengthmax:
            for i in range(len(self.peakdata) - self.lengthmax):
                if len(self.peakdata) !=0:
                    self.peakdata.pop(0)
                else:
                    self.log.addText('Error in pop, the peakdata seem to be shorter than expected.')
        # ---  -- #
        try:
            data = np.array(self.peakdata)
            data = data/np.max(data)
            self.plot.setData( data )
        except:
            err_msg  = 'Issues with data, data: {}'.format(data)
            self.log.addText( err_msg )

################################################################################################
# CODE
################################################################################################
if __name__=='__main__':
    print('STARTING')
    objct = GaussianFit()
    print(objct.param)
    objct.fitAlltogether()
    print('FINNISHED')
