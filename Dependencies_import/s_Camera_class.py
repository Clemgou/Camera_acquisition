#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Compilation of different works.

Many of the method in the Camera class are adaptation of the work of Éric Piel, found at:
	https://github.com/delmic/odemis/blob/master/src/odemis/driver/ueye.py
'''

#########################################################################################################################
# IMPORTATION
#########################################################################################################################
import sys
import numpy  as np
import cv2
import pyueye as pe
from   pyueye    import ueye
import ctypes

import faulthandler
#faulthandler.enable()


from s_Miscellaneous_functions        import get_bits_per_pixel


import time
#########################################################################################################################
# FUNCTIONS
#########################################################################################################################

class Camera:
    # ~~~~~~~~~~~~~~~~~~~~~~~~ #
    class ImageBuffer:
        def __init__(self):
            self.mem_ptr = ueye.c_mem_p()
            self.mem_id  = ueye.int()
    # ~~~~~~~~~~~~~~~~~~~~~~~~ #
    class Rect:
        def __init__(self, x=0, y=0, width=0, height=0):
            self.x = x
            self.y = y
            self.width = width
            self.height = height
    # ~~~~~~~~~~~~~~~~~~~~~~~~ #
    class uEyeException(Exception):
        def __init__(self, error_code):
            self.error_code = error_code
        def __str__(self):
            return "Err: " + str(self.error_code)
    # ~~~~~~~~~~~~~~~~~~~~~~~~ #
    def __init__(self, cam_id=0, log=None, fps=10., default=True):
        self.cam_id  = cam_id
        self.log     = log
        self.cam     = None
        self.fps     = fps
        self.colorMode = ueye.IS_CM_BGR8_PACKED
        # ---  --- #
        self.initialize()
        # ---  --- #
        if default and self.isCameraInit:
            self.initDefault()

    def initialize(self):
        # --- using pyueye --- #
        self.cam          = ueye.HIDS(self.cam_id)
        self.frame_buffer = []
        # ---  --- #
        ret = ueye.is_InitCamera(self.cam, None) # init camera and return 0,1 according to if it worked
        if ret != ueye.IS_SUCCESS:
                self.cam = None
                self.addToLog('Camera initation: failed.')
                self.isCameraInit = False
                self.close_camera()
                return None
        self.isCameraInit = True

    def initDefault(self):
        return None

    def close_camera(self):
        ret = None
        if self.cam is not None:
                ret = ueye.is_ExitCamera(self.cam)
        if ret == ueye.IS_SUCCESS:
                self.cam = None
                self.isCameraInit = False

    def __info__(self):
        cam_info     =ueye.CAMINFO()
        ueye.is_GetCameraInfo(self.cam, cam_info)
        # ---  --- #
        info_display  = ''
        info_display +=   'Serial No: {}'.format(cam_info.SerNo)
        info_display += '\nID       : {}'.format(cam_info.ID)
        info_display += '\nVersion  : {}'.format(cam_info.Version)
        info_display += '\nDate     : {}'.format(cam_info.Date)
        info_display += '\nSelect   : {}'.format(cam_info.Select)
        info_display += '\nType     : {}'.format(cam_info.Type)
        info_display += '\nReserved : {}'.format(cam_info.Reserved)
        return info_display

    def acquire_movie(self, num_frames):
        '''
        Return the list of frame array that consitutes the movie.
        '''
        self.capture_video()
        time.sleep(1.)
        # ---  --- #
        movie = []
        for _ in range(num_frames):
            movie.append(self.get_frame())
        # ---  --- #
        self.stop_video()
        time.sleep(1.)
        return movie

    def addToLog(self, txt):
        if self.log != None:
            self.log.addText(txt)
        else:
            print(txt)

    def check(self, state, funct_name):
        if state != ueye.IS_SUCCESS:
            self.addToLog( 'Error: in {0}.\nThe state is not ueye.IS_SUCCESS, instead it is: {1}'.format(funct_name, state))
            raise self.uEyeException(state)

    def get_aoi(self):
        rect_aoi = ueye.IS_RECT()
        ueye.is_AOI(self.cam, ueye.IS_AOI_IMAGE_GET_AOI, rect_aoi, ueye.sizeof(rect_aoi))
        # ---  --- #
        x, y, width, height = rect_aoi.s32X.value, rect_aoi.s32Y.value, rect_aoi.s32Width.value, rect_aoi.s32Height.value
        return x, y, width, height

    def set_aoi(self, x, y, width, height):
        rect_aoi           = ueye.IS_RECT()
        rect_aoi.s32X      = ueye.int(x)
        rect_aoi.s32Y      = ueye.int(y)
        rect_aoi.s32Width  = ueye.int(width)
        rect_aoi.s32Height = ueye.int(height)
        # ---  --- #
        hasWorked = ueye.is_AOI(self.cam, ueye.IS_AOI_IMAGE_SET_AOI, rect_aoi, ueye.sizeof(rect_aoi))  # set and return the success of AOI change
        #print('SET AOI: ', hasWorked )
        return hasWorked

    def alloc(self, buffer_count=3):
        '''
        Initialization of the ring buffer.
        '''
        rec_aoi    = self.Rect( *self.get_aoi() )
        color_mode = ueye.is_SetColorMode(self.cam, ueye.IS_GET_COLOR_MODE)
        self.bpp   = get_bits_per_pixel( color_mode )
        # --- freeing the memory from previous buffer --- #
        for buff in self.frame_buffer:
            hasWorked = ueye.is_FreeImageMem(self.cam, buff.mem_ptr, buff.mem_id)
            self.check( hasWorked, 'is_FreeImageMem')
        # --- allocate memory to buffer --- #
        for i in range(buffer_count):
                buff = self.ImageBuffer()
                ueye.is_AllocImageMem(  self.cam,
                                        rec_aoi.width, rec_aoi.height, self.bpp,
                                        buff.mem_ptr, buff.mem_id)
                hasWorked = ueye.is_AddToSequence(self.cam, buff.mem_ptr, buff.mem_id)
                self.check( hasWorked, 'is_AddToSequence')
                self.frame_buffer.append(buff)
        # ---  --- #
        hasWorked = ueye.is_InitImageQueue(self.cam, 0) # init and return the success of image queued.
        self.check( hasWorked , 'is_InitImageQueue')
        # ---  --- #
        self.img_buffer = self.frame_buffer[-1]

    def waitForNextFrame(self):
        self.timeout    = 1000
        self.img_buffer = self.ImageBuffer()#self.frame_buffer[-1]
        isWaiting       = ueye.is_WaitForNextImage(self.cam, self.timeout, self.img_buffer.mem_ptr, self.img_buffer.mem_id)
        print('WAIT FOR NEXT IMG: {0}, IS_SUCCESS: {1}'.format(isWaiting, ueye.IS_SUCCESS) )
        if isWaiting == ueye.IS_SUCCESS:
            return True
        else:
            return False

    def lockBuffer(self):
        hasWorked = ueye.is_LockSeqBuf(self.cam, self.img_buffer.mem_id, self.img_buffer.mem_ptr)
        self.check( hasWorked, 'is_LockSeqBuf')

    def unlockBuffer(self):
        hasWorked = ueye.is_UnlockSeqBuf(self.cam, self.img_buffer.mem_id, self.img_buffer.mem_ptr)
        self.check( hasWorked, 'is_UnlockSeqBuf')

    def getImageData(self):
        # --- set AOI --- #
        rect_aoi = ueye.IS_RECT()
        hasWorked= ueye.is_AOI(self.cam, ueye.IS_AOI_IMAGE_GET_AOI, rect_aoi, ueye.sizeof(rect_aoi))
        self.check( hasWorked, 'getImageData')
        # ---  --- #
        x        = ueye.int()
        y        = ueye.int()
        bits     = ueye.int()
        pitch    = ueye.int()
        self.frame_width  = rect_aoi.s32Width.value
        self.frame_height = rect_aoi.s32Height.value
        hasWorked= ueye.is_InquireImageMem(self.cam, self.img_buffer.mem_ptr, self.img_buffer.mem_id, x, y, bits, pitch)
        self.check( hasWorked, 'getImageData')
        self.imgdata = ueye.get_data(self.img_buffer.mem_ptr, self.frame_width, self.frame_height, bits, pitch, True)

    def get_frame(self):
        #self.lockBuffer() # seems to be unecessary
        # ---  --- #
        self.getImageData()
        # --- convert 1D array to 2D wrt the data style (ie color or not) --- #
        self.frame = self.from_1d_to_2d_image(self.imgdata) # reshape the image data as 1dimensional array
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY) # make a gray image
        # ---  --- #
        self.unlockBuffer()
        return self.frame

    def capture_video(self, wait=False):
        wait_param = ueye.IS_WAIT if wait else ueye.IS_DONT_WAIT
        return ueye.is_CaptureVideo(self.cam, wait_param)

    def stop_video(self):
        return ueye.is_StopLiveVideo(self.cam, ueye.IS_FORCE_VIDEO_STOP)

    def freeze_video(self, wait=False):
        wait_param = ueye.IS_WAIT if wait else ueye.IS_DONT_WAIT
        return ueye.is_FreezeVideo(self.cam, wait_param)

    def from_1d_to_2d_image(self, img_data):
        channels = int((7 + self.bpp) / 8) # with self.bpp from alloc with get_bits_per_pixel( color_mode )
        if channels > 1:
            return np.reshape(img_data, (self.frame_height, self.frame_width, channels))
        else:
            return np.reshape(img_data, (self.frame_height, self.frame_width))

    def set_colormode(self):
        self.check(ueye.is_SetColorMode(self.cam, self.colorMode), 'is_SetColorMode' )

    def get_colormode(self):
        ret = ueye.is_SetColorMode(self.cam, ueye.IS_GET_COLOR_MODE)
        return ret

    def change_colormode(self, colormode):
        self.colorMode = colormode
        self.set_colormode()

    def getExposure(self):
        '''
        Exposure time in ms.
        '''
        val_formated = ctypes.c_double(0)
        val_size     = ctypes.c_int32( ctypes.sizeof(val_formated) )
        hasWorked = ueye.is_Exposure(self.cam, ueye.IS_EXPOSURE_CMD_GET_EXPOSURE, val_formated, val_size)
        self.check( hasWorked, 'is_Exposure')
        return val_formated.value
        #self.addToLog('is_Exposure has worked: {0}\n Value of exposure is: {1}, of size {2}.\nWanted value is: {3}'.format(hasWorked, val_formated, val_size, exp_val))

    def setExposure(self, exp_val):
        '''
        Exposure time in ms.
        '''
        val_formated = ctypes.c_double( float(exp_val) )
        val_size     = ctypes.c_int32( ctypes.sizeof(val_formated) )
        hasWorked = ueye.is_Exposure(self.cam, ueye.IS_EXPOSURE_CMD_SET_EXPOSURE, val_formated, val_size)
        self.check( hasWorked, 'is_Exposure')
        #self.addToLog('is_Exposure has worked: {0}\n Value of exposure is: {1}, of size {2}.\nWanted value is: {3}'.format(hasWorked, val_formated, val_size, exp_val))

    def setHarwareGain(self, gain_val):
        current_gain = ueye.is_SetHardwareGain(self.cam, ueye.IS_GET_MASTER_GAIN, ueye.IS_IGNORE_PARAMETER, ueye.IS_IGNORE_PARAMETER, ueye.IS_IGNORE_PARAMETER)
        hasWorked    = ueye.is_SetHardwareGain(self.cam, int(gain_val), ueye.IS_IGNORE_PARAMETER, ueye.IS_IGNORE_PARAMETER, ueye.IS_IGNORE_PARAMETER)
        self.check( hasWorked, 'is_SetHardwareGain')

    def getFrameTimeRange(self):
        """
        Note: depends on the pixel clock settings
        return (2 floats): min/max duration between each frame in s
        """
        ftmn = ctypes.c_double()  # in s
        ftmx = ctypes.c_double()
        ftic = ctypes.c_double()
        hasWorked = ueye.is_GetFrameTimeRange(self.cam, ftmn, ftmx, ftic)
        self.check( hasWorked, 'getFrameTimeRange')
        return ftmn.value, ftmx.value, ftic.value

    def getFrameRate(self):
        fps = ctypes.c_double()
        hasWorked = ueye.is_SetFrameRate(self.cam, ueye.IS_GET_FRAMERATE, fps)
        self.check( hasWorked, 'getFrameRate')
        return fps.value

    def setFrameRate(self, fr):
        """
        Note: values out of range are automatically clipped
        fr (0>float): framerate (in Hz) to be set
        return (0>float): actual framerate applied
        """
        newfps = ctypes.c_double()
        hasWorked = ueye.is_SetFrameRate(self.cam, ctypes.c_double(fr), newfps)
        self.check( hasWorked, 'setFrameRate')
        return newfps.value

    def getPixelClock(self):
        """
        return (0<int): the pixel clock in MHz
        """
        pc = ctypes.c_uint32()
        hasWorked = ueye.is_PixelClock(self.cam, ueye.IS_PIXELCLOCK_CMD_GET, pc, ctypes.sizeof(pc))
        self.check( hasWorked, 'getPixelClock' )
        return pc.value

    def setPixelClock(self, pxl_clck):
        val_formated = ctypes.c_uint32(pxl_clck)
        hasWorked = ueye.is_PixelClock(self.cam, ueye.IS_PIXELCLOCK_CMD_SET, val_formated, ctypes.sizeof(val_formated))
        self.check( hasWorked, 'setPixelClock' )

#########################################################################################################################
# CODE
#########################################################################################################################

if __name__ == '__main__':
    print('STARTING')
    camera = Camera(default=False)
    print('IS CAMERA ON: ', camera.isCameraInit )
    print('Camera info')
    print(camera.__info__())
    print('Set color mode and frame size')
    camera.set_colormode()
    camera.set_aoi(0,0, 1280, 1024)
    print('Alloc')
    camera.alloc()
    print('Capture video')
    print(camera.capture_video())
    frame = camera.get_frame()
    print(type(frame))
    print('Set Exposure')
    camera.setExposure(12.5)
    print(camera.getExposure())
    print('Set Gain')
    camera.setHarwareGain(0.)
    print('Frame time range: ', camera.getFrameTimeRange() )
    print('Set Frame rate')
    print('frame rate we set: ', camera.setFrameRate(5) )
    print('frame rate we get: ', camera.getFrameRate() )
    print('Set pixel clock')
    camera.setPixelClock(22)
    print('Pixel Clock: ', camera.getPixelClock() )
    print('Continuous view')
    p = 0
    while False:
        time.sleep(1/10)
        if True:#camera.nextFrame():
            frame = camera.get_frame()
            print('max val frame: ',np.max(frame))
        cv2.imshow('frame',frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        print('p = ',p)
        p += 1
    #print(frame.shape)
    #frame = frame.reshape([camera.frame_width, camera.frame_height])
    print('Stop video')
    camera.stop_video()
    print('Close camera')
    camera.close_camera()
    print('FINISHED')
