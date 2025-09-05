# robot_navigation.py (With Mat-Based Navigation)
import asyncio
from bleak import BleakClient
from functools import partial
import numpy as np
import config

class ToioController:
    def __init__(self, addresses, motor_uuid, pos_id_uuid):
        self.addresses = addresses
        self.motor_uuid = motor_uuid
        self.pos_id_uuid = pos_id_uuid
        self.clients = {}
        self.robot_states = {
            addr: {"x": 0, "y": 0, "angle": 0, "updated": False} for addr in addresses
        }

    # --- NEW: Helper function to map our Playfield coordinates to Mat coordinates ---
    def _map_playfield_to_mat(self, playfield_x, playfield_y):
        """Converts a coordinate from the 0-300mm playfield to the mat's native coordinate system."""
        
        # Map X coordinate
        mat_x = np.interp(
            playfield_x,
            [0, config.PLAYFIELD_SIZE_MM[0]],
            [config.MAT_MAP["top_left"][0], config.MAT_MAP["bottom_right"][0]]
        )
        
        # Map Y coordinate (handles the inversion automatically)
        mat_y = np.interp(
            playfield_y,
            [0, config.PLAYFIELD_SIZE_MM[1]],
            [config.MAT_MAP["top_left"][1], config.MAT_MAP["bottom_right"][1]]
        )
        
        return int(mat_x), int(mat_y)

    # ... (notification handler is the same) ...
    def _notification_handler(self, address: str, characteristic, data: bytearray):
        if data[0] == 1:
            x = int.from_bytes(data[1:3], "little")
            y = int.from_bytes(data[3:5], "little")
            angle = int.from_bytes(data[5:7], "little")
            self.robot_states[address].update(x=x, y=y, angle=angle, updated=True)

    # ... (connect, get_robot_state, disconnect are the same) ...
    async def connect(self):
        # ... (no changes here)
        print("[INFO] Connecting to Toio robots...")
        for address in self.addresses:
            client = BleakClient(address)
            try:
                await client.connect(timeout=10.0)
                if client.is_connected:
                    self.clients[address] = client
                    handler = partial(self._notification_handler, address)
                    await client.start_notify(self.pos_id_uuid, handler)
                    print(f"  [OK] Connected and subscribed to {address}")
            except Exception as e:
                print(f"  [ERROR] Failed to connect/subscribe to {address}: {e}")
        print(f"[INFO] Connection finished. {len(self.clients)} robots connected.")
        return len(self.clients) > 0

    def get_robot_state(self, address):
        return self.robot_states.get(address)

    async def disconnect(self):
        for client in self.clients.values():
            if client.is_connected: await client.disconnect()
        print("[INFO] All Toios disconnected.")

    async def send_motor_command(self, address, command):
        client = self.clients.get(address)
        if client and client.is_connected:
            try: await client.write_gatt_char(self.motor_uuid, bytearray(command))
            except Exception as e: print(f"  [ERROR] sending command to {address}: {e}")

    # --- NEW: The rewritten, intelligent moveTo function ---
    async def move_robot_to_target(self, address, target_x_mm, target_y_mm, max_speed=80):
        """Commands a robot to move to a specific target on the playfield."""
        
        # 1. Convert our easy playfield coordinates to the mat's coordinates
        mat_x, mat_y = self._map_playfield_to_mat(target_x_mm, target_y_mm)
        
        print(f"  > CMD: {address} moveTo ({target_x_mm}, {target_y_mm})mm -> ({mat_x}, {mat_y})mat")

        # 2. Build the high-level "Motor control with target specified" command
        command = bytearray(13)
        command[0] = 0x03  # Command ID
        command[1] = 0x01  # Control instance ID
        command[2] = 0x05  # Timeout (5 seconds)
        command[3] = 0x00  # Movement type (move to target, rotating as needed)
        command[4] = int(max_speed)
        command[5] = 0x00  # Speed change type (constant speed)
        command[6] = 0x00  # Reserved
        command[7:9] = mat_x.to_bytes(2, 'little')
        command[9:11] = mat_y.to_bytes(2, 'little')
        command[11:13] = (0).to_bytes(2, 'little') # Final angle doesn't matter

        # 3. Send the command
        await self.send_motor_command(address, command)

        # 4. Wait until the robot reports that it has arrived
        while True:
            state = self.get_robot_state(address)
            if not state or not state['updated']:
                await asyncio.sleep(0.1)
                continue
            
            current_x, current_y = state['x'], state['y']
            distance = np.sqrt((current_x - mat_x)**2 + (current_y - mat_y)**2)
            
            # If we are within 10 mat units (approx 1cm), we consider it "arrived"
            if distance < 10:
                print(f"  <-- OK: {address} arrived at target.")
                break
            
            await asyncio.sleep(0.05) # Check position 20 times per second