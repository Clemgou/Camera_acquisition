#!/usr/bin/env python
# -*- coding: utf-8 -*-



#########################################################################################################################
# IMPORTATION
#########################################################################################################################
import numpy as np
import cv2
import pyueye as pe
from   pyueye import ueye


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

    def __str__(self):
        return None

    def acquire_movie(self, num_frames):
        '''
        Return the list of frame array that consitutes the movie.
        '''
        movie = []
        for _ in range(num_frames):
            movie.append(self.get_frame())
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

#########################################################################################################################
# CODE
#########################################################################################################################

if __name__ == '__main__':
    print('STARTING')
    camera = Camera(default=False)
    print('IS CAMERA ON: ', camera.isCameraInit )
    camera.set_colormode()
    camera.set_aoi(0,0, 1280, 1024)
    #camera.set_aoi(0,0,  600, 600)
    print('Alloc')
    camera.alloc()
    print('Capture video')
    print(camera.capture_video())
    #frame = camera.get_frame()
    #print(type(frame))
    p = 0
    while True:
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
