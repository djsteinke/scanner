import serial
from cv2 import VideoCapture, imshow, imwrite, waitKey, destroyWindow


cam_id = 0
arduino_com = "COM4"
arduino = serial.Serial(arduino_com, 115200, timeout=.1)

# 200 steps/rev
# turn table 4 steps / pic

steps = 50

if __name__ == '__main__':
    cam = VideoCapture(cam_id)
    result, image = cam.read()

    arduino.write("Hello from Python!")

    scanning = True
    step = 0

    while scanning:
        if step == steps:
            scanning = False
        # set platform 0 deg
        arduino.write("step")
        while True:
            data = arduino.readline()
            if data == "complete":
                result, image = cam.read()
                if result:
                    title = f"scan_{step}"
                    imshow(title, image)
                    imwrite(f"scan_{step}.png", image)
                    destroyWindow(title)
                break
        step += 1
