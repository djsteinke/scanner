
import logging
import math
import threading
from time import sleep
from tkinter import *
import _tkinter
from tkinter.ttk import Progressbar
from threading import Timer

import matplotlib
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from numpy import array

import calibration
from android import Android
from arduino import Arduino
from calibrate_camera import CameraCalibration
from calibrate_scalar import AndroidScalar
from collapsible_pane import CollapsiblePane
from circular_scan import CircularScan
from subprocess import run
from os import getcwd, makedirs, path

from parser import points_triangulate
from parser_util import points_max_cols
from scan_popup import ScanPopup
from calibration import Calibration, AndroidCalibration
from hdpitkinter import HdpiTk
from PIL import ImageTk, Image
import cv2
import socket
import io

import numpy as np

cam_id = 0
arduino = Arduino(speed=9600)
arduino_com = "COM3"

scanning = False
connected = False
android = Android()
android_connected = False
popup = None

font = "arial 9"
font_bold = font + " bold"

# create logger with 'spam_application'
logger = logging.getLogger('CircularScan')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('scan.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


ms = 2.0


def adb(start):
    if start:
        res = run(['adb', 'start-server'], capture_output=True)
    else:
        res = run(['adb', 'kill-server'], capture_output=True)
    print(res)
    return res.returncode


def in_progress(text, close, result=None):
    global popup, android_connected
    if not close:
        popup = Toplevel(root)
        popup.geometry('300x100+100+450')
        pady = 20
        if text is not None:
            popup_label = Label(popup, text=text)
            popup_label.pack(pady=(pady, 0))
            pady = 3
        progress_bar = Progressbar(popup, orient=HORIZONTAL, length=100, mode='indeterminate')
        progress_bar.pack(pady=(pady, 0))
        progress_bar.start(10)
        popup.grab_set()
    else:
        if popup is not None:
            popup.destroy()
        if result == "connected":
            android_connected = not android_connected
            connect_android['text'] = 'Disconnect' if android_connected else 'Connect'


def connect():
    global android_connected
    try:
        if not android_connected:
            if adb(True) == 0:
                host = "%s.%s.%s.%s" % (host_value1.get('1.0', 'end-1c'), host_value2.get('1.0', 'end-1c'),
                                        host_value3.get('1.0', 'end-1c'), host_value4.get('1.0', 'end-1c'))
                android.connect(host, int(port_value.get("1.0", 'end-1c')), in_progress)
        else:
            android.disconnect()
            adb(False)
        android_connected = not android_connected
        connect_android['text'] = 'Disconnect' if android_connected else 'Connect'
    except Exception as e:
        print(str(e))
        adb(False)
        in_progress(None, True)


def connect_android():
    global popup, android
    in_progress("Connecting...", False)
    adb(True)
    host = "%s.%s.%s.%s" % (host_value1.get('1.0', 'end-1c'), host_value2.get('1.0', 'end-1c'),
                            host_value3.get('1.0', 'end-1c'), host_value4.get('1.0', 'end-1c'))
    port = int(port_value.get("1.0", 'end-1c'))
    android = Android(host=host, port=port, cb=in_progress)
    Timer(0.1, android.connect).start()


scan_steps = 0
current_step = 0


def scan_clicked():
    global scan_popup, scan, scan_steps
    scan_steps = int(steps_scan.get('1.0', 'end-1c'))
    degrees = float(scan_degrees.get('1.0', 'end-1c'))
    ll = use_left_laser.get() == 1
    rl = use_right_laser.get() == 1
    color = use_color.get() == 1
    pics = use_left_laser.get() + use_right_laser.get() + use_color.get()
    #scan_popup = ScanPopup(root, scan_steps, pics)
    #scan_popup.open()
    if not arduino.connected:
        arduino_connect()
    step(0)
    camera_calibration = None
    scan = CircularScan(arduino=arduino, android=android, d=getcwd(), s=scan_steps, c=None, sc=step,
                        degrees=degrees, rl=rl, ll=ll, color=color, cap=None, camera_calibration=camera_calibration,
                        brightness=bright_v, contrast=contrast_v)
    Timer(0.1, scan.start).start()


def scan_started():
    scan_popup.tl.grab_set()


def camera_calibration_clicked():
    Timer(0.1, run_camera_calibration).start()


def run_camera_calibration():
    cal_path = getcwd() + "\\calibration\\circular"
    cal = Calibration(arduino=arduino, camera=cam, android=None, path=cal_path)
    cal.start()


def android_calibration_clicked():
    Timer(0.1, run_android_calibration).start()


def run_android_calibration():
    global android_calibration
    cal_path = getcwd() + "\\calibration\\android"
    cal = AndroidCalibration(path=cal_path, arduino=arduino)
    cal.calibrate()
    android_calibration = CameraCalibration(cal_path, reload=False)


def android_cal_scalar_clicked():
    Timer(0.1, run_android_cal_scalar).start()


def run_android_cal_scalar():
    cwd = getcwd() + "\\calibration\\android"
    cal = AndroidScalar(cwd)
    cal.start()


def calibration_clicked():
    if tl is not None:
        tl.destroy()
    Timer(0.1, run_calibration).start()


tl = None
cal_cnt = 0


def run_calibration():
    global tl, cal_cnt
    d = getcwd() + "\\calibration"
    if cal_cnt == 0:
        android.take_picture(f'%s\\calibration_%s.jpg' % (d, 'F0'))
        arduino.send_msg_new(2)
        android.take_picture(f'%s\\calibration_%s.jpg' % (d, 'F1'))
        arduino.send_msg_new(1)
        arduino.send_msg_new(4)
        android.take_picture(f'%s\\calibration_%s.jpg' % (d, 'F2'))
        arduino.send_msg_new(3)
        # motor_steps = int(200.0 * 16.0 * 180.0 / 360.0)
        # arduino.send_msg_new(6, 1, motor_steps)         # turn platform
        tl = Toplevel()
        tl.geometry('200x100+100+450')
        lb = Label(tl, text='Move pattern to back.')
        lb.pack(pady=(20, 0))
        cb = Button(tl, text="Continue", command=calibration_clicked, width=15)
        cb.pack(pady=(10, 0))
        tl.grab_set()
        cal_cnt += 1
    elif cal_cnt == 1:
        android.take_picture(f'%s\\calibration_%s.jpg' % (d, 'B0'))
        arduino.send_msg_new(2)
        android.take_picture(f'%s\\calibration_%s.jpg' % (d, 'B1'))
        arduino.send_msg_new(1)
        arduino.send_msg_new(4)
        android.take_picture(f'%s\\calibration_%s.jpg' % (d, 'B2'))
        arduino.send_msg_new(3)
        tl = Toplevel()
        tl.geometry('200x100+100+450')
        lb = Label(tl, text='Move pattern to center.')
        lb.pack(pady=(20, 0))
        cb = Button(tl, text="Continue", command=calibration_clicked, width=15)
        cb.pack(pady=(10, 0))
        tl.grab_set()
        cal_cnt += 1
    else:
        android.take_picture(f'%s\\calibration_%s.jpg' % (d, 'C0'))
        arduino.send_msg_new(2)
        android.take_picture(f'%s\\calibration_%s.jpg' % (d, 'C1'))
        arduino.send_msg_new(1)
        arduino.send_msg_new(4)
        android.take_picture(f'%s\\calibration_%s.jpg' % (d, 'C2'))
        arduino.send_msg_new(3)
        sleep(1)
        android.move_files()
        cal_cnt = 0


def take_pic_clicked():
    if cam:
        ret, cv2image = cam.read()
        if ret:
            h, w, _ = cv2image.shape
            if w > h:
                cv2image = cv2.rotate(cv2image, cv2.ROTATE_90_COUNTERCLOCKWISE)

            cv2image = camera_calibration.undistort_img(cv2image, crop=False)
            p = getcwd() + "\\calibration\\pics\\pic_0001.jpg"
            cv2.imwrite(p, cv2image)
            print(cv2image.shape)
            print(print_px())


def step(s):
    global current_step
    if s == -1:
        #scan_popup.error("ERROR:\nArduino not connected.\nConnect arduino and try again.")
        tmp = 1
    else:
        #scan_popup.step(s)
        current_step = s
        per = s / scan_steps * 100
        pb['value'] = per
        lb['text'] = f'Step: %d/%d' % (current_step, scan_steps)
        if s > 0:
            process_pic(s)
        if scan.complete and arduino.connected:
            # Once scan is complete, disconnect arduino
            arduino_connect()


def process_pic(s):
    global scan_xyz, curr_xyz
    s = s-1
    l_img = cv2.imread(scan.path + "\\images\\" + 'right_%04d.jpg' % s)
    c_img = cv2.imread(scan.path + "\\images\\" + 'color_%04d.jpg' % s)
    xy = points_max_cols(l_img, threshold=(160, 255), c=True, roi=[[0, 1080], [0, 1920]])
    offset = -s * float(scan.dps)
    xyz = []
    for x, y in xy:
        p = points_triangulate((x, y), offset, color=c_img, right=True)
        r = math.sqrt(math.pow(p[0], 2) + math.pow(p[2], 2))
        if r < 120:
            xyz.append(p)

    curr_xyz = array(xyz)
    if len(xyz) > 0:
        scan_xyz = np.append(scan_xyz, curr_xyz, axis=0)
    prev_l = len(scan_xyz) - len(curr_xyz)

    sc._offsets3d = (scan_xyz[prev_l:, 0], scan_xyz[prev_l:, 2], scan_xyz[prev_l:, 1])
    scan_sc._offsets3d = (scan_xyz[:prev_l, 0], scan_xyz[:prev_l, 2], scan_xyz[:prev_l, 1])

    rot = (offset + 90) % 360 - 180
    ax.view_init(elev=30, azim=rot, roll=0)

    canvas.draw()


def scan_complete():
    tmp = 1


def stop_scan():
    # TODO stop scans
    tmp = 1


def move_deg(deg):
    rot_dir = 0
    if deg < 0:
        rot_dir = 1
        deg = abs(deg)
    turns = float(deg)
    motor_steps = int(200 * ms * turns / 360)
    arduino.send_msg_new(6, rot_dir, motor_steps)         # turn platform


def move_right_click():
    Timer(0.1, move_right).start()


def move_left_click():
    Timer(0.1, move_left).start()


def move_right():
    turns = float(mv_turns.get('1.0', 'end-1c'))
    motor_steps = int(200.0 * ms * turns / 360.0 * 7.2)
    arduino.send_msg_new(6, 0, motor_steps)         # turn platform
    #print_px()
    # arduino.send_msg(f"STEP:{motor_steps}:CCW")     # turn platform


def move_left():
    turns = float(mv_turns.get('1.0', 'end-1c'))
    motor_steps = int(200.0 * ms * turns / 360.0 * 7.2)
    arduino.send_msg_new(6, 1, motor_steps)         # turn platform
    #print_px()
    #arduino.send_msg(f"STEP:{motor_steps}:CW")  # turn platform


def print_px():
    ret, cv2image = cam.read()
    if ret:
        h, w, _ = cv2image.shape
        if w > h:
            cv2image = cv2.rotate(cv2image, cv2.ROTATE_90_COUNTERCLOCKWISE)

        cv2image = camera_calibration.undistort_img(cv2image, crop=True)

        h, w, _ = cv2image.shape
        # print(h, w)
        calibration.find_checkerboard(cv2image)
        print(len(calibration.get_corners()))
        if len(calibration.get_corners()) > 0:
            pX = calibration.corners_ret[(calibration.ny-1) * calibration.nx][0][0]
            pdx = 0
            pdy = 0
            pdt = 0
            # print(calibration.corners_ret)
            for y in range(0, calibration.ny-1):
                for x in range(0, calibration.nx-1):
                    pdt += 1
                    i = y*calibration.nx + x
                    pdx += calibration.corners_ret[i+1][0][0] - calibration.corners_ret[i][0][0]
                    pdy += calibration.corners_ret[i+calibration.nx][0][1] - calibration.corners_ret[i][0][1]
            pdx /= pdt
            pdy /= pdt
            print(pX, pdx, pdy)


def laser_one():
    if laser_one_button['relief'] == 'raised':
        arduino.send_msg_new(7, v=l1_duty.get())
        arduino.send_msg_new(2)
        laser_one_button.config(bg="#EC7063")
        laser_one_button['relief'] = 'sunken'
        l1_duty_slider['state'] = 'disabled'
    else:
        arduino.send_msg_new(1)
        laser_one_button.config(bg="SystemButtonFace")
        laser_one_button['relief'] = 'raised'
        l1_duty_slider['state'] = 'active'


def laser_two():
    if laser_two_button['relief'] == 'raised':
        arduino.send_msg_new(8, v=l2_duty.get())
        arduino.send_msg_new(4)
        laser_two_button.config(bg="#EC7063")
        laser_two_button['relief'] = 'sunken'
        l2_duty_slider['state'] = 'disabled'
    else:
        arduino.send_msg_new(3)
        laser_two_button.config(bg="SystemButtonFace")
        laser_two_button['relief'] = 'raised'
        l2_duty_slider['state'] = 'active'


def flat_clicked():
    curr_p0x = float(1080.0)
    while True:
        print("move")
        move_deg(-1)
        ret, cv2image = cam.read()
        if ret:
            h, w, _ = cv2image.shape
            if w > h:
                cv2image = cv2.rotate(cv2image, cv2.ROTATE_90_COUNTERCLOCKWISE)

            cv2image = camera_calibration.undistort_img(cv2image, crop=True)
            calibration.find_checkerboard(cv2image)
            p0x = float(calibration.p0x)
            pX = calibration.corners_ret[(calibration.ny-1)*calibration.nx][0][0]
            pdx = 0
            for i in range(0, calibration.ny-1):
                # print(calibration.corners_ret[i*calibration.nx][0][0])
                pdx += calibration.corners_ret[(i+1)*calibration.nx][0][0] - calibration.corners_ret[i*calibration.nx][0][0]
            pdx /= calibration.ny
            p0x = pX
            print(curr_p0x, p0x)
            if p0x - curr_p0x > 0.0:
                break
            else:
                curr_p0x = p0x
        sleep(0.5)


def arduino_connect():
    if arduino.connected:
        arduino.send_msg_new(a=10)
        arduino.close()
    else:
        try:
            arduino.port = pico_port_value.get('1.0', 'end-1c')
            arduino.open()
        except Exception as e:
            print(str(e))
    arduino_con_bt['text'] = '-' if arduino.connected else '+'
    arduino.send_msg_new(a=9)
    if arduino.connected:
        arduino_con_bt.config(bg="#EC7063")
        arduino_con_bt['relief'] = 'sunken'
        r = rpm.get('1.0', 'end-1c')
        #arduino.send_msg(f'RPM:{r}')
        arduino.send_msg_new(5, 0, int(r))
    else:
        arduino_con_bt.config(bg="SystemButtonFace")
        arduino_con_bt['relief'] = 'raised'


curr_img = None


def show_webcam():
    global curr_img

    # Get the latest frame and convert into Image
    ret, cv2image = cam.read()
    if ret:
        h, w, _ = cv2image.shape
        if w > h:
            cv2image = cv2.rotate(cv2image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            h, w, _ = cv2image.shape
        cv2image = camera_calibration.undistort_img(cv2image, crop=True)

        curr_img = cv2image

        # print(cv2image.shape)

        r = 1.0
        if h > 640:
            r = float(h)/640.0
            w = int(float(w) / r)
            h = int(float(h) / r)
            cv2image = cv2.resize(cv2image, (w, h), interpolation=cv2.INTER_AREA)
        #cv2image = cv2.line(cv2image, (0, int(h / 2)), (w, int(h / 2)), [0, 0, 255], 1)
        hc = int(camera_calibration.mtx[1][2]/r)
        wc = int(camera_calibration.mtx[0][2]/r)
        cv2image = cv2.line(cv2image, (wc, 0), (wc, h), [0, 0, 255], 1)
        cv2image = cv2.line(cv2image, (0, hc), (w, hc), [0, 0, 255], 1)
        cv2image = calibration.find_checkerboard(cv2image, True)
        # Convert image to PhotoImage
        try:
            cv2image = cv2.cvtColor(cv2image, cv2.COLOR_BGR2RGB)
            cv2image = apply_brightness_contrast(cv2image)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            rmain.imgtk = imgtk
            rmain.configure(image=imgtk)
        except _tkinter.TclError or RuntimeError as e:
            print('Error: ', str(e))
        # Repeat after an interval to capture continiously
    rmain.after(200, show_webcam)


def func_bright_contrast(img):
    global bright, contrast
    bright = 255 - cv2.getTrackbarPos('bright', 'adjust')
    contrast = 127 - cv2.getTrackbarPos('contrast', 'adjust')
    #effect = apply_brightness_contrast(img, bright, contrast)
    #cv2.imshow('Effect', effect)


def apply_brightness_contrast(input_img):
    #global bright, contrast
    #brightness = map(bright, 0, 510, -255, 255)
    #contrast = map(contrast, 0, 254, -127, 127)
    bright = bright_v.get()
    contrast = contrast_v.get()
    if bright != 0:
        if bright > 0:
            shadow = bright
            highlight = 255
        else:
            shadow = 0
            highlight = 255 + bright
        alpha_b = (highlight - shadow)/255
        gamma_b = shadow
        buf = cv2.addWeighted(input_img, alpha_b, input_img, 0, gamma_b)
    else:
        buf = input_img.copy()
    if contrast != 0:
        f = float(131 * (contrast + 127)) / (127 * (131 - contrast))
        alpha_c = f
        gamma_c = 127*(1-f)
        buf = cv2.addWeighted(buf, alpha_c, buf, 0, gamma_c)
    cv2.putText(buf, 'B:{},C:{}'.format(bright, contrast), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    return buf


def update_plot():
    scan_dir = '20221230134211'
    scan_path = getcwd() + "\\scans\\" + scan_dir
    details_path = f'{scan_path}\\{scan_dir}.xyz'
    pc = np.loadtxt(details_path, float)
    print(len(pc))

    up_cnt = int(len(pc) / 100)
    up = 0
    lp = 0
    y = []
    for a, b, c, _, _, _, _, _, _ in pc:
        y.append([a, c, b])
        up += 1
        if up >= up_cnt:
            lp += 1
            print(lp)
            up = 0
            z = array(y)
            rot = ((lp * 3) + 180) % 360 - 180
            #ax.view_init(0, rot, 0)
            #plt.draw()
            #canvas.draw()
            # fig.canvas.flush_events()
            # x, y, z = [], [], []
            #plt.pause(0.1)
            # y = []

    z = array(y)
    w = array(scan_xyz)
    #sc._offsets3d = (z[:, 0], z[:, 1], z[:, 2])
    scan_sc._offset3d = (w[:, 0], w[:, 1], w[:, 2])
    canvas.draw()


def quit_me():
    print('quit')
    root.quit()
    root.destroy()


if __name__ == '__main__':
    root = HdpiTk()
    root.protocol("WM_DELETE_WINDOW", quit_me)
    #root = Tk()
    root.grid_rowconfigure(0, weight=1)  # this needed to be added
    root.grid_columnconfigure(0, weight=1)  # as did this
    root.grid_columnconfigure(1, weight=1)  # as did this

    root.title("Circular Scanner")

    menubar = Menu(root, background='#ff8000', foreground='black', activebackground='white', activeforeground='black')
    file = Menu(menubar, tearoff=0, background='#ffcc99', foreground='black')
    file.add_command(label="New")
    file.add_command(label="Open")
    file.add_command(label="Save")
    file.add_command(label="Save as")
    file.add_separator()
    file.add_command(label="Exit", command=quit_me)
    menubar.add_cascade(label="File", menu=file)

    mn = Frame(root)
    mn.columnconfigure(0, weight=1)
    mn.columnconfigure(1, weight=3)

    mn_row = -1

    mn_row += 1

    config_label = Label(mn, text="Pico Control", font=font_bold)
    config_label.grid(columnspan=2, column=0, row=mn_row, sticky=W, pady=(20, 0))

    mn_row += 1
    pico_port_label = Label(mn, text="Port:")
    pico_port_label.grid(column=0, row=mn_row, padx=(10, 0), pady=(3, 15), sticky=W)
    pico_port_value = Text(mn, width=5, height=1)
    pico_port_value.insert('1.0', 'COM3')
    pico_port_value.grid(column=1, row=mn_row, padx=(10, 10), sticky=W)
    arduino_con_bt = Button(mn, text="+", width=3, command=arduino_connect)
    arduino_con_bt.grid(column=1, row=mn_row)
    mn_row += 1

    config_label = Label(mn, text="Rotate")
    config_label.grid(column=0, row=mn_row, sticky=W, padx=(10, 0), pady=3)
    fr = Frame(mn)
    mv_left_button = Button(fr, text="<-", command=move_left_click, width=5)
    mv_left_button.grid(column=0, row=0, pady=3)
    mv_turns = Text(fr, width=4, height=1)
    mv_turns.insert('1.0', '5')
    mv_turns.grid(column=1, row=0, padx=(10, 10))
    mv_right_button = Button(fr, text="->", command=move_right_click, width=5)
    mv_right_button.grid(column=2, row=0, pady=3)
    fr.grid(column=1, row=mn_row, sticky=EW)
    mn_row += 1

    l1_duty = IntVar(value=90)
    l2_duty = IntVar(value=90)
    laser_one_button = Button(mn, text="L", command=laser_one, font=font_bold, width=5)
    laser_one_button.grid(column=0, row=mn_row, padx=(10, 0), sticky=W)
    l1_duty_slider = Scale(mn, variable=l1_duty, from_=0, to=100, orient=HORIZONTAL, sliderlength=20, tickinterval=50)
    l1_duty_slider.grid(column=1, row=mn_row, padx=(0, 0), pady=(3, 0), sticky=EW)
    mn_row += 1
    laser_two_button = Button(mn, text="R", command=laser_two, font=font_bold, width=5)
    laser_two_button.grid(column=0, row=mn_row, padx=(10, 0), sticky=W)
    l2_duty_slider = Scale(mn, variable=l2_duty, from_=0, to=100, orient=HORIZONTAL, sliderlength=20, tickinterval=50)
    l2_duty_slider.grid(column=1, row=mn_row, padx=(0, 0), pady=(3, 10), sticky=EW)

    mn_row += 1
    config_label = Label(mn, text="Android Control", font=font_bold)
    config_label.grid(columnspan=2, column=0, row=mn_row, sticky=W, pady=(20, 0))

    mn_row += 1
    host_label = Label(mn, text="Host:")  # 255.255.255.255
    host_label.grid(column=0, row=mn_row, padx=(10, 0), pady=3, sticky=W)
    host_frame = Frame(mn)
    host_value1 = Text(host_frame, width=3, height=1)
    host_value1.insert('1.0', '192')
    host_value1.grid(column=0, row=0)
    Label(host_frame, text=".").grid(column=1, row=0)
    host_value2 = Text(host_frame, width=3, height=1)
    host_value2.insert('1.0', '168')
    host_value2.grid(column=2, row=0)
    Label(host_frame, text=".").grid(column=3, row=0)
    host_value3 = Text(host_frame, width=3, height=1)
    host_value3.insert('1.0', '0')
    host_value3.grid(column=4, row=0)
    Label(host_frame, text=".").grid(column=5, row=0)
    host_value4 = Text(host_frame, width=3, height=1)
    host_value4.insert('1.0', '139')
    host_value4.grid(column=6, row=0, padx=(0, 10))
    host_frame.grid(column=1, row=mn_row, padx=(10, 10), pady=3, sticky=W)

    mn_row += 1
    port_label = Label(mn, text="Port:")
    port_label.grid(column=0, row=mn_row, padx=(10, 0), pady=3, sticky=W)
    port_value = Text(mn, width=5, height=1)
    port_value.insert('1.0', '50001')
    port_value.grid(column=1, row=mn_row, padx=(10, 10), sticky=W)
    #mn_row += 1
    #connect_android = Button(mn, text="Connect", command=connect_android, font=font_bold, width=10)
    #connect_android.grid(column=0, columnspan=2, row=mn_row, padx=(0, 0), pady=(3, 10))

    mn_row += 1
    label = Label(mn, text="Scan Setup", font=font_bold)
    label.grid(columnspan=2, column=0, row=mn_row, sticky=W, pady=(20, 0))
    use_metric = IntVar(value=1)
    mn_row += 1
    label = Label(mn, text="Degrees:")
    label.grid(column=0, row=mn_row, padx=(10, 0), pady=3, sticky=W)
    scan_degrees = Text(mn, width=3, height=1)
    scan_degrees.insert('1.0', '360')
    scan_degrees.grid(column=1, row=mn_row, padx=(10, 10), sticky=W)
    mn_row += 1
    label = Label(mn, text="Steps/Scan:")
    label.grid(column=0, row=mn_row, padx=(10, 0), pady=3, sticky=W)
    steps_scan = Text(mn, width=3, height=1)
    steps_scan.insert('1.0', '120')
    steps_scan.grid(column=1, row=mn_row, padx=(10, 10), sticky=W)
    mn_row += 1
    label = Label(mn, text="Speed (rpm):")
    label.grid(column=0, row=mn_row, padx=(10, 0), pady=3, sticky=W)
    rpm = Text(mn, width=3, height=1)
    rpm.insert('1.0', '20')
    rpm.grid(column=1, row=mn_row, padx=(10, 10), sticky=W)
    use_left_laser = IntVar()
    use_right_laser = IntVar(value=1)
    use_color = IntVar(value=1)
    mn_row += 1
    label = Label(mn, text="Left Laser:")
    label.grid(column=0, row=mn_row, padx=(10, 0), pady=3, sticky=W)
    left_laser = Checkbutton(mn, variable=use_left_laser)
    left_laser.grid(column=1, row=mn_row, padx=(5, 0), sticky=W)
    mn_row += 1
    label = Label(mn, text="Right Laser:")
    label.grid(column=0, row=mn_row, padx=(10, 0), pady=3, sticky=W)
    right_laser = Checkbutton(mn, variable=use_right_laser)
    right_laser.grid(column=1, row=mn_row, padx=(5, 0), sticky=W)
    mn_row += 1
    label = Label(mn, text="Color:")
    label.grid(column=0, row=mn_row, padx=(10, 0), pady=3, sticky=W)
    color_cb = Checkbutton(mn, variable=use_color)
    color_cb.grid(column=1, row=mn_row, padx=(5, 0), sticky=W)
    mn_row += 1
    bright_v = IntVar(value=0)
    contrast_v = IntVar(value=0)
    """
    bright_slider = Scale(mn, variable=bright_v, from_=-255, to=255, orient=HORIZONTAL)
    contrast_slider = Scale(mn, variable=contrast_v, from_=-127, to=127, orient=HORIZONTAL)
    bright_slider.grid(column=0, columnspan=2, row=mn_row, padx=(0, 0), pady=(3, 10))
    mn_row += 1
    contrast_slider.grid(column=0, columnspan=2, row=mn_row, padx=(0, 0), pady=(3, 10))
    mn_row += 1
    """
    fr = Frame(mn)
    fr.columnconfigure(0, weight=1)
    fr.columnconfigure(1, weight=1)
    but_start = Button(fr, text="Cal. Android", command=android_calibration_clicked, font=font_bold, width=10)
    but_start.grid(column=0, row=mn_row, padx=15, pady=0, sticky=EW)
    but_start = Button(fr, text="Cal. Scalar", command=android_cal_scalar_clicked, font=font_bold, width=10)
    but_start.grid(column=1, row=mn_row, padx=15, pady=0, sticky=EW)
    fr.grid(column=0, columnspan=2, row=mn_row, padx=(10, 10), pady=(7, 0))
    mn_row += 1

    but_start = Button(mn, text="Start Scan", command=scan_clicked, font=font_bold, width=10)
    but_start.grid(column=0, columnspan=2, row=mn_row, padx=(0, 0), pady=(10, 0))
    """
    fr = Frame(mn)
    but_start = Button(fr, text="Cal. Scalar", command=calibration_clicked, font=font_bold, width=10)
    but_start.grid(column=0, columnspan=1, row=0, padx=(0, 10), pady=(0, 0), sticky=EW)
    but_start = Button(fr, text="Cal. Camera", command=android_calibration_clicked, font=font_bold, width=10)
    but_start.grid(column=1, columnspan=1, row=0, padx=(10, 0), pady=(0, 0), sticky=EW)
    fr.grid(column=0, columnspan=2, row=mn_row, padx=(0, 0), pady=(7, 0))
    mn_row += 1
    but_start = Button(mn, text="Find Flat", command=flat_clicked, font=font_bold, width=10)
    but_start.grid(column=1, columnspan=1, row=mn_row, padx=(0, 0), pady=(10, 0))

    mn_row += 1
    but_start = Button(mn, text="Take Pic", command=take_pic_clicked, font=font_bold, width=10)
    but_start.grid(column=0, columnspan=1, row=mn_row, padx=(0, 0), pady=(10, 0))
    """
    mn_row += 1
    but_start = Button(mn, text="draw", command=update_plot, font=font_bold, width=10)
    but_start.grid(column=0, columnspan=1, row=mn_row, padx=(0, 0), pady=(10, 0))
    mn_row += 1
    mn.grid(column=0, row=0, padx=10, pady=(0, 10))
    #mn.pack(padx=10, pady=(0, 10))
    # Create a label in the frame
    #rmain = Label(root)
    #rmain.grid(column=1, row=0)

    rmain = Frame(root)
    #rmain.columnconfigure(0, weight=1)
    #rmain.grid(column=1, row=0)

    scan_frame = Frame(rmain)
    lb = Label(scan_frame, text='Step: %d/%d' % (0, scan_steps))
    lb.pack()
    pb = Progressbar(scan_frame, orient=HORIZONTAL, length=300, mode='determinate')
    pb.pack()
    scan_frame.pack(pady=(0, 10))

    matplotlib.use("TkAgg")

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    curr_xyz = array([[-150, -150, -150]])
    scan_xyz = array([[150, 150, 150, 0, 0, 0, 0, 0, 0, 0]])
    ax.set_zlim(-150, 150)
    up = 0
    plt.xlim(-150, 150)
    plt.ylim(-150, 150)
    sc = ax.scatter(scan_xyz[:, 0], scan_xyz[:, 2], scan_xyz[:, 1], s=0.3, marker='o', c="green", label="curr")
    scan_sc = ax.scatter(scan_xyz[:, 0], scan_xyz[:, 2], scan_xyz[:, 1], s=0.1, marker='o', c="gray", label="prev")
    canvas = FigureCanvasTkAgg(fig, rmain)
    canvas.draw()
    canvas.get_tk_widget().pack()
    #canvas.get_tk_widget().grid(row=0, column=1)
    toolbar = NavigationToolbar2Tk(canvas, rmain)
    toolbar.update()
    canvas.get_tk_widget().pack()
    rmain.grid(column=1, row=0)

    webcam = False
    if webcam:
        p = getcwd() + "\\calibration\\circular"
        if path.isfile(p + "\\calibration_0001.jpg"):
            camera_calibration = CameraCalibration(p, reload=True)
        else:
            camera_calibration = CameraCalibration(wd=None)

        cam = cv2.VideoCapture(cam_id, cv2.CAP_DSHOW)
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    android_config = True
    if android_config:
        p = getcwd() + "\\calibration\\android"
        if path.isfile(p + "\\calib_pickle.p"):
            android_calibration = CameraCalibration(p, reload=True)

    scan_popup = ScanPopup(root, 0)
    scan = CircularScan()

    #cv2.namedWindow('adjust', 1)
    #cv2.createTrackbar('bright', 'adjust', bright, 2 * 255, func_bright_contrast)
    #cv2.createTrackbar('contrast', 'adjust', contrast, 2 * 127, func_bright_contrast)

    #show_webcam()
    #update_plot()

    root.config(menu=menubar)
    root.mainloop()
