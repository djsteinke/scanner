from tkinter import *
from tkinter.ttk import Progressbar


class ScanPopup(object):
    def __init__(self, root=None, steps=None):
        self.root = root
        self.steps = steps
        self.tl = None
        self.cb = None
        self.pb = None
        self.vl = None

    def open(self):
        self.tl = Toplevel(self.root)
        self.cb = Button(self.tl, text="Cancel", command=self.cancel)
        self.pb = Progressbar(self.tl, orient=HORIZONTAL, length=200, mode='determinate')
        self.vl = Label(self.tl, text='Step: %d/%d' % (0, self.steps))
        self.tl.geometry('300x140+100+450')
        self.vl.pack(pady=(20, 0))
        self.pb.pack(pady=(3, 0))
        self.cb.pack(pady=(6, 0))
        self.tl.grab_set()

    def error(self, msg):
        self.vl['text'] = msg
        self.cb['text'] = 'Close'

    def move(self, val):
        per = val / self.steps * 100
        self.pb['value'] = per
        self.vl['text'] = 'Moving: %d/%d' % (0, self.steps)

    def step(self, val):
        per = val / self.steps * 100
        self.pb['value'] = per
        self.vl['text'] = 'Step: %d/%d' % (val, self.steps)
        if self.pb['value'] == 100:
            self.vl['text'] = 'Scan complete.'
            self.cb['text'] = 'Close'

    def cancel(self):
        if self.cb['text'] == 'Close':
            self.tl.destroy()
        else:
            self.step(self.pb['value']*2+10)
