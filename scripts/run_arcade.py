import asyncio, time, logging, math
from typing import Dict
from toio import ToioCoreCube, BLEScanner

from src.state_machine import CubeStateMachine, Params, compute_repulsions, Pose

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("arcade")

async def set_motor_speeds(cube: ToioCoreCube, v_l_mm_s: float, v_r_mm_s: float, duration_ms: int = 100):
    ok = False
    for name in ["motor_control", "set_motor", "motor"]:
        fn = getattr(cube, name, None)
        if callable(fn):
            try:
                await fn(int(v_l_mm_s), int(v_r_mm_s), int(duration_ms))
                ok = True
                break
            except Exception as e:
                log.debug("motor method %s failed: %s", name, e)
    if not ok:
        api_motor = getattr(getattr(cube, "api", None), "motor", None)
        if api_motor:
            for mname in ["motor_control", "run", "drive"]:
                fn = getattr(api_motor, mname, None)
                if callable(fn):
                    try:
                        await fn(int(v_l_mm_s), int(v_r_mm_s), int(duration_ms))
                        ok = True
                        break
                    except Exception as e:
                        log.debug("api.motor.%s failed: %s", mname, e)
    if not ok:
        log.warning("No compatible motor method found; speeds (%s, %s) not sent.", v_l_mm_s, v_r_mm_s)

class PoseTracker:
    def __init__(self, cube: ToioCoreCube):
        self.cube = cube
        self.pose = Pose(150.0, 150.0, 0.0, time.time())

    async def enable_notifications(self):
        enabled = False
        api = getattr(self.cube, "api", None)
        if api and hasattr(api, "id"):
            try:
                await api.id.request_id_information(True)
                enabled = True
            except Exception as e:
                log.debug("api.id.request_id_information failed: %s", e)

            try:
                def on_id(packet):
                    x = getattr(packet, "x", None)
                    y = getattr(packet, "y", None)
                    angle = getattr(packet, "angle", None) or getattr(packet, "deg", None) or 0.0
                    if x is not None and y is not None:
                        self.pose = Pose(float(x), float(y), math.radians(float(angle)), time.time())
                if hasattr(api.id, "add_listener"):
                    api.id.add_listener(on_id)
                    enabled = True
            except Exception as e:
                log.debug("api.id.add_listener failed: %s", e)

        if not enabled:
            log.warning("Position-ID notifications not enabled; using default pose.")

async def main():
    log.info("Scanning for up to 4 cubes...")
    devs = await BLEScanner.scan(num=4)
    if not devs:
        log.error("No cubes found. Power them on and retry.")
        return

    state_order = ["roaming", "tired", "stressed", "lazy"]
    cubes = []
    trackers: Dict[str, PoseTracker] = {}
    sms: Dict[str, CubeStateMachine] = {}

    for i, dev in enumerate(devs[:4]):
        cube = ToioCoreCube(dev.interface)
        await cube.connect()
        cid = f"cube{i+1}"
        log.info("Connected %s on %s", cid, dev.interface)
        cubes.append((cid, cube))

        tracker = PoseTracker(cube)
        await tracker.enable_notifications()
        trackers[cid] = tracker

        sms[cid] = CubeStateMachine(cid, state_order[i % len(state_order)], Params())

    period = 0.1
    try:
        last = time.time()
        while True:
            now = time.time(); dt = now - last; last = now

            poses = {cid: trackers[cid].pose for cid, _ in cubes}
            rep = compute_repulsions(poses, list(sms.values())[0].p.safety_radius)

            for cid, cube in cubes:
                v_l, v_r = sms[cid].step(dt, repel_vec=rep[cid])
                log.info("%s state=%s pose=(%.0f,%.0f) vL=%.1f vR=%.1f",
                         cid, sms[cid].state, poses[cid].x, poses[cid].y, v_l, v_r)
                await set_motor_speeds(cube, v_l, v_r, int(period*1000))

            await asyncio.sleep(period)
    except KeyboardInterrupt:
        log.info("Stopping...")
    finally:
        for _, cube in cubes:
            try:
                await set_motor_speeds(cube, 0, 0, 100)
                await cube.disconnect()
            except Exception:
                pass
        log.info("Disconnected all cubes.")

if __name__ == "__main__":
    asyncio.run(main())
