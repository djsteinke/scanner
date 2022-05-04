import os
import cv2
from imutils import rotate_bound
from time import strftime
from scan_popup import ScanPopup

steps = 11


class Calibration(object):
    def __init__(self, arduino=None, android=None, path="/", callback=None):
        self.arduino = arduino
        self.android = android
        self.path = path
        self._callback = callback
        self.popup = ScanPopup()

    def start(self):
        self.popup = ScanPopup(steps=steps)
        self.popup.open()
        if not os.path.isdir(self.path):
            os.makedirs(self.path)
        self.calibrate()

    def step(self, val):
        self.popup.step(val)

    def calibrate(self):
        self.arduino.send_msg_new(1)
        self.arduino.send_msg_new(3)
        dps = 180.0 / 360.0 / (steps * 1.0 - 1.0)                 # degrees / step, 180 degrees / 10 steps
        pps = round(200.0 * 16.0 * dps)             # 200 full steps per rotation (motor), 16 micro-steps
        for i in range(1, steps):
            self.android.take_picture(f'%s/calibration_%04d.jpg' % (self.path, i))
            self.arduino.send_msg_new(6, 1, pps)         # turn platform
            if self.popup is not None:
                self.step(i+1)

        self.android.move_files()
        if self._callback is not None:
            self._callback()
