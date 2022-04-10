import os
from time import strftime
import json


class LinearScan(object):
    def __init__(self, cap=None, arduino=None, android=None, d="/", s=100, c=None, sc=None,
                 pitch=1, length=0.0, ll=False, rl=True, metric=True):
        self.cap = cap
        self.arduino = arduino
        self.android = android
        self.wd = d
        self.steps = s
        self.ll = ll
        self.rl = rl
        self._step = 0
        self._callback = c
        self._step_callback = sc
        self.path = None
        self.pitch = pitch
        self.metric = metric
        if metric:
            ps = length/s/pitch
        else:
            ps = length/s*pitch
        self.per_step = ps
        print(self.per_step)
        self.timestamp = strftime('%Y%m%d%H%M%S')

    def start(self):
        self.path = os.path.join(self.wd, f"scans")
        self.save_details()
        if not self.arduino.connected:
            print("Arduino not connected. Exiting.")
            if self._step_callback is not None:
                self._step_callback(-1)
            exit()

        self.path = os.path.join(self.wd, f"scans\\{self.timestamp}")  # create scans dir
        os.makedirs(self.path)
        self.save_details()

        motor_steps = 400 * self.per_step

        if not self.arduino.connected:
            self.arduino.open()

        if not self.ll:
            self.arduino.send_msg("L21")     # Turn ON right laser

        for i in range(0, self.steps):
            self._step = i
            if self.ll:
                self.arduino.send_msg("L11")     # Turn ON left laser
                self.android.take_picture(f'%s\\left_%s_%04d.jpg' % (self.path, self.timestamp, i))
                self.arduino.send_msg("L10")     # Turn OFF left laser
            if self.rl:
                if self.ll:
                    self.arduino.send_msg("L21")     # Turn ON right laser
                self.android.take_picture_tmp(f'%s\\right_%s_%04d.jpg' % (self.path, self.timestamp, i))
                if self.ll:
                    self.arduino.send_msg("L20")     # Turn OFF right laser
            self.arduino.send_msg(f"STEP:{motor_steps}:CW")      # turn platform
            if self._step_callback is not None:
                self._step_callback(i+1)

        self.android.sync_media_service()
        if self._callback is not None:
            self._callback()

    def save_details(self):
        if self.metric:
            distance = self.pitch*self.per_step
        else:
            distance = 25.4/18.0*self.per_step
        details = {"date": self.timestamp,
                   "steps": self.steps,
                   "ll": self.ll,
                   "rl": self.rl,
                   "dps": '%0.2f' % distance}
        print(details)
        d_path = self.path + "\\details.json"
        f = open(d_path, 'w')
        f.write(json.dumps(details))
        f.close()

    @property
    def step(self):
        return self._step

    @step.setter
    def step(self, value):
        self._step = value
