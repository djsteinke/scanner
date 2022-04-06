
import numpy as np

import sys
import optparse
import cv2
import os
import math
import time

from math import *
import glob
from os import getcwd

from model.pointset import *
from model.parser_tmp import *


def main():

    right = []
    scan_folder = "20220406081736"
    path = getcwd() + "\\scan\\" + scan_folder
    filename = f'{path}\\{scan_folder}.xyz'

    # print "Scanning %s for files" % path

    right = glob.glob("%s/right*" % path.rstrip('/'))
    right.sort()

    steps = len(right)

    print("I: processing %d steps" % steps)

    right = parse_images(right)

    print("I: Writing pointcloud to %s" % filename)

    # TODO write XYZ file
    output_asc_pointset(filename, right)


if __name__ == "__main__":
    main()
