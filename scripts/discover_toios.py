import asyncio
from toio import ToioCoreCube, BLEScanner

async def main():
    print("Scanning for Toio cubes...")
    dev_list = await BLEScanner.scan(num=4)  # Find up to 4 cubes
    if not dev_list:
        print("No cubes found. Make sure they're on and BLE is enabled.")
        return

    for i, dev in enumerate(dev_list, 1):
        print(f"{i}. interface: {dev.interface}, name/id: {dev.name}")

    # Connect to each cube sequentially, then disconnect
    cubes = []
    for dev in dev_list:
        cube = ToioCoreCube(dev.interface)
        await cube.connect()
        print(f"Connected to cube on interface {dev.interface}")
        cubes.append(cube)

    await asyncio.sleep(3)  # Let them stay connected briefly

    for cube in cubes:
        await cube.disconnect()
        print("Disconnected.")

if __name__ == "__main__":
    asyncio.run(main())
