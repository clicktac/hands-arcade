# config.py

# -- Hardware Settings --
CAMERA_INDEX = 0
CAMERA_RESOLUTION = (640, 480)

# -- Calibration Data --
CALIBRATION_FILE = "calibration_data.npz"
MAT_MAP = {
    "top_left": (89, 238),      # Mat XY for Playfield (0, 0)
    "bottom_right": (283, 45)  # Mat XY for Playfield (300, 300)
}

# -- Playfield Settings --
PLAYFIELD_SIZE_MM = (300, 300)

# -- Toio Robot BLE Addresses --
TOIO_ADDRESSES = [
    "EB:69:D3:D2:C1:9A",
    "C3:6B:4A:1F:C1:57",
    "F1:4C:2F:5F:54:4A",
    "CB:7D:4C:24:58:4B",
]

# -- Toio BLE Characteristics (UUIDs) --
TOIO_MOTOR_CHAR_UUID = "10b20102-5b3b-4571-9508-cf3efcd7bbae"
TOIO_POSITION_ID_CHAR_UUID = "10b20101-5b3b-4571-9508-cf3efcd7bbae"