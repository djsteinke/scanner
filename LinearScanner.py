from tkinter import *
import _tkinter
from tkinter.ttk import Progressbar
from urllib import request
import urllib3
import json
import numpy as np
from PIL import ImageTk, Image
from threading import Timer
from pico import Pico
from cv2 import cv2
from os import getcwd, makedirs, path
from scan_popup import ScanPopup
from hdpitkinter import HdpiTk
from time import sleep, strftime
from calibrate_camera import CameraCalibration

cam_id = 1
pico_port = "COM6"
pico = Pico(com=pico_port, speed=9600)

scanning = False
connected = False
popup = None

font = "arial 9"
font_bold = font + " bold"

pitch = 2.0  # mm/rot
spr = 32.0 * 16.0  # steps per rotation
rpm = 5.0  # max rpt for 28byj stepper
max_length = 310.0  # max length of screw
scan_length = 0.0
scan_steps = 0


def save_details(scan_path, details):
    print(details)
    d_path = scan_path + "\\details.json"
    f = open(d_path, 'w')
    f.write(json.dumps(details))
    f.close()


def scan_clicked():
    global scan_popup, scan_length, scan_steps
    scan_steps = int(steps_scan.get('1.0', 'end-1c'))
    scan_length = float(screw_length.get('1.0', 'end-1c'))
    scan_popup = ScanPopup(root, scan_steps)
    scan_popup.open()
    # Use 1 laser, color, metric always
    Timer(0.1, start_scan).start()


def start_scan():
    mmps = scan_length / float(scan_steps)
    tps = mmps / pitch
    sps = tps * spr

    timestamp = strftime('%Y%m%d%H%M%S')
    scan_path = path.join(getcwd(), f"scans\\{timestamp}")  # create scans dir
    image_path = path.join(scan_path, "images")
    makedirs(image_path)

    save_details(scan_path,
                 {"date": timestamp,
                  "steps": scan_steps,
                  "ll": False,
                  "rl": True,
                  "color": True,
                  "type": "linear",
                  "dps": round(mmps, 2)})

    for s in range(0, scan_steps):
        if s > 0:
            pico.send_msg_new(6, 0, int(sps))  # turn platform
        save_pic(f'{image_path}\\color_%04d.jpg' % s)
        pico.send_msg_new(2)
        # sleep(1.0)
        save_pic(f'{image_path}\\right_%04d.jpg' % s)
        pico.send_msg_new(1)
        step(s + 1)


tl = None
cal_cnt = 0


def calibrate_camera_clicked():
    if tl is not None:
        tl.destroy()
    Timer(0.1, run_calibrate_camera).start()


def calibration_clicked():
    if tl is not None:
        tl.destroy()
    Timer(0.1, run_calibration).start()


def run_calibrate_camera():
    global tl, camera_calibration
    d = getcwd() + "\\calibration\\webcam"
    if not path.isdir(d):
        makedirs(d)
    pico.send_msg_new(1)                                # Turn laser off
    save_pic(f'%s\\calibration_%s.jpg' % (d, 'C0'))     # take pic of pattern
    camera_calibration = CameraCalibration(d, reload=True)


def run_calibration():
    global tl, cal_cnt
    d = getcwd() + "\\calibration\\linear"
    if not path.isdir(d):
        makedirs(d)
    if cal_cnt == 0:
        # save_pic(f'%s\\calibration_%s.jpg' % (d, 'F0'))
        save_pic(f'%s\\calibration_%s.jpg' % (d, 'F0'))
        pico.send_msg_new(2)
        # sleep(1.0)
        save_pic(f'%s\\calibration_%s.jpg' % (d, 'F1'))
        pico.send_msg_new(1)
        tl = Toplevel()
        tl.geometry('200x100+100+450')
        lb = Label(tl, text='Move pattern to back.')
        lb.pack(pady=(20, 0))
        cb = Button(tl, text="Continue", command=calibration_clicked, width=15)
        cb.pack(pady=(10, 0))
        tl.grab_set()
        cal_cnt += 1
    else:
        save_pic(f'%s\\calibration_%s.jpg' % (d, 'B0'))
        pico.send_msg_new(2)
        sleep(1.0)
        save_pic(f'%s\\calibration_%s.jpg' % (d, 'B1'))
        pico.send_msg_new(1)
        cal_cnt = 0


def step(s):
    if s == -1:
        scan_popup.error("ERROR:\nPico not connected.\nConnect pico and try again.")
    else:
        scan_popup.step(s)


def scan_complete():
    tmp = 1


def stop_scan():
    # TODO stop scans
    tmp = 1


def move_left_click():
    Timer(0.2, move_left).start()


def move_right_click():
    Timer(0.2, move_right).start()


def move_right():
    mm = float(mv_turns.get('1.0', 'end-1c'))
    steps = mm / pitch * spr
    pico.send_msg_new(6, 1, int(steps))  # turn platform


def move_left():
    mm = float(mv_turns.get('1.0', 'end-1c'))
    steps = mm / pitch * spr
    pico.send_msg_new(6, 0, int(steps))  # turn platform


def laser_one():
    if laser_one_button['relief'] == 'raised':
        pico.send_msg_new(2)
        laser_one_button.config(bg="#EC7063")
        laser_one_button['relief'] = 'sunken'
    else:
        pico.send_msg_new(1)
        laser_one_button.config(bg="SystemButtonFace")
        laser_one_button['relief'] = 'raised'


def pico_connect():
    if pico.connected:
        pico.close()
    else:
        com = pico_port_field.get('1.0', 'end-1c')
        pico.com = com
        try:
            pico.open()
        except Exception as e:
            print(str(e))
    arduino_con_bt['text'] = '-' if pico.connected else '+'
    if pico.connected:
        arduino_con_bt.config(bg="#EC7063")
        arduino_con_bt['relief'] = 'sunken'
    else:
        arduino_con_bt.config(bg="SystemButtonFace")
        arduino_con_bt['relief'] = 'raised'


cam_url = 'http://192.168.0.23:8080'
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

        if h > 640:
            r = float(h)/640.0
            w = int(float(w) / r)
            h = int(float(h) / r)
            cv2image = cv2.resize(cv2image, (w, h), interpolation=cv2.INTER_AREA)
        cv2image = cv2.line(cv2image, (int(w / 2), 0), (int(w / 2), h), [0, 0, 255], 1)
        cv2image = cv2.line(cv2image, (0, int(h / 2)), (w, int(h / 2)), [0, 0, 255], 1)
        # Convert image to PhotoImage
        try:
            cv2image = cv2.cvtColor(cv2image, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            lmain.imgtk = imgtk
            lmain.configure(image=imgtk)
        except _tkinter.TclError or RuntimeError as e:
            print('Error: ', str(e))
        # Repeat after an interval to capture continiously
    lmain.after(100, show_webcam)


img_num = 0


def save_pic(f=None, use_cam=True):
    if webcam:
        sleep(0.5)
        while True:
            ret, src = cam.read()
            if ret:
                h, w, _ = src.shape
                if w > h:
                    src = cv2.rotate(src, cv2.ROTATE_90_COUNTERCLOCKWISE)
                cv2.imwrite(f, src)
                break
            else:
                sleep(0.5)
    elif use_cam:
        sleep(4.5)
        img = curr_img
        if f is None:
            f = "%s\\scans\\pics\\%04d.jpg" % (getcwd(), img_num)
        cv2.imwrite(f, img)
    else:
        sleep(1.0)
        take_pic(f=f)


def take_pic(f=None, focus=False):
    global img_num
    #request.urlopen('http://192.168.0.11:8080/focus')
    if focus or img_num == 0:
        print('photoaf')
        req = request.urlopen(f'{cam_url}/photo.jpg')
    else:
        print('photo')
        req = request.urlopen(f'{cam_url}/photo.jpg')
    # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
    img = cv2.imdecode(arr, -1)  # 'Load it as it is'
    img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    if f is None:
        f = "%s\\scans\\pics\\%04d.jpg" % (getcwd(), img_num)
    cv2.imwrite(f, img)
    img_num += 1


if __name__ == '__main__':
    root = HdpiTk()
    # root = Tk()
    root.grid_rowconfigure(0, weight=1)  # this needed to be added
    root.grid_columnconfigure(0, weight=1)  # as did this

    root.title("Linear Scanner")
    # root.geometry("960x540")
    # Create a frame
    # root.columnconfigure(0, weight=1)
    # root.columnconfigure(1, weight=1)

    mn = Frame(root)
    mn.columnconfigure(0, weight=1)
    mn.columnconfigure(1, weight=1)

    mn_row = -1

    mn_row += 1
    label = Label(mn, text="Scanner Setup", font=font_bold)
    label.grid(columnspan=2, column=0, row=mn_row, sticky=W, pady=(20, 0))
    arduino_con_bt = Button(mn, text="+", width=3, command=pico_connect)
    arduino_con_bt.grid(column=1, row=mn_row, sticky=E)
    mn_row += 1
    label = Label(mn, text="PICO Port:")
    label.grid(column=0, row=mn_row, padx=(10, 0), pady=3, sticky=W)
    pico_port_field = Text(mn, width=5, height=1)
    pico_port_field.insert('1.0', pico_port)
    pico_port_field.grid(column=1, row=mn_row, padx=(10, 10), sticky=W)
    mn_row += 1
    label = Label(mn, text="Scan Length:")
    label.grid(column=0, row=mn_row, padx=(10, 0), pady=3, sticky=W)
    screw_length = Text(mn, width=3, height=1)
    screw_length.insert('1.0', '280')
    screw_length.grid(column=1, row=mn_row, padx=(10, 10), sticky=W)
    mn_row += 1
    label = Label(mn, text="Steps/Scan:")
    label.grid(column=0, row=mn_row, padx=(10, 0), pady=3, sticky=W)
    steps_scan = Text(mn, width=3, height=1)
    steps_scan.insert('1.0', '140')
    steps_scan.grid(column=1, row=mn_row, padx=(10, 10), sticky=W)
    mn_row += 1
    fr = Frame(mn)
    mv_left_button = Button(fr, text="<-", command=move_left_click, width=5)
    mv_left_button.grid(column=0, row=0, pady=3)
    mv_turns = Text(fr, width=4, height=1)
    mv_turns.insert('1.0', '5')
    mv_turns.grid(column=1, row=0, padx=(10, 10))
    mv_right_button = Button(fr, text="->", command=move_right_click, width=5)
    mv_right_button.grid(column=2, row=0, pady=3)
    fr.grid(column=0, columnspan=2, row=mn_row)
    mn_row += 1
    label = Label(mn, text="Camera ID:")
    label.grid(column=0, row=mn_row, padx=(10, 0), pady=3, sticky=W)
    camera_id = Text(mn, width=3, height=1)
    camera_id.insert('1.0', '1')
    camera_id.grid(column=1, row=mn_row, padx=(10, 10), sticky=W)

    mn_row += 1
    config_label = Label(mn, text="Laser Control", font=font_bold)
    config_label.grid(columnspan=2, column=0, row=mn_row, sticky=W, pady=(20, 0))

    mn_row += 1
    on_off_label = Label(mn, text="On/Off:")
    on_off_label.grid(column=0, row=mn_row, padx=(10, 0), sticky=W)
    laser_one_button = Button(mn, text="L1", command=laser_one, font=font_bold, width=5)
    laser_one_button.grid(column=1, row=mn_row, padx=(10, 0), sticky=W)

    # f1 = Frame(mn, pady=10)
    # f1.columnconfigure(0, weight=1)
    # f1.columnconfigure(1, weight=1)

    mn_row += 1
    config_label = Label(mn, text="Calibrate", font=font_bold)
    config_label.grid(columnspan=2, column=0, row=mn_row, sticky=W, pady=(20, 0))

    mn_row += 1
    but_start = Button(mn, text="Scalar", command=calibration_clicked, font=font_bold, width=10)
    but_start.grid(column=0, columnspan=1, row=mn_row, padx=(0, 5), pady=(0, 0))
    but_start = Button(mn, text="Camera", command=calibrate_camera_clicked, font=font_bold, width=10)
    but_start.grid(column=1, columnspan=1, row=mn_row, padx=(5, 0), pady=(0, 0))

    mn_row += 1
    but_start = Button(mn, text="Start Scan", command=scan_clicked, font=font_bold, width=10)
    but_start.grid(column=0, columnspan=2, row=mn_row, padx=(0, 10), pady=(20, 0))

    mn_row += 1
    but_start = Button(mn, text="Take Pic", command=take_pic, font=font_bold, width=10)
    but_start.grid(column=0, columnspan=2, row=mn_row, padx=(0, 10), pady=(20, 0))

    mn_row += 1
    mn.grid(column=0, row=0, padx=10, pady=(0, 10))

    # Create a label in the frame
    lmain = Label(root)
    lmain.grid(column=1, row=0)

    webcam = True
    if webcam:
        p = getcwd() + "\\calibration\\webcam"
        if path.isfile(p + "\\calibration_C0.jpg"):
            camera_calibration = CameraCalibration(p)
        else:
            camera_calibration = CameraCalibration(wd=None)

        cam = cv2.VideoCapture(cam_id, cv2.CAP_DSHOW)
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    else:
        camera_calibration = CameraCalibration(wd=None)
        cam = cv2.VideoCapture(f'{cam_url}/video')
        request.urlopen(f'{cam_url}/focus')

    show_webcam()

    scan_popup = ScanPopup(root, 0)
    # scan = LinearScan()

    root.mainloop()
