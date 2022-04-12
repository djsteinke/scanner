import os
import cv2
from imutils import rotate_bound
from time import strftime
from scan_popup import ScanPopup


class Calibration(object):
    def __init__(self, arduino=None, android=None, path="/", linear=False, callback=None):
        self.arduino = arduino
        self.android = android
        self._callback = None
        self.path = path
        self.linear = linear
        #self.per_step = length/s*pitch
        #print(self.per_step)
        self._callback = callback
        self.popup = ScanPopup()

    def start(self):
        self.popup = ScanPopup(steps=10)
        self.popup.open()
        os.makedirs(self.path)
        self.calibrate()

    def step(self, val):
        self.popup.step(val)

    def calibrate(self):
        if self.linear:
            tmp = 1
        else:
            self.arduino.send_msg("L10")     # Turn OFF both lasers
            self.arduino.send_msg("L20")
            pulses = 20        # 1/2 micro steps, 18 deg/pic
            for i in range(0, 11):
                self.android.take_picture_tmp(f'%s/calibration_%04d.jpg' % (self.path, i))
                self.arduino.send_msg(f"STEP:{pulses}:CW")      # turn platform
                if self.popup is not None:
                    self.step(i+1)
            if self._callback is not None:
                self._callback()
