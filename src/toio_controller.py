import asyncio
from toio import CubeScanner, Cube

class ToioController:
    def __init__(self, addresses_file="data/toioBLT_address.txt"):
        with open(addresses_file, "r") as f:
            self.addresses = [line.strip() for line in f if line.strip()]
        self.cubes = []

    async def connect(self):
        for addr in self.addresses:
            cube = Cube(addr)
            await cube.connect()
            print(f"Connected to cube {addr}")
            self.cubes.append(cube)

    async def disconnect(self):
        for cube in self.cubes:
            await cube.disconnect()
