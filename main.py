from time import sleep

import serial
import cv2


cam_id = 1
arduino_com = "COM4"
arduino = serial.Serial(arduino_com, 115200, timeout=.1)

# 200 steps/rev
# turn table 4 steps / pic

steps = 5

if __name__ == '__main__':
    cam = cv2.VideoCapture(cam_id, cv2.CAP_ANY)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    result, image = cam.read()
    cv2.imshow("test", image)
    cv2.waitKey()

    print('Wrote test.')
    scanning = True
    step = 0
    connected = False

    while scanning:
        print(f'step{step}')
        if step == steps:
            scanning = False
        # set platform 0 deg
        if connected:
            arduino.write(bytes("step", encoding="utf8"))
            print('step')
        while True:
            data = arduino.readline()
            strData = data.decode()
            if len(strData) > 0:
                print(f'rawData{strData}')
            if bytes("setup", encoding="utf8") in data:
                connected = True
                break

            if bytes("complete", encoding="utf8") in data:
                result, image = cam.read()
                if result:
                    title = f"scan_{step}"
                    cv2.imshow(title, image)
                    cv2.imwrite(f"scan_{step}.png", image)
                    cv2.destroyWindow(title)
                break
        step += 1
    cam.release()
    cv2.destroyAllWindows()
