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
            self.arduino.send_msg("L10")            # Turn OFF both lasers
            self.arduino.send_msg("L20")
            dps = 180.0 / 360.0 / 10.0               # degrees / step, 180 degrees / 10 steps
            pps = round(200.0 * 16.0 * dps)          # 200 full steps per rotation (motor), 16 micro-steps
            for i in range(1, 12):
                self.android.take_picture_tmp(f'%s/calibration_%04d.jpg' % (self.path, i))
                self.arduino.send_msg(f"STEP:{pps}:CCW")      # turn platform
                if self.popup is not None:
                    self.step(i+1)
            if self._callback is not None:
                self._callback()
