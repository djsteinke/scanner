import threading
import cv2
from os import getcwd
from time import sleep, strftime
from tkinter import *
from tkinter.messagebox import showinfo

from PIL import ImageTk, Image

from arduino import Arduino
from scan import Scan

cam_id = 0
arduino = Arduino(speed=38400)

# 200 steps/rev
# turn table 4 steps / pic

steps = 5

cam_h = 720
cam_w = 1280
cam_mid_h = 360
cam_mid_w = 640

vl_s = (cam_mid_w, 0)
vl_e = (cam_mid_w, cam_h)
hl_s = (0, cam_mid_h)
hl_e = (cam_w, cam_mid_h)

# Capture from camera

codec = 0x47504A4D # MJPG
cap = cv2.VideoCapture(cam_id, cv2.CAP_ANY)
# cap.set(cv2.CAP_PROP_FPS, 15.0)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_w)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_h)
print(f'EXPOSURE: {cap.get(cv2.CAP_PROP_EXPOSURE)}')
print(f'FPS: {cap.get(cv2.CAP_PROP_FPS)}')
print(f'Saturation: {cap.get(cv2.CAP_PROP_SATURATION)}')

arduino_com = "COM4"

scanning = False
step = 0
connected = False

saturation_spinbox = None
contrast_spinbox = None
brightness_spinbox = None
saturation = cap.get(cv2.CAP_PROP_SATURATION)
contrast = cap.get(cv2.CAP_PROP_CONTRAST)
brightness = cap.get(cv2.CAP_PROP_BRIGHTNESS)

but_start = None
but_cancel = None
root = None

rotate_image = False

laser_one = False
laser_two = False


def get_timestamp():
    return strftime("%Y%m%d%H%M%S")


def laser_one_control():
    global laser_one
    laser_one = not laser_one
    if laser_one:
        laser_one_button.config(bg="#EC7063")
        laser_one_button['relief'] = 'sunken'
        arduino.send_msg("L11")
    else:
        laser_one_button.config(bg="SystemButtonFace")
        laser_one_button['relief'] = 'raised'
        arduino.send_msg("L10")


def laser_two_control():
    global laser_two
    laser_two = not laser_two
    if laser_two:
        laser_two_button.config(bg="#EC7063")
        laser_two_button['relief'] = 'sunken'
        arduino.send_msg("L21")
    else:
        laser_two_button.config(bg="SystemButtonFace")
        laser_two_button['relief'] = 'raised'
        arduino.send_msg("L20")


def flip_image():
    global rotate_image
    rotate_image = not rotate_image


def set_saturation_ret(event):
    set_saturation()


def set_saturation():
    global saturation
    if saturation_spinbox is not None:
        saturation = float(saturation_spinbox.get())
        print(f'set_saturation[{saturation}]')
        cap.set(cv2.CAP_PROP_SATURATION, saturation)


def set_contrast_ret(event):
    set_contrast()


def set_contrast():
    global contrast
    if contrast_spinbox is not None:
        contrast = float(contrast_spinbox.get())
        print(f'set_contrast[{contrast}]')
        cap.set(cv2.CAP_PROP_CONTRAST, contrast)


def set_brightness_ret(event):
    set_brightness()


def set_brightness():
    global brightness
    if brightness_spinbox is not None:
        brightness = float(brightness_spinbox.get())
        print(f'set_brightness[{brightness}]')
        cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)


def button_test():
    print('Button click')


def video_stream():
    res, fr = cap.read()
    line_color = (0, 0, 255)  # RED color in BGR
    line_thickness = 1
    fr = cv2.line(fr, vl_s, vl_e, line_color, line_thickness)
    fr = cv2.line(fr, hl_s, hl_e, line_color, line_thickness)
    fr = cv2.resize(fr, (cam_mid_w, cam_mid_h), interpolation=cv2.INTER_LINEAR_EXACT)
    cv2image = cv2.cvtColor(fr, cv2.COLOR_BGR2RGBA)
    img = Image.fromarray(cv2image)
    imgtk = ImageTk.PhotoImage(image=img)
    lmain.imgtk = imgtk
    lmain.configure(image=imgtk)
    lmain.after(1, video_stream)


def start_scan():
    if but_start is not None and but_cancel is not None:
        but_start['state'] = 'disabled'
        but_cancel['state'] = 'normal'
    scan = Scan(cap, arduino, getcwd(), s=5, c=scan_complete)
    thread = threading.Timer(0.1, scan.start)
    thread.start()


def next_step():
    global step
    if step <= steps:
        if connected:
            step += 1
            print(f'step{step}')
            motor_steps = 200*16/steps
            arduino.send_msg(f"STEP:{motor_steps}:CW")
            #ArduinoMessage(arduino, "step", msg_counter.get_next(), next_step).send()
    else:
        print("Scan complete.")


def scan_complete():
    if but_start is not None and but_cancel is not None:
        sleep(3)
        if root is not None:
            showinfo(message="Scan complete.", parent=root)

        but_start['state'] = 'normal'
        but_cancel['state'] = 'disabled'


font = "arial 9"
font_bold = font + " bold"


if __name__ == '__main__':
    arduino.open()

    if not cap.isOpened():
        raise IOError("Cannot open webcam")

    root = Tk()
    root.title("Scanner")
    # root.geometry("960x540")
    # Create a frame
    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=1)

    mn = Frame(root)
    mn.columnconfigure(0, weight=1)
    mn.columnconfigure(1, weight=1)

    mn_row = -1

    mn_row += 1
    config_label = Label(mn, text="Camera Control", font=font_bold)
    config_label.grid(columnspan=2, column=0, row=mn_row, sticky=W)

    mn_row += 1
    but_start = Button(mn, text="Run configure", command=())
    but_start.grid(column=0, row=mn_row, padx=10, sticky=W)

    mn_row += 1
    saturation_label = Label(mn, text="Saturation:")
    saturation_label.grid(column=0, row=mn_row, sticky=W, pady=3, padx=(10, 0))
    saturation_spinbox = Spinbox(mn, from_=0, to=100, width=10, textvariable=StringVar(value=int(saturation)),
                                 command=set_saturation)
    saturation_spinbox.grid(column=1, row=mn_row, sticky=E)
    saturation_spinbox.bind('<Return>', set_saturation_ret)

    mn_row += 1
    brightness_label = Label(mn, text="Brightness:")
    brightness_label.grid(column=0, row=mn_row, sticky=W, pady=3, padx=(10, 0))
    brightness_spinbox = Spinbox(mn, from_=0, to=100, width=10, textvariable=StringVar(value=int(brightness)),
                                 command=set_brightness)
    brightness_spinbox.grid(column=1, row=mn_row, sticky=E)
    brightness_spinbox.bind('<Return>', set_brightness_ret)

    mn_row += 1
    contrast_label = Label(mn, text="Contrast:")
    contrast_label.grid(column=0, row=mn_row, sticky=W, pady=3, padx=(10, 0))
    contrast_spinbox = Spinbox(mn, from_=0, to=100, width=10, textvariable=StringVar(value=int(contrast)),
                               command=set_contrast)
    contrast_spinbox.grid(column=1, row=mn_row, sticky=E)
    contrast_spinbox.bind('<Return>', set_contrast_ret)

    mn_row += 1
    config_label = Label(mn, text="Laser Control", font=font_bold)
    config_label.grid(columnspan=2, column=0, row=mn_row, sticky=W, pady=(20, 0))

    mn_row += 1
    on_off_label = Label(mn, text="On/Off:")
    on_off_label.grid(column=0, row=mn_row, padx=(10, 0), sticky=W)
    laser_one_button = Button(mn, text="  L  ", command=laser_one_control, font=font_bold)
    laser_one_button.grid(column=1, row=mn_row, sticky=W)
    laser_two_button = Button(mn, text="  R  ", command=laser_two_control, font=font_bold)
    laser_two_button.grid(column=1, row=mn_row, sticky=E)

    """
        mn_row += 1
        rotate_checkbox = Checkbutton(mn, text="Vertical Image", command=flip_image)
        rotate_checkbox.grid(columnspan=2, column=0, row=mn_row, sticky=W)
    """
    mn_row += 1
    mn.grid(column=0, row=0, padx=10, pady=10, sticky=N)
    #f1 = Frame(mn, pady=10)
    #f1.columnconfigure(0, weight=1)
    #f1.columnconfigure(1, weight=1)

    bottom = Frame(root)
    but_start = Button(bottom, text="Start Scan", command=start_scan)
    but_start.grid(column=0, row=0, padx=10)
    but_cancel = Button(bottom, text="Cancel Scan", command=button_test)
    but_cancel.grid(column=1, row=0, padx=10)
    but_cancel['state'] = "disabled"
    #f1.grid(column=0, row=mn_row)
    bottom.grid(column=0, row=0, padx=10, pady=10, sticky=S)

    # Create a label in the frame
    lmain = Label(root)
    lmain.grid(column=1, row=0)

    video_stream()
    root.mainloop()

    cap.release()
    cv2.destroyAllWindows()
    exit()




