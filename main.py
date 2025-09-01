# main.py (ROBUST CAMERA CHECK VERSION)
import cv2
import numpy as np
import mediapipe as mp
import time
import random
import asyncio
from bleak import BleakClient

# --- Configuration is the same ---
CONFIG = {
    "camera_index": 0,
    "camera_resolution": (640, 480),
    "calibration_file": "calibration_data.npz",
    "toio_addresses": [
        "EB:69:D3:D2:C1:9A", "C3:6B:4A:1F:C1:57",
        "F1:4C:2F:5F:54:4A", "CB:7D:4C:24:58:4B",
    ],
    "toio_motor_char_uuid": "10b20102-5b3b-4571-9508-cf3efcd7bbae",
    "physical_area_mm": (300, 300),
    "agency_min_time_s": 5.0,
    "agency_max_time_s": 10.0,
}

# --- Helper Classes ---

class FisheyeCamera:
    def __init__(self, index, resolution, calib_file):
        self.cap = cv2.VideoCapture(index)
        # --- NEW, ROBUST CHECK ---
        if not self.cap.isOpened():
            # This will stop the program immediately if the camera fails
            raise IOError(f"Cannot open camera at index {index}. It might be in use by another program.")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        self.K, self.D = None, None
        self._load_calibration(calib_file)

    # ... (The rest of the FisheyeCamera class is the same) ...
    def _load_calibration(self, file_path):
        try:
            with np.load(file_path) as data: self.K, self.D = data['K'], data['D']
            print("[OK] Successfully loaded camera calibration data.")
        except FileNotFoundError: print("[ERROR] Calibration file not found.")
    def read(self):
        ret, frame = self.cap.read()
        if not ret: return None, None
        if self.K is not None and self.D is not None:
            undistorted = cv2.fisheye.undistortImage(frame, self.K, self.D, Knew=self.K)
            return frame, undistorted
        return frame, frame
    def release(self): self.cap.release()

# --- (All other helper classes are exactly the same) ---
class HandTracker:
    def __init__(self, min_detection_confidence=0.7):
        self.hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=min_detection_confidence)
        self.mp_drawing = mp.solutions.drawing_utils
    def find_hand_landmarks(self, image):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return self.hands.process(image_rgb)
    def draw_landmarks(self, image, results):
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks: self.mp_drawing.draw_landmarks(image, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
        return image

class ToioController:
    def __init__(self, addresses, motor_uuid):
        self.addresses = addresses
        self.motor_uuid = motor_uuid
        self.clients = {}
    async def connect(self):
        print("[INFO] Starting Toio connection process...")
        for address in self.addresses:
            print(f"[INFO] Attempting to connect to {address}...")
            client = BleakClient(address)
            try:
                await client.connect(timeout=10.0)
                if client.is_connected:
                    self.clients[address] = client
                    print(f"  [OK] Successfully connected to {address}")
            except Exception as e: print(f"  [ERROR] Failed to connect to {address}: {e}")
        print(f"[INFO] Connection process finished. {len(self.clients)} robots connected.")
        return len(self.clients) > 0
    async def disconnect(self):
        for address, client in self.clients.items():
            if client.is_connected: await client.disconnect()
        print("[INFO] All Toios disconnected.")
    async def send_motor_command(self, address, command):
        if address in self.clients and self.clients[address].is_connected:
            try: await self.clients[address].write_gatt_char(self.motor_uuid, bytearray(command))
            except Exception as e: print(f"  [ERROR] sending command to {address}: {e}")
    async def move_robot_to_target(self, address, target_pos):
        move_forward_cmd = [0x01, 0x01, 0x01, 0x32, 0x02, 0x01, 0x32]
        await self.send_motor_command(address, move_forward_cmd)
        await asyncio.sleep(0.1)
        stop_cmd = [0x01, 0x01, 0x01, 0x00, 0x02, 0x01, 0x00]
        await self.send_motor_command(address, stop_cmd)

class SharedAgencyManager:
    def __init__(self, min_time, max_time):
        self.states, self.current_state = ["USER_CONTROL", "MACHINE_AUTONOMOUS"], "USER_CONTROL"
        self.min_time, self.max_time = min_time, max_time
        self.last_switch_time = time.time()
        self.current_duration = random.uniform(self.min_time, self.max_time)
    def update(self):
        if time.time() - self.last_switch_time > self.current_duration:
            self.current_state = self.states[1 - self.states.index(self.current_state)]
            self.last_switch_time = time.time()
            self.current_duration = random.uniform(self.min_time, self.max_time)
            print(f"[STATE] Agency switched to: {self.current_state}")
    def get_state(self): return self.current_state

async def main():
    camera = None # Define camera here so finally block can access it
    toio_controller = None # Define controller here for same reason
    try:
        print("[INIT] Script starting...")
        # --- NEW: Graceful error handling for camera ---
        try:
            camera = FisheyeCamera(CONFIG["camera_index"], CONFIG["camera_resolution"], CONFIG["calibration_file"])
            print("[INIT] Camera initialized.")
        except IOError as e:
            print(f"\n[FATAL] A critical error occurred with the camera: {e}")
            print("[FATAL] Please check if the camera is connected or reboot the Pi.")
            return # Exit the script

        hand_tracker = HandTracker()
        toio_controller = ToioController(CONFIG["toio_addresses"], CONFIG["toio_motor_char_uuid"])
        agency_manager = SharedAgencyManager(CONFIG["agency_min_time_s"], CONFIG["agency_max_time_s"])
        
        await toio_controller.connect()
        if len(toio_controller.clients) == 0:
            print("\n[FATAL] No Toio robots were connected. Exiting.")
            return

        print("[INFO] Entering main loop...")
        while True:
            raw_frame, frame = camera.read()
            if frame is None:
                print("[WARN] Camera frame is empty. Exiting loop.")
                break
            
            results = hand_tracker.find_hand_landmarks(frame)
            if results.multi_hand_landmarks:
                agency_manager.update()
                state = agency_manager.get_state()
                if state == "USER_CONTROL":
                    wrist = results.multi_hand_landmarks[0].landmark[0]
                    target_x = np.interp(wrist.x, [0, 1], [0, CONFIG["physical_area_mm"][0]])
                    target_y = np.interp(wrist.y, [0, 1], [0, CONFIG["physical_area_mm"][1]])
                    targets = [(target_x, target_y) for _ in toio_controller.clients]
                else:
                    targets = [(random.uniform(0, CONFIG["physical_area_mm"][0]), random.uniform(0, CONFIG["physical_area_mm"][1])) for _ in toio_controller.clients]
                
                move_tasks = [toio_controller.move_robot_to_target(addr, tgt) for addr, tgt in zip(toio_controller.clients.keys(), targets)]
                await asyncio.gather(*move_tasks)
            
            debug_frame = hand_tracker.draw_landmarks(frame.copy(), results)
            cv2.putText(debug_frame, agency_manager.get_state(), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.imshow("Hands Arcade V2 - Debug", debug_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'): break
    finally:
        print("[INFO] Cleaning up and shutting down...")
        if camera: camera.release()
        if toio_controller: await toio_controller.disconnect()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    asyncio.run(main())
