# hardware.py (Corrected Version)
import cv2
import numpy as np
import mediapipe as mp

class FisheyeCamera:
    def __init__(self, index, resolution, calib_file):
        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            raise IOError(f"Cannot open camera at index {index}.")
        # The fix is here: cv2 instead of cv
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        self.K, self.D = None, None
        self._load_calibration(calib_file)

    def _load_calibration(self, file_path):
        try:
            with np.load(file_path) as data:
                self.K, self.D = data['K'], data['D']
            print("[OK] Camera calibration data loaded.")
        except FileNotFoundError:
            print(f"[ERROR] Calibration file '{file_path}' not found.")

    def read(self):
        ret, frame = self.cap.read()
        if not ret:
            return None, None
        if self.K is not None and self.D is not None:
            undistorted_frame = cv2.fisheye.undistortImage(frame, self.K, self.D, Knew=self.K)
            return frame, undistorted_frame
        return frame, frame

    def release(self):
        self.cap.release()

class HandTracker:
    def __init__(self, min_detection_confidence=0.7):
        self.hands = mp.solutions.hands.Hands(
            max_num_hands=1,
            min_detection_confidence=min_detection_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils

    def find_hand_landmarks(self, image):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return self.hands.process(image_rgb)

    def draw_landmarks(self, image, results):
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    image, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS
                )
        return image