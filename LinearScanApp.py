from tkinter import *
from tkinter.ttk import Progressbar
from threading import Timer
from android import Android
from arduino import Arduino
from collapsible_pane import CollapsiblePane
from linear_scan import LinearScan
from subprocess import run
from os import getcwd, makedirs
from os.path import isdir
from scan_popup import ScanPopup
from hdpitkinter import HdpiTk

cam_id = 0
arduino_com = "COM3"
arduino = Arduino(com='COM3', speed=9600)

scanning = False
connected = False
android = Android()
android_connected = False
popup = None

font = "arial 9"
font_bold = font + " bold"


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


def scan_clicked():
    global scan_popup, scan
    scan_steps = int(steps_scan.get('1.0', 'end-1c'))
    pitch = float(screw_pitch.get('1.0', 'end-1c'))
    length = float(screw_length.get('1.0', 'end-1c'))
    scan_popup = ScanPopup(root, scan_steps)
    scan_popup.open()
    ll = use_left_laser.get() == 1
    rl = use_right_laser.get() == 1
    color = use_color.get() == 1
    metric = use_metric.get() == 1
    scan = LinearScan(arduino=arduino, android=android, d=getcwd(), s=scan_steps, c=scan_complete, sc=step, pitch=pitch,
                      length=length, rl=rl, ll=ll, metric=metric, color=color)
    Timer(0.1, scan.start).start()


def calibration_clicked():
    d = getcwd() + "\\calibration"
    if not isdir(d):
        makedirs(d)
    android.take_picture(d + "\\linear_calibration_0000.jpg")


def step(s):
    if s == -1:
        scan_popup.error("ERROR:\nArduino not connected.\nConnect arduino and try again.")
    else:
        scan_popup.step(s)


def scan_complete():
    tmp = 1


def stop_scan():
    # TODO stop scans
    tmp = 1


def move_right():
    turns = float(mv_turns.get('1.0', 'end-1c'))
    motor_steps = int(400 * turns)
    arduino.send_msg_new(6, 1, motor_steps)         # turn platform
    # arduino.send_msg(f"STEP:{motor_steps}:CCW")     # turn platform


def move_left():
    turns = float(mv_turns.get('1.0', 'end-1c'))
    motor_steps = int(400 * turns)
    arduino.send_msg_new(6, 0, motor_steps)         # turn platform
    #arduino.send_msg(f"STEP:{motor_steps}:CW")  # turn platform


def laser_one():
    if laser_one_button['relief'] == 'raised':
        #arduino.send_msg("L11")
        arduino.send_msg_new(2)
        laser_one_button.config(bg="#EC7063")
        laser_one_button['relief'] = 'sunken'
    else:
        #arduino.send_msg("L10")
        arduino.send_msg_new(1)
        laser_one_button.config(bg="SystemButtonFace")
        laser_one_button['relief'] = 'raised'


def laser_two():
    if laser_two_button['relief'] == 'raised':
        #arduino.send_msg("L21")
        arduino.send_msg_new(4)
        laser_two_button.config(bg="#EC7063")
        laser_two_button['relief'] = 'sunken'
    else:
        #arduino.send_msg("L20")
        arduino.send_msg_new(3)
        laser_two_button.config(bg="SystemButtonFace")
        laser_two_button['relief'] = 'raised'


def arduino_connect():
    if arduino.connected:
        arduino.close()
    else:
        try:
            arduino.open()
        except Exception as e:
            print(str(e))
    arduino_con_bt['text'] = '-' if arduino.connected else '+'
    if arduino.connected:
        arduino_con_bt.config(bg="#EC7063")
        arduino_con_bt['relief'] = 'sunken'
        r = rpm.get('1.0', 'end-1c')
        #arduino.send_msg(f'RPM:{r}')
        arduino.send_msg_new(5, 0, r)
    else:
        arduino_con_bt.config(bg="SystemButtonFace")
        arduino_con_bt['relief'] = 'raised'


if __name__ == '__main__':
    #arduino.open()

    #root = HdpiTk()
    root = Tk()
    root.grid_rowconfigure(0, weight=1)  # this needed to be added
    root.grid_columnconfigure(0, weight=1)  # as did this

    root.title("Linear Scanner")
    # root.geometry("960x540")
    # Create a frame
    #root.columnconfigure(0, weight=1)
    #root.columnconfigure(1, weight=1)

    mn = Frame(root)
    mn.columnconfigure(0, weight=1)
    mn.columnconfigure(1, weight=1)

    mn_row = -1

    mn_row += 1
    label = Label(mn, text="Scanner Setup", font=font_bold)
    label.grid(columnspan=2, column=0, row=mn_row, sticky=W, pady=(20, 0))
    arduino_con_bt = Button(mn, text="+", width=3, command=arduino_connect)
    arduino_con_bt.grid(column=1, row=mn_row, sticky=E)
    use_metric = IntVar(value=1)
    mn_row += 1
    label = Label(mn, text="Metric:")
    label.grid(column=0, row=mn_row, padx=(10, 0), pady=3, sticky=W)
    metric_cb = Checkbutton(mn, variable=use_metric)
    metric_cb.grid(column=1, row=mn_row, padx=(5, 0), sticky=W)
    mn_row += 1
    label = Label(mn, text="Screw Pitch:")
    label.grid(column=0, row=mn_row, padx=(10, 0), pady=3, sticky=W)
    screw_pitch = Text(mn, width=3, height=1)
    screw_pitch.insert('1.0', '2')
    screw_pitch.grid(column=1, row=mn_row, padx=(10, 10), sticky=W)
    mn_row += 1
    label = Label(mn, text="Screw Length:")
    label.grid(column=0, row=mn_row, padx=(10, 0), pady=3, sticky=W)
    screw_length = Text(mn, width=3, height=1)
    screw_length.insert('1.0', '300')
    screw_length.grid(column=1, row=mn_row, padx=(10, 10), sticky=W)
    mn_row += 1
    label = Label(mn, text="Steps/Scan:")
    label.grid(column=0, row=mn_row, padx=(10, 0), pady=3, sticky=W)
    steps_scan = Text(mn, width=3, height=1)
    steps_scan.insert('1.0', '150')
    steps_scan.grid(column=1, row=mn_row, padx=(10, 10), sticky=W)
    mn_row += 1
    label = Label(mn, text="Speed (rpm):")
    label.grid(column=0, row=mn_row, padx=(10, 0), pady=3, sticky=W)
    rpm = Text(mn, width=3, height=1)
    rpm.insert('1.0', '10')
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
    fr = Frame(mn)
    mv_left_button = Button(fr, text="<-", command=move_left, width=5)
    mv_left_button.grid(column=0, row=0, pady=3)
    mv_turns = Text(fr, width=4, height=1)
    mv_turns.insert('1.0', '3')
    mv_turns.grid(column=1, row=0, padx=(10, 10))
    mv_right_button = Button(fr, text="->", command=move_right, width=5)
    mv_right_button.grid(column=2, row=0, pady=3)
    fr.grid(column=0, columnspan=2, row=mn_row)

    mn_row += 1
    config_label = Label(mn, text="Laser Control", font=font_bold)
    config_label.grid(columnspan=2, column=0, row=mn_row, sticky=W, pady=(20, 0))

    mn_row += 1
    on_off_label = Label(mn, text="On/Off:")
    on_off_label.grid(column=0, row=mn_row, padx=(10, 0), sticky=W)
    laser_one_button = Button(mn, text="L", command=laser_one, font=font_bold, width=5)
    laser_one_button.grid(column=1, row=mn_row, padx=(10, 0), sticky=W)
    laser_two_button = Button(mn, text="R", command=laser_two, font=font_bold, width=5)
    laser_two_button.grid(column=1, row=mn_row, padx=(80, 0), sticky=W)

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
    host_value4.insert('1.0', '37')
    host_value4.grid(column=6, row=0, padx=(0, 10))
    host_frame.grid(column=1, row=mn_row, padx=(10, 10), pady=3, sticky=W)

    mn_row += 1
    port_label = Label(mn, text="Port:")
    port_label.grid(column=0, row=mn_row, padx=(10, 0), pady=3, sticky=W)
    port_value = Text(mn, width=5, height=1)
    port_value.insert('1.0', '5555')
    port_value.grid(column=1, row=mn_row, padx=(10, 10), sticky=W)
    mn_row += 1
    connect_android = Button(mn, text="Connect", command=connect_android, width=10)
    connect_android.grid(column=0, columnspan=2, row=mn_row, padx=(0, 10), pady=3)
    #connect_android = Button(mn, text="Disconnect", command=laser_one_control, width=10)
    #connect_android.grid(column=1, row=mn_row, padx=(10, 10), sticky=EW)

    #f1 = Frame(mn, pady=10)
    #f1.columnconfigure(0, weight=1)
    #f1.columnconfigure(1, weight=1)

    mn_row += 1
    but_start = Button(mn, text="Calibration", command=calibration_clicked, font=font_bold, width=10)
    but_start.grid(column=0, columnspan=2, row=mn_row, padx=(0, 10), pady=(20, 0))

    mn_row += 1
    but_start = Button(mn, text="Start Scan", command=scan_clicked, font=font_bold, width=10)
    but_start.grid(column=0, columnspan=2, row=mn_row, padx=(0, 10), pady=(20, 0))

    mn_row += 1
    mn.pack(padx=10, pady=(0, 10))
    #mn.grid(column=0, row=0, padx=10, pady=10, sticky=N)

    #col = CollapsiblePane(root, "<", ">")
    #col.pack(expand=True)
    #col.grid(column=0, row=2)
    # Create a label in the frame
    lmain = Label(root)
    #lmain.grid(column=1, row=0)

    scan_popup = ScanPopup(root, 0)
    scan = LinearScan()

    root.mainloop()
