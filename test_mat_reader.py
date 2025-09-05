# test_mat_reader.py
import asyncio
from bleak import BleakClient

# --- Configuration ---
# Use the address of the Toio you want to test with.
TOIO_ADDRESS = "EB:69:D3:D2:C1:9A" 

# This is the UUID for the Position ID sensor that we discovered.
POSITION_ID_CHAR_UUID = "10b20101-5b3b-4571-9508-cf3efcd7bbae"

def notification_handler(characteristic, data: bytearray):
    """
    This function is called every time the Toio sends new position data.
    It decodes the raw byte data into readable numbers.
    """
    # According to the toio spec, the first byte tells us the type of data.
    # '1' means it's a standard mat position reading.
    if data[0] == 1:
        # Bytes 1 and 2 are the X coordinate (in little-endian format).
        x = int.from_bytes(data[1:3], "little")
        # Bytes 3 and 4 are the Y coordinate.
        y = int.from_bytes(data[3:5], "little")
        # Bytes 5 and 6 are the Angle.
        angle = int.from_bytes(data[5:7], "little")
        
        # Print the data to the console. The '\r' at the start and end=''
        # makes the line update in place, which is much cleaner.
        print(f"Position -> X: {x:4d}, Y: {y:4d}, Angle: {angle:3d}", end='\r')

async def main(address):
    print(f"Attempting to connect to {address}...")
    async with BleakClient(address) as client:
        if client.is_connected:
            print(f"--> Successfully connected! Subscribing to position data...")
            print("--> Place the robot on the mat. Press Ctrl+C to stop.")
            
            # Subscribe to notifications from the position sensor.
            # The 'notification_handler' function will now be called automatically.
            await client.start_notify(POSITION_ID_CHAR_UUID, notification_handler)
            
            # Keep the script running to receive data.
            while True:
                await asyncio.sleep(1.0)
        else:
            print(f"--> Failed to connect to {address}")

if __name__ == "__main__":
    try:
        asyncio.run(main(TOIO_ADDRESS))
    except KeyboardInterrupt:
        print("\nStopping script.")