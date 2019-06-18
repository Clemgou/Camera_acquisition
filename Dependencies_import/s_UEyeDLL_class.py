
class UEyeError(Exception):
    def __init__(self, errno, strerror, *args, **kwargs):
        super(UEyeError, self).__init__(errno, strerror, *args, **kwargs)
        self.args = (errno, strerror)
        self.errno = errno
        self.strerror = strerror

    def __str__(self):
return self.args[1]


class UEyeDLL(CDLL):
    """
    Subclass of CDLL specific to 'uEye' library, which handles error codes for
    all the functions automatically.
    """

    def __init__(self):
        # TODO: also support loading the Windows DLL on Windows
        try:
            # Global so that its sub-libraries can access it
            CDLL.__init__(self, "libueye_api.so.1", RTLD_GLOBAL)
        except OSError:
            logging.error("Check that IDS SDK is correctly installed")
            raise

    def at_errcheck(self, result, func, args):
        """
        Analyse the return value of a call and raise an exception in case of
        error.
        Follows the ctypes.errcheck callback convention
        """
        # everything returns 0 on correct usage, and < 0 on error
        if result != 0:
            fn = func.__name__
            if fn in self._no_check_get:
                arg1 = args[1]
                if isinstance(arg1, ctypes._SimpleCData):
                    arg1 = arg1.value
                if arg1 in self._no_check_get[fn]:
                    # Was in a GET mode => the result value is not an error
                    return result

            # Note: is_GetError() return the specific error state for a given camera
            if result in UEyeDLL.err_code:
                raise UEyeError(result, "Call to %s failed with error %s (%d)" %
                                (fn, UEyeDLL.err_code[result], result))
            else:
                raise UEyeError(result, "Call to %s failed with error %d" %
                                (fn, result))
        return result

    def __getitem__(self, name):
        func = super(UEyeDLL, self).__getitem__(name)
        if name in self._no_check_func:
            return func

        func.__name__ = name
        func.errcheck = self.at_errcheck
        return func

    # Functions which don't return normal error code
    _no_check_func = ("is_GetDLLVersion",)

    # Some function (mainly Set*()) have some mode which means GET*, where the
    # return value is not an error code (but the value to read).
    # Function name -> list of values in second arg which can return any value
    _no_check_get = {"is_CaptureVideo": (GET_LIVE,),
                     "is_SetColorMode": (GET_COLOR_MODE,),
                    }

    err_code = {
         -1: "NO_SUCCESS",
          # 0: "SUCCESS",
          1: "INVALID_HANDLE",
          2: "IO_REQUEST_FAILED",
          3: "CANT_OPEN_DEVICE",
          4: "CANT_CLOSE_DEVICE",
          5: "CANT_SETUP_MEMORY",
          6: "NO_HWND_FOR_ERROR_REPORT",
          7: "ERROR_MESSAGE_NOT_CREATED",
          8: "ERROR_STRING_NOT_FOUND",
          9: "HOOK_NOT_CREATED",
         10: "TIMER_NOT_CREATED",
         11: "CANT_OPEN_REGISTRY",
         12: "CANT_READ_REGISTRY",
         13: "CANT_VALIDATE_BOARD",
         14: "CANT_GIVE_BOARD_ACCESS",
         15: "NO_IMAGE_MEM_ALLOCATED",
         16: "CANT_CLEANUP_MEMORY",
         17: "CANT_COMMUNICATE_WITH_DRIVER",
         18: "FUNCTION_NOT_SUPPORTED_YET",
         19: "OPERATING_SYSTEM_NOT_SUPPORTED",
         20: "INVALID_VIDEO_IN",
         21: "INVALID_IMG_SIZE",
         22: "INVALID_ADDRESS",
         23: "INVALID_VIDEO_MODE",
         24: "INVALID_AGC_MODE",
         25: "INVALID_GAMMA_MODE",
         26: "INVALID_SYNC_LEVEL",
         27: "INVALID_CBARS_MODE",
         28: "INVALID_COLOR_MODE",
         29: "INVALID_SCALE_FACTOR",
         30: "INVALID_IMAGE_SIZE",
         31: "INVALID_IMAGE_POS",
         32: "INVALID_CAPTURE_MODE",
         33: "INVALID_RISC_PROGRAM",
         34: "INVALID_BRIGHTNESS",
         35: "INVALID_CONTRAST",
         36: "INVALID_SATURATION_U",
         37: "INVALID_SATURATION_V",
         38: "INVALID_HUE",
         39: "INVALID_HOR_FILTER_STEP",
         40: "INVALID_VERT_FILTER_STEP",
         41: "INVALID_EEPROM_READ_ADDRESS",
         42: "INVALID_EEPROM_WRITE_ADDRESS",
         43: "INVALID_EEPROM_READ_LENGTH",
         44: "INVALID_EEPROM_WRITE_LENGTH",
         45: "INVALID_BOARD_INFO_POINTER",
         46: "INVALID_DISPLAY_MODE",
         47: "INVALID_ERR_REP_MODE",
         48: "INVALID_BITS_PIXEL",
         49: "INVALID_MEMORY_POINTER",
         50: "FILE_WRITE_OPEN_ERROR",
         51: "FILE_READ_OPEN_ERROR",
         52: "FILE_READ_INVALID_BMP_ID",
         53: "FILE_READ_INVALID_BMP_SIZE",
         54: "FILE_READ_INVALID_BIT_COUNT",
         55: "WRONG_KERNEL_VERSION",
         60: "RISC_INVALID_XLENGTH",
         61: "RISC_INVALID_YLENGTH",
         62: "RISC_EXCEED_IMG_SIZE",
         70: "DD_MAIN_FAILED",
         71: "DD_PRIMSURFACE_FAILED",
         72: "DD_SCRN_SIZE_NOT_SUPPORTED",
         73: "DD_CLIPPER_FAILED",
         74: "DD_CLIPPER_HWND_FAILED",
         75: "DD_CLIPPER_CONNECT_FAILED",
         76: "DD_BACKSURFACE_FAILED",
         77: "DD_BACKSURFACE_IN_SYSMEM",
         78: "DD_MDL_MALLOC_ERR",
         79: "DD_MDL_SIZE_ERR",
         80: "DD_CLIP_NO_CHANGE",
         81: "DD_PRIMMEM_NULL",
         82: "DD_BACKMEM_NULL",
         83: "DD_BACKOVLMEM_NULL",
         84: "DD_OVERLAYSURFACE_FAILED",
         85: "DD_OVERLAYSURFACE_IN_SYSMEM",
         86: "DD_OVERLAY_NOT_ALLOWED",
         87: "DD_OVERLAY_COLKEY_ERR",
         88: "DD_OVERLAY_NOT_ENABLED",
         89: "DD_GET_DC_ERROR",
         90: "DD_DDRAW_DLL_NOT_LOADED",
         91: "DD_THREAD_NOT_CREATED",
         92: "DD_CANT_GET_CAPS",
         93: "DD_NO_OVERLAYSURFACE",
         94: "DD_NO_OVERLAYSTRETCH",
         95: "DD_CANT_CREATE_OVERLAYSURFACE",
         96: "DD_CANT_UPDATE_OVERLAYSURFACE",
         97: "DD_INVALID_STRETCH",
        100: "EV_INVALID_EVENT_NUMBER",
        101: "INVALID_MODE",
        # 102: "CANT_FIND_FALCHOOK",
        102: "CANT_FIND_HOOK",
        103: "CANT_GET_HOOK_PROC_ADDR",
        104: "CANT_CHAIN_HOOK_PROC",
        105: "CANT_SETUP_WND_PROC",
        106: "HWND_NULL",
        107: "INVALID_UPDATE_MODE",
        108: "NO_ACTIVE_IMG_MEM",
        109: "CANT_INIT_EVENT",
        110: "FUNC_NOT_AVAIL_IN_OS",
        111: "CAMERA_NOT_CONNECTED",
        112: "SEQUENCE_LIST_EMPTY",
        113: "CANT_ADD_TO_SEQUENCE",
        114: "LOW_OF_SEQUENCE_RISC_MEM",
        115: "IMGMEM2FREE_USED_IN_SEQ",
        116: "IMGMEM_NOT_IN_SEQUENCE_LIST",
        117: "SEQUENCE_BUF_ALREADY_LOCKED",
        118: "INVALID_DEVICE_ID",
        119: "INVALID_BOARD_ID",
        120: "ALL_DEVICES_BUSY",
        121: "HOOK_BUSY",
        122: "TIMED_OUT",
        123: "NULL_POINTER",
        124: "WRONG_HOOK_VERSION",
        125: "INVALID_PARAMETER",
        126: "NOT_ALLOWED",
        127: "OUT_OF_MEMORY",
        128: "INVALID_WHILE_LIVE",
        129: "ACCESS_VIOLATION",
        130: "UNKNOWN_ROP_EFFECT",
        131: "INVALID_RENDER_MODE",
        132: "INVALID_THREAD_CONTEXT",
        133: "NO_HARDWARE_INSTALLED",
        134: "INVALID_WATCHDOG_TIME",
        135: "INVALID_WATCHDOG_MODE",
        136: "INVALID_PASSTHROUGH_IN",
        137: "ERROR_SETTING_PASSTHROUGH_IN",
        138: "FAILURE_ON_SETTING_WATCHDOG",
        139: "NO_USB20",
        140: "CAPTURE_RUNNING",
        141: "MEMORY_BOARD_ACTIVATED",
        142: "MEMORY_BOARD_DEACTIVATED",
        143: "NO_MEMORY_BOARD_CONNECTED",
        144: "TOO_LESS_MEMORY",
        145: "IMAGE_NOT_PRESENT",
        146: "MEMORY_MODE_RUNNING",
        147: "MEMORYBOARD_DISABLED",
        148: "TRIGGER_ACTIVATED",
        150: "WRONG_KEY",
        151: "CRC_ERROR",
        152: "NOT_YET_RELEASED",
        153: "NOT_CALIBRATED",
        154: "WAITING_FOR_KERNEL",
        155: "NOT_SUPPORTED",
        156: "TRIGGER_NOT_ACTIVATED",
        157: "OPERATION_ABORTED",
        158: "BAD_STRUCTURE_SIZE",
        159: "INVALID_BUFFER_SIZE",
        160: "INVALID_PIXEL_CLOCK",
        161: "INVALID_EXPOSURE_TIME",
        162: "AUTO_EXPOSURE_RUNNING",
        163: "CANNOT_CREATE_BB_SURF",
        164: "CANNOT_CREATE_BB_MIX",
        165: "BB_OVLMEM_NULL",
        166: "CANNOT_CREATE_BB_OVL",
        167: "NOT_SUPP_IN_OVL_SURF_MODE",
        168: "INVALID_SURFACE",
        169: "SURFACE_LOST",
        170: "RELEASE_BB_OVL_DC",
        171: "BB_TIMER_NOT_CREATED",
        172: "BB_OVL_NOT_EN",
        173: "ONLY_IN_BB_MODE",
        174: "INVALID_COLOR_FORMAT",
        175: "INVALID_WB_BINNING_MODE",
        176: "INVALID_I2C_DEVICE_ADDRESS",
        177: "COULD_NOT_CONVERT",
        178: "TRANSFER_ERROR",
        179: "PARAMETER_SET_NOT_PRESENT",
        180: "INVALID_CAMERA_TYPE",
        181: "INVALID_HOST_IP_HIBYTE",
        182: "CM_NOT_SUPP_IN_CURR_DISPLAYMODE",
        183: "NO_IR_FILTER",
        184: "STARTER_FW_UPLOAD_NEEDED",
        185: "DR_LIBRARY_NOT_FOUND",
        186: "DR_DEVICE_OUT_OF_MEMORY",
        187: "DR_CANNOT_CREATE_SURFACE",
        188: "DR_CANNOT_CREATE_VERTEX_BUFFER",
        189: "DR_CANNOT_CREATE_TEXTURE",
        190: "DR_CANNOT_LOCK_OVERLAY_SURFACE",
        191: "DR_CANNOT_UNLOCK_OVERLAY_SURFACE",
        192: "DR_CANNOT_GET_OVERLAY_DC",
        193: "DR_CANNOT_RELEASE_OVERLAY_DC",
        194: "DR_DEVICE_CAPS_INSUFFICIENT",
        195: "INCOMPATIBLE_SETTING",
        196: "DR_NOT_ALLOWED_WHILE_DC_IS_ACTIVE",
        197: "DEVICE_ALREADY_PAIRED",
        198: "SUBNETMASK_MISMATCH",
        199: "SUBNET_MISMATCH",
        200: "INVALID_IP_CONFIGURATION",
        201: "DEVICE_NOT_COMPATIBLE",
        202: "NETWORK_FRAME_SIZE_INCOMPATIBLE",
        203: "NETWORK_CONFIGURATION_INVALID",
        204: "ERROR_CPU_IDLE_STATES_CONFIGURATION",
        205: "DEVICE_BUSY",
        206: "SENSOR_INITIALIZATION_FAILED",
        207: "IMAGE_BUFFER_NOT_DWORD_ALIGNED",
        208: "SEQ_BUFFER_IS_LOCKED",
        209: "FILE_PATH_DOES_NOT_EXIST",
        210: "INVALID_WINDOW_HANDLE",
}
