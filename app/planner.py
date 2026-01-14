# app/planner.py
from typing import List, Dict, Tuple

def rects_overlap(px, py, cell_w, cell_h, obs):
    # obs: dict with x, y (bottom-left), width, height (meters)
    # we consider cell as [px, px+cell_w) x [py, py+cell_h)
    ox1, oy1 = obs['x'], obs['y']
    ox2, oy2 = obs['x'] + obs['width'], obs['y'] + obs['height']
    cx1, cy1 = px, py
    cx2, cy2 = px + cell_w, py + cell_h
    return not (cx2 <= ox1 or cx1 >= ox2 or cy2 <= oy1 or cy1 >= oy2)

def point_in_any_obstacle(x, y, obstacles):
    # For a point check we can simply check if inside any rect
    for obs in obstacles:
        if obs['x'] <= x <= obs['x'] + obs['width'] and obs['y'] <= y <= obs['y'] + obs['height']:
            return True
    return False

def generate_coverage_path(wall_w: float, wall_h: float, obstacles: List[Dict], step: float = 0.1) -> List[Tuple[float, float]]:
    """
    Generate a zigzag path covering the wall area with grid step size 'step' (meters).
    Obstacles is a list of dicts: {x, y, width, height} where (x,y) is bottom-left corner.
    Returns a list of (x_center, y_center) points.
    """
    # number of steps along x and y
    nx = max(1, int(round(wall_w / step)))
    ny = max(1, int(round(wall_h / step)))
    cell_w = wall_w / nx
    cell_h = wall_h / ny

    path = []
    for row in range(ny):
        y = (row + 0.5) * cell_h  # center of the cell
        # determine x order: left->right or right->left
        if row % 2 == 0:
            x_indices = range(nx)
        else:
            x_indices = range(nx - 1, -1, -1)

        for i in x_indices:
            x = (i + 0.5) * cell_w
            # skip if overlaps obstacle (we check rectangle overlap between cell and obstacle)
            blocked = False
            for obs in obstacles:
                if rects_overlap(x - cell_w/2, y - cell_h/2, cell_w, cell_h, obs):
                    blocked = True
                    break
            if not blocked:
                path.append((round(x, 4), round(y, 4)))
    return path
