# main.py (Navigation Test Script)
import asyncio
import config
from robot_navigation import ToioController

async def main():
    toio_controller = None
    try:
        toio_controller = ToioController(
            config.TOIO_ADDRESSES, 
            config.TOIO_MOTOR_CHAR_UUID, 
            config.TOIO_POSITION_ID_CHAR_UUID
        )
        
        await toio_controller.connect()
        if len(toio_controller.clients) == 0:
            print("\n[FATAL] No Toio robots connected. Exiting.")
            return

        print("\n--- Starting Navigation Test ---")
        
        # Define the corners of our "safe" playfield (30mm from the edges)
        # Using a dictionary to map robot address to target for clarity
        robot_addresses = list(toio_controller.clients.keys())
        targets = {
            robot_addresses[0]: (30, 30),      # Robot 1 -> Top-Left
            robot_addresses[1]: (270, 30),     # Robot 2 -> Top-Right
            robot_addresses[2]: (30, 270),     # Robot 3 -> Bottom-Left
            robot_addresses[3]: (270, 270),    # Robot 4 -> Bottom-Right
        }

        # Create a list of movement tasks
        tasks = []
        for address, target in targets.items():
            task = toio_controller.move_robot_to_target(address, target[0], target[1])
            tasks.append(task)

        # Run all movement tasks simultaneously and wait for them all to complete
        await asyncio.gather(*tasks)

        print("\n--- Navigation Test Complete ---")

    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        print("\n[INFO] Cleaning up and shutting down...")
        if toio_controller:
            await toio_controller.disconnect()

if __name__ == "__main__":
    asyncio.run(main())