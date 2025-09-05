# Hands Arcade

Living arcade system with 4 Sony Toio robots and hand-tracking interaction.

## Setup
```bash
# clone repo
git clone <your-private-github-url>
cd hands-arcade

# install deps
pip3 install -r requirements.txt
```

## Quick tests
- Discover Toios:
```bash
python3 scripts/discover_toios.py
```

- Camera capture:
```bash
python3 scripts/capture_test.py --out test.mp4
```
