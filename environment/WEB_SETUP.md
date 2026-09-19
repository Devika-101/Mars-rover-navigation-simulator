# Finish-tonight setup

1. Copy these files/folders into the project root:
   - `app.py`
   - `requirements-web.txt`
   - `ui/`
   - `static/`
   - `simulator/README.md`

2. Keep the existing `data/` folder and your existing `environment/` and `pathfinding/` folders.

3. Install:
```bash
pip install -r requirements-web.txt
```

4. Run:
```bash
python app.py
```

5. Open the Flask local address shown in the terminal.

## Important
The included A* is a temporary implementation for getting the website working before the teammate merges A*. Do not submit it as the teammate's implementation if the team is expected to use their version. Once their A* is available, connect it in `app.py`.

## Current demo behavior
- Uses the actual 100x100 Gale Crater environment arrays.
- Click the map or enter target coordinates.
- Checks an outward path and a return path.
- Shows a battery estimate and animates the rover.
- Supports simulated dynamic hazards and replanning.
- Comparison page measures A* and Dijkstra on identical inputs.
