#! usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################################
# IMPORTATION
################################################################################################

import numpy     as np
import pyqtgraph as pg
import scipy
from scipy.optimize import curve_fit

################################################################################################
# FUNCTIONS
################################################################################################

from PyQt5.QtGui import QFrame

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class QVLine(QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

class GaussianFit():
    def __init__(self, xdata=[], ydata=[], N=1, x0=[], a=[], b=[], mode='all', peakthreshold=1., max_=1., log=None, span_dic={}):
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
        self.dic_span  = span_dic
        self.maximums  = []
        # ---  --- #
        self.xdata = xdata
        self.ydata = ydata
        # ---  --- #
        self.makeParam()

    def gaussian(self, x, x0,a,b):
        return a*np.exp(-b*(x-x0)**2)

    def jac_gaussian(self, x ,x0,a,b):
        jac = np.zeros([len(x), 3])
        jac[:,0] = +2*(x-x0)*a*b*np.exp(-b*(x-x0)**2)
        jac[:,1] = np.exp(-b*(x-x0)**2)
        jac[:,2] = -a*(x-x0)**2*np.exp(-b*(x-x0)**2)
        return jac

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

    def jac_sumGaussian(self, x, *param):
        n   = int(len(param)/3)
        jac = np.zeros([len(x), 3*n])
        for i in range(n):
            jac[:,3*i:3*i+3] = self.jac_gaussian(x, *param[3*i:3*(i+1)])
        return jac

    def fitAlltogether(self):
        param_guess   = self.param.reshape([self.param.shape[0]*3])
        try:
            popt, pcov = curve_fit(self.sumGaussian, self.xdata, self.ydata, p0=param_guess, jac=self.jac_sumGaussian)
            self.param = popt.reshape([self.fit_nbr,3])
        except:
            err_msg = 'Error: in fitAlltogether. Something is wrong with curve_fit implementation.\nparam_guess: {}'.format(param_guess)
            self.log.addText(err_msg)

    def fitPeakByPeak(self):
        KEYS = list( self.dic_span.keys() )
        N    = len(KEYS)
        self.param    = np.zeros([N,3])
        self.maximums = np.ones(N)
        for i in range(N):
            region = self.dic_span[KEYS[i]].span.getRegion()
            m , M  = int(np.min(region)), int(np.max(region))
            x0,a,b = np.mean( self.xdata[m:M] ), np.max(self.ydata[m:M]) , 1.#np.abs(M-m)/2.
            self.maximums[i] = a
            try:
                popt, pcov = curve_fit(self.gaussian, self.xdata[m:M], self.ydata[m:M], p0=[x0, a, b], method='lm', jac=self.jac_gaussian)
                self.param[i] = popt
            except:
               err_msg = 'Error: in fitPeakByPeak. Something is wrong with curve_fit implementation.\nparam_guess: {}'.format(self.param)
               self.log.addText(err_msg)

    def fitMethod(self):
        if   self.mode == 'all':
            self.makeParam()
            self.fitAlltogether()
            # --- verification everything went normally --- #
            if self.param.shape[0] != self.fit_nbr:
                err_msg = 'Error: in fitMethod, the number of fitting parameter do not match the number of peaks.'
                self.log.addText(err_msg)
                return None
        elif self.mode == 'pbp':
            self.fitPeakByPeak()
            # --- verification everything went normally --- #
            if self.param.shape[0] != len( list(self.dic_span.keys()) ):
                err_msg = 'Error: in fitMethod, the number of fitting parameter do not match the number of peaks.'
                self.log.addText(err_msg)
                return None

    def makeGaussianFit(self):
        if self.fit_nbr == 0 and self.mode == 'all':
            return None
        # ---  --- #
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

    def setSpanDictionary(self, span_dic):
        self.dic_span = span_dic

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
        if   self.orient=='horizontal':
            self.label.setPos( 0.  ,   np.mean(self.span.getRegion())+self.text_height*0.2  )
        elif self.orient=='vertical':
            self.label.setPos( np.mean(self.span.getRegion())-np.abs(self.text_width), 0  )
        # --- feed back --- #
        #self.log.addText( 'TEXt POSITION: {}'.format(self.label.pos()) )

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

class PeakPlot(pg.PlotItem):
    def __init__(self, name='peakplot_', clickable=True, span=None, data=[], color='r', len_max=1, log=None):
        super().__init__()
        self.feedback = True
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
            for i in range( int(len(self.peakdata)-self.lengthmax) ):
                if len(self.peakdata) !=0:
                    self.peakdata.pop(0)
                else:
                    self.log.addText('Error in pop, the peakdata seem to be shorter than expected.')
        # ---  -- #
        try:
            data = np.array(self.peakdata)
            #data = data/np.max(data)
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
