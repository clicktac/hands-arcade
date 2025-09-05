import asyncio
from toio import CubeScanner

async def main():
    print("Scanning for Toio cubes...")
    scanner = CubeScanner()
    cubes = await scanner.search()
    for c in cubes:
        print(f"Found cube: {c.id} - addr: {c.address}")

if __name__ == "__main__":
    asyncio.run(main())
