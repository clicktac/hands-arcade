import cv2
import numpy as np

class CameraServer:
    def __init__(self, calib_file="data/calibration_data.npz", device=0):
        self.cap = cv2.VideoCapture(device)
        data = np.load(calib_file)
        self.mtx = data['mtx']
        self.dist = data['dist']

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        h, w = frame.shape[:2]
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(self.mtx, self.dist, (w,h), 1, (w,h))
        dst = cv2.undistort(frame, self.mtx, self.dist, None, newcameramtx)
        return dst
