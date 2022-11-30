import cv2
from tkinter import IntVar

#bright = IntVar(value=0)
#contrast = IntVar(value=0)


def apply_brightness_contrast(input_img, _bright=0, _contrast=0):
    #global bright, contrast
    #brightness = map(bright, 0, 510, -255, 255)
    #contrast = map(contrast, 0, 254, -127, 127)
    #_bright = bright.get()
    #_contrast = contrast.get()
    if _bright != 0:
        if _bright > 0:
            shadow = _bright
            highlight = 255
        else:
            shadow = 0
            highlight = 255 + _bright
        alpha_b = (highlight - shadow)/255
        gamma_b = shadow
        buf = cv2.addWeighted(input_img, alpha_b, input_img, 0, gamma_b)
    else:
        buf = input_img.copy()
    if _contrast != 0:
        f = float(131 * (_contrast + 127)) / (127 * (131 - _contrast))
        alpha_c = f
        gamma_c = 127*(1-f)
        buf = cv2.addWeighted(buf, alpha_c, buf, 0, gamma_c)
    cv2.putText(buf, 'B:{},C:{}'.format(_bright, _contrast), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    return buf
