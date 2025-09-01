# discover_toio.py
import asyncio
from bleak import BleakClient

# Put the address of your FIRST Toio here
ADDRESS = "EB:69:D3:D2:C1:9A"

async def main(address):
    print(f"Attempting to connect to {address}...")
    async with BleakClient(address) as client:
        if client.is_connected:
            print(f"Successfully connected to {address}")
            print("-" * 30)
            
            # Iterate through all services offered by the device
            for service in client.services:
                print(f"[Service] {service.uuid}: {service.description}")
                
                # For each service, iterate through its characteristics
                for char in service.characteristics:
                    print(f"  [Characteristic] {char.uuid}: {char.description}")
                    # Also print the properties (read, write, notify, etc.)
                    print(f"    Properties: {', '.join(char.properties)}")
            
            print("-" * 30)
        else:
            print(f"Failed to connect to {address}")

if __name__ == "__main__":
    asyncio.run(main(ADDRESS))
