import cv2
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=str, default="capture.mp4")
    parser.add_argument("--device", type=int, default=0)
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.device)
    if not cap.isOpened():
        raise RuntimeError("Camera not found.")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(args.out, fourcc, 30.0, (640, 480))

    print("Press q to stop recording...")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("capture", frame)
        out.write(frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
