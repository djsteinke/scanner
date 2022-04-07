import os
import cv2
from imutils import rotate_bound
from time import strftime
from os import getcwd


class Scan(object):
    def __init__(self, cap=None, arduino=None, android=None, d="/", w=640, h=480, s=100, c=None, r=False, sc=None,
                 pitch=0, length=0.0):
        self.cap = cap
        self.arduino = arduino
        self.android = android
        self.wd = d
        self.width = w
        self.height = h
        self.steps = s
        self._step = 0
        self._callback = c
        self._step_callback = sc
        self.path = None
        self.rotate = r
        self.per_step = length/s*pitch
        print(self.per_step)
        self.timestamp = strftime('%Y%m%d%H%M%S')

    def start(self):
        if not self.arduino.connected:
            print("Arduino not connected. Exiting.")
            exit()

        self.path = os.path.join(self.wd, f"scans/{self.timestamp}")  # create scan dir
        os.makedirs(self.path)

        if self.per_step > 0:
            motor_steps = 400 * self.per_step
        else:
            motor_steps = 400 / self.steps

        if not self.arduino.connected:
            self.arduino.open()

        #self.android.open_camera_tmp()
        self.arduino.send_msg("L21")     # Turn ON right laser

        for i in range(0, self.steps):
            self._step = i
            #self.arduino.send_msg("L11")     # Turn ON left laser
            # self.save_frame(f'left_%s_%04d.jpg' % (self.timestamp, i))
            #self.android.take_picture(f'%s/left_%s_%04d.jpg' % (path, self.timestamp, i))
            #self.arduino.send_msg("L10")     # Turn OFF left laser
            #self.arduino.send_msg("L21")     # Turn ON right laser
            #self.save_frame(f'right_%s_%04d.jpg' % (self.timestamp, i))
            self.android.take_picture_tmp(f'%s/right_%s_%04d.jpg' % (self.path, self.timestamp, i))
            #self.arduino.send_msg("L20")     # Turn OFF right laser
            # self.save_frame(f'color_%s_%04d.jpg' % (self.timestamp, i))       # take color photo for color object
            self.arduino.send_msg(f"STEP:{motor_steps}:CW")      # turn platform
            if self._step_callback is not None:
                self._step_callback(i+1)

        # self.arduino.close()     # disconnect arduino

        if self._callback is not None:
            self._callback()

    def save_frame(self, filename):
        ret, image = self.cap.read()
        if self.rotate:
            image = rotate_bound(image, -90)
        file = os.path.join(self.path, filename)
        cv2.imwrite(file, image)

    @property
    def step(self):
        return self._step

    @step.setter
    def step(self, value):
        self._step = value
