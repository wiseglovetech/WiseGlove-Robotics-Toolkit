import ctypes
from ctypes import c_void_p, c_char_p, c_bool, c_int, c_ushort, c_float, POINTER, create_string_buffer

class WGDevice:
    def __init__(self, lib_path="./libwiseglove.so"):
        # 加载动态库
        self.lib = ctypes.CDLL(lib_path)

        # 创建 C++ 对象
        self.lib.pynewglove.restype = c_void_p
        self.obj = self.lib.pynewglove()
        if not self.obj:
            raise RuntimeError("无法创建 Wiseglove 对象")

        # ---- 注册所有函数签名 ----
        self.lib.pydeleteglove.argtypes = [c_void_p]

        self.lib.pyopen.argtypes = [c_void_p, c_char_p]
        self.lib.pyopen.restype = c_bool

        self.lib.pyClose.argtypes = [c_void_p]

        self.lib.pyGetManu.argtypes = [c_void_p, c_char_p]
        self.lib.pyGetManu.restype = c_bool

        self.lib.pyGetModel.argtypes = [c_void_p, c_char_p]
        self.lib.pyGetModel.restype = c_bool

        self.lib.pyGetSn.argtypes = [c_void_p, c_char_p]
        self.lib.pyGetSn.restype = c_bool

        self.lib.pyGetNumOfFinger.argtypes = [c_void_p]
        self.lib.pyGetNumOfFinger.restype = c_int

        self.lib.pyGetNumOfPressure.argtypes = [c_void_p]
        self.lib.pyGetNumOfPressure.restype = c_int

        self.lib.pyGetNumOfArm.argtypes = [c_void_p]
        self.lib.pyGetNumOfArm.restype = c_int

        self.lib.pyGetData.argtypes = [c_void_p, POINTER(c_ushort)]
        self.lib.pyGetData.restype = c_int

        self.lib.pyGetScaledData.argtypes = [c_void_p, POINTER(c_ushort)]
        self.lib.pyGetScaledData.restype = c_int

        self.lib.pyGetAngle.argtypes = [c_void_p, POINTER(c_float)]
        self.lib.pyGetAngle.restype = c_int

        self.lib.pyGetQuat.argtypes = [c_void_p, POINTER(c_float)]
        self.lib.pyGetQuat.restype = c_int

        self.lib.pyGetQuatOrg.argtypes = [c_void_p, POINTER(c_float)]
        self.lib.pyGetQuatOrg.restype = c_int

        self.lib.pyGetPressureRaw.argtypes = [c_void_p, POINTER(c_ushort)]
        self.lib.pyGetPressureRaw.restype = c_int

        self.lib.pySetCalibMode.argtypes = [c_void_p, c_int]
        self.lib.pyResetCalib.argtypes = [c_void_p]
        self.lib.pyResetQuat.argtypes = [c_void_p]
        self.lib.pyZeroPressure.argtypes = [c_void_p]
        self.lib.pySetFeedBack.argtypes = [c_void_p, POINTER(ctypes.c_ubyte)]

    def __del__(self):
        if hasattr(self, "obj") and self.obj:
            self.lib.pydeleteglove(self.obj)
            self.obj = None

    # ----------------- 类方法 -----------------
    def open(self, port: str) -> bool:
        return self.lib.pyopen(self.obj, port.encode('utf-8'))

    def close(self):
        self.lib.pyClose(self.obj)

    def get_manu(self) -> str:
        buf = create_string_buffer(32)
        if self.lib.pyGetManu(self.obj, buf):
            return buf.value.decode()
        return ""

    def get_model(self) -> str:
        buf = create_string_buffer(32)
        if self.lib.pyGetModel(self.obj, buf):
            return buf.value.decode()
        return ""

    def get_sn(self) -> str:
        buf = create_string_buffer(32)
        if self.lib.pyGetSn(self.obj, buf):
            return buf.value.decode()
        return ""

    def get_num_of_finger(self) -> int:
        return self.lib.pyGetNumOfFinger(self.obj)

    def get_num_of_pressure(self) -> int:
        return self.lib.pyGetNumOfPressure(self.obj)

    def get_num_of_arm(self) -> int:
        return self.lib.pyGetNumOfArm(self.obj)

    def get_data(self):
        num = self.get_num_of_finger()
        arr = (c_ushort * num)()
        ret = self.lib.pyGetData(self.obj, arr)
        return ret,list(arr[:num])

    def get_scaled_data(self):
        num = self.get_num_of_finger()
        arr = (c_ushort * num)()
        ret = self.lib.pyGetScaledData(self.obj, arr)
        return ret,list(arr[:num])

    def get_angle(self):
        num = self.get_num_of_finger()
        arr = (c_float * num)()
        ret = self.lib.pyGetAngle(self.obj, arr)
        return ret,list(arr[:num])

    def get_quat(self):
        arr = (c_float * 16)()
        ret = self.lib.pyGetQuat(self.obj, arr)
        return ret,list(arr[:16])

    def get_quat_org(self):
        arr = (c_float * 16)()
        ret = self.lib.pyGetQuatOrg(self.obj, arr)
        return ret,list(arr[:16])

    def get_pressure_raw(self):
        num = self.get_num_of_pressure()
        arr = (c_ushort * num)()
        ret = self.lib.pyGetPressureRaw(self.obj, arr)
        return ret,list(arr[:num])

    def set_calib_mode(self, mode: int):
        self.lib.pySetCalibMode(self.obj, mode)

    def reset_calib(self):
        self.lib.pyResetCalib(self.obj)

    def reset_quat(self):
        self.lib.pyResetQuat(self.obj)

    def zero_pressure(self):
        self.lib.pyZeroPressure(self.obj)

    def set_feedback(self, fddata):
        arr = (ctypes.c_ubyte * len(fddata))(*fddata)
        self.lib.pySetFeedBack(self.obj, arr)
