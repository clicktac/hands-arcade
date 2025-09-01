import cv2

# The index '0' is usually the first USB camera.
# If this doesn't work, try '1' or '2'.
CAMERA_INDEX = 0

print("Attempting to open camera...")
# Create a video capture object
cap = cv2.VideoCapture(CAMERA_INDEX)

# Check if the camera opened successfully
if not cap.isOpened():
    print(f"Error: Could not open camera at index {CAMERA_INDEX}.")
    print("Please check if the camera is plugged in correctly.")
    exit()

print("Camera opened successfully! Displaying feed.")
print("Press 'q' on your keyboard to quit.")

# Loop forever to read frames from the camera
while True:
    # Read one frame
    ret, frame = cap.read()

    # 'ret' will be False if the frame could not be read
    if not ret:
        print("Error: Can't receive frame (stream end?). Exiting ...")
        break

    # Display the resulting frame in a window
    cv2.imshow('Camera Test - Press Q to Quit', frame)

    # Wait for the 'q' key to be pressed to exit the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the camera and close windows
print("Closing camera...")
cap.release()
cv2.destroyAllWindows()
