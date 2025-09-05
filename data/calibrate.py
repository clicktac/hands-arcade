# calibrate.py (Corrected Version)
import numpy as np
import cv2
import time

# --- Configuration ---
CHECKERBOARD = (6, 9) 
SQUARE_SIZE_MM = 20 

# --- Prepare object points ---
objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
objp = objp * SQUARE_SIZE_MM

# --- Arrays to store object points and image points from all the images. ---
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.

print("Starting camera... Point it at the checkerboard.")
print("Press 'c' to calibrate when you have enough captures (15-20 recommended).")
print("Press 'q' to quit.")

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

captured_frames = 0
last_capture_time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK + cv2.CALIB_CB_NORMALIZE_IMAGE)

    if ret == True:
        cv2.drawChessboardCorners(frame, CHECKERBOARD, corners, ret)
        if time.time() - last_capture_time > 2.0:
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
            imgpoints.append(corners2)
            
            captured_frames += 1
            last_capture_time = time.time()
            print(f"SUCCESS! Captured frame #{captured_frames}")

    cv2.putText(frame, f"Captures: {captured_frames}/15", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow('Calibration View - Press Q to Quit', frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('c') and captured_frames > 10:
        print("Calibrating... Please wait.")
        
        # ===================================================================
        # THE FIX IS HERE: Convert lists to the required NumPy array format
        # ===================================================================
        objpoints_np = np.array(objpoints, dtype=np.float32)
        imgpoints_np = np.array(imgpoints, dtype=np.float32)
        
        # We need to reshape the arrays to fit the function's expectations
        objpoints_np = objpoints_np.reshape(captured_frames, 1, -1, 3)
        imgpoints_np = imgpoints_np.reshape(captured_frames, 1, -1, 2)
        # ===================================================================

        K = np.zeros((3, 3))
        D = np.zeros((4, 1))
        
        try:
            ret, K, D, rvecs, tvecs = cv2.fisheye.calibrate(
                objpoints_np, # Use the corrected numpy array
                imgpoints_np, # Use the corrected numpy array
                gray.shape[::-1],
                K,
                D
            )
            
            if ret:
                print("Calibration successful!")
                np.savez("calibration_data.npz", K=K, D=D)
                print("Calibration data saved to calibration_data.npz")
                break
            else:
                print("Calibration failed internally. Try again with more/better captures.")

        except cv2.error as e:
            print(f"An OpenCV error occurred during calibration: {e}")
            print("This can happen with poor quality captures. Please try again.")

cap.release()
cv2.destroyAllWindows()
