import cv2


def get_roi_by_path(path, ratio):
    xroi = [0, 0]
    yroi = [0, 0]
    img = cv2.imread(path)
    h, w, c = img.shape
    shrink = 6
    h_tmp = int(h / shrink)
    w_tmp = int(w / shrink)
    roi = cv2.resize(img, (w_tmp, h_tmp), interpolation=cv2.INTER_LINEAR_EXACT)
    r = cv2.selectROI("ROI", roi)
    xroi[0] = int(r[0]) * shrink
    xroi[1] = int(r[0] + r[2]) * shrink
    yroi[0] = int(r[1]) * shrink
    yroi[1] = int(r[1] + r[3]) * shrink
    print('ROI')
    print(xroi, yroi)
    cv2.destroyWindow("ROI")
    return [int(xroi[0] / ratio), int(xroi[1] / ratio)], [int(yroi[0] / ratio), int(yroi[1] / ratio)]


def get_roi_by_img(img, ratio):
    xroi = [0, 0]
    yroi = [0, 0]
    h, w, c = img.shape
    shrink = 6
    h_tmp = int(h / shrink)
    w_tmp = int(w / shrink)
    roi = cv2.resize(img, (w_tmp, h_tmp), interpolation=cv2.INTER_LINEAR_EXACT)
    r = cv2.selectROI("ROI", roi)
    xroi[0] = int(r[0]) * shrink
    xroi[1] = int(r[0] + r[2]) * shrink
    yroi[0] = int(r[1]) * shrink
    yroi[1] = int(r[1] + r[3]) * shrink
    print('ROI[x, y]', xroi, yroi)
    cv2.destroyWindow("ROI")
    return [int(xroi[0] / ratio), int(xroi[1] / ratio)], [int(yroi[0] / ratio), int(yroi[1] / ratio)]
