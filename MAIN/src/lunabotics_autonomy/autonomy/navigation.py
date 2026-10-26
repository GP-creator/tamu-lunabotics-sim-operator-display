"""Cost-aware A* with inflation, collision-checked shortcutting, and regulated tracking."""
import heapq
import math
from functools import lru_cache
from .types import Config, Pose


def distance(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])


def wrap(a):
    return (a + math.pi) % (2*math.pi) - math.pi


def point_segment_distance(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    if dx*dx+dy*dy < 1e-12:
        return distance(p, a)
    u = max(0.0, min(1.0, ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)))
    return distance(p, (a[0]+u*dx, a[1]+u*dy))


@lru_cache(maxsize=16)
def _footprint_offsets(pad, cell):
    # Cover every cell touching the circular swept footprint, including a
    # half-cell discretization allowance at its edge.
    radius = math.ceil((pad+cell/math.sqrt(2))/cell)
    return tuple((di,dj) for di in range(-radius,radius+1)
        for dj in range(-radius,radius+1)
        if math.hypot(di*cell,dj*cell) <= pad+cell/math.sqrt(2))


def observed_footprint(p, cfg, known_free, pad=None):
    if known_free is None:
        return True
    pad = pad if pad is not None else cfg.robot_radius+cfg.clearance
    ci,cj = int(p[0]/cfg.cell),int(p[1]/cfg.cell)
    return all((ci+di,cj+dj) in known_free
               for di,dj in _footprint_offsets(pad,cfg.cell))


def segment_clear(a, b, points, cfg, known_free=None):
    pad = max(cfg.robot_radius + cfg.clearance, cfg.stop_distance + 0.10)
    if not all(pad <= x <= bound-pad for x, bound in
               ((a[0], cfg.width), (a[1], cfg.height),
                (b[0], cfg.width), (b[1], cfg.height))):
        return False
    if known_free is not None:
        steps = max(1, math.ceil(distance(a,b)/(cfg.cell*0.5)))
        for index in range(1,steps+1):
            x = a[0]+(b[0]-a[0])*index/steps
            y = a[1]+(b[1]-a[1])*index/steps
            if not observed_footprint((x,y),cfg,known_free):
                return False
    return all(point_segment_distance(p, a, b) >= pad for p in points
               if all(math.isfinite(v) for v in p))


def route_clear(pose: Pose, path, points, cfg, known_free=None):
    if not path:
        return False
    previous = (pose.x, pose.y)
    traveled = 0.0
    for waypoint in path:
        d = distance(previous, waypoint)
        if d > 1e-8 and not segment_clear(previous, waypoint, points, cfg, known_free):
            return False
        traveled += d
        if traveled >= 1.0:
            return True
        previous = waypoint
    return True


def _shortcut(path, obstacles, cfg, known_free=None):
    if len(path) < 3:
        return path
    out = [path[0]]
    i = 0
    while i < len(path)-1:
        j = len(path)-1
        while j > i+1 and not segment_clear(path[i], path[j], obstacles, cfg, known_free):
            j -= 1
        out.append(path[j])
        i = j
    return out


def plan(start: Pose, goal: tuple[float, float], points, cfg: Config, known_free=None):
    """Return a safe any-angle route or [] if the inflated grid has no route."""
    nx, ny = math.ceil(cfg.width/cfg.cell), math.ceil(cfg.height/cfg.cell)
    clearance = max(cfg.robot_radius + cfg.clearance, cfg.stop_distance + 0.10)

    def cell(p):
        return min(nx-1, max(0, int(p[0]/cfg.cell))), min(ny-1, max(0, int(p[1]/cfg.cell)))

    def xy(p):
        return (p[0]+0.5)*cfg.cell, (p[1]+0.5)*cfg.cell

    obstacles = [p for p in points if all(math.isfinite(v) for v in p)]
    blocked = set()
    penalty = {}
    for i in range(nx):
        for j in range(ny):
            x, y = xy((i, j))
            if not (clearance <= x <= cfg.width-clearance and
                    clearance <= y <= cfg.height-clearance):
                blocked.add((i, j))
            if known_free is not None and (i,j) not in known_free:
                blocked.add((i,j))
            elif known_free is not None and not observed_footprint((x,y),cfg,
                    known_free):
                blocked.add((i,j))
    radius = math.ceil((clearance+0.5)/cfg.cell)
    for ox, oy in obstacles:
        ci, cj = cell((ox, oy))
        for i in range(max(0, ci-radius), min(nx, ci+radius+1)):
            for j in range(max(0, cj-radius), min(ny, cj+radius+1)):
                d = distance(xy((i,j)), (ox,oy))
                if d < clearance:
                    blocked.add((i,j))
                elif d < clearance+0.5:
                    penalty[(i,j)] = max(penalty.get((i,j), 0.0),
                                         2.0*(clearance+0.5-d)/0.5)
    source, target = cell((start.x,start.y)), cell(goal)
    # Cell-center inflation is conservative: accept the source only when the
    # continuous pose itself satisfies the same clearance test.
    if (source in blocked and
        (known_free is None or source in known_free) and
        segment_clear((start.x,start.y),(start.x,start.y),obstacles,cfg,known_free)):
        blocked.remove(source)
    if source in blocked or target in blocked:
        return []
    todo = [(distance(source,target),0.0,source)]
    g, parent = {source:0.0}, {}
    while todo:
        _, old_cost, node = heapq.heappop(todo)
        if old_cost > g[node]+1e-8:
            continue
        if node == target:
            chain = [node]
            while chain[-1] != source:
                chain.append(parent[chain[-1]])
            path = [(start.x,start.y)] + [xy(p) for p in reversed(chain[:-1])] + [goal]
            return _shortcut(path, obstacles, cfg, known_free)[1:]
        for di in (-1,0,1):
            for dj in (-1,0,1):
                if not di and not dj:
                    continue
                other = (node[0]+di,node[1]+dj)
                if other in blocked or not (0 <= other[0] < nx and 0 <= other[1] < ny):
                    continue
                if di and dj and ((node[0]+di,node[1]) in blocked or
                                  (node[0],node[1]+dj) in blocked):
                    continue
                edge = math.hypot(di,dj)*(1+penalty.get(other,0.0))
                trial = g[node]+edge
                if trial+1e-9 < g.get(other,float('inf')):
                    g[other],parent[other] = trial,node
                    heapq.heappush(todo,(trial+distance(other,target),trial,other))
    return []


def exploratory_route(start: Pose, goal, points, cfg, known_free):
    """Move only within observed free space to acquire a view of an unseen goal.

    The ordinary goal planner gets first priority. Exploration cannot traverse
    unknown space or continue if no safe waypoint makes meaningful progress.
    """
    if known_free is None:
        return [],None
    pad = max(cfg.robot_radius+cfg.clearance,cfg.stop_distance+.10)
    current = distance((start.x,start.y),goal)
    obstacles = [p for p in points if all(math.isfinite(v) for v in p)]
    def xy(cell):
        return ((cell[0]+.5)*cfg.cell,(cell[1]+.5)*cfg.cell)
    allowed = set()
    for cell in known_free:
        p = xy(cell)
        if (pad <= p[0] <= cfg.width-pad and
            pad <= p[1] <= cfg.height-pad and
            observed_footprint(p,cfg,known_free) and
            all(distance(p,obstacle) >= pad for obstacle in obstacles)):
            allowed.add(cell)
    source = (int(start.x/cfg.cell),int(start.y/cfg.cell))
    if source not in allowed:
        return [],None
    # Search the connected component first. Sorting all observed cells by
    # goal distance can choose unreachable islands behind unseen shadows.
    queue = [source]
    seen = {source}
    best,score = None,float('inf')
    for cell in queue:
        p = xy(cell)
        progress = current-distance(p,goal)
        travel = distance(p,(start.x,start.y))
        if progress >= .5 and travel >= .5:
            candidate_score = distance(p,goal)+.02*travel
            if candidate_score < score:
                best,score = p,candidate_score
        for di,dj in ((1,0),(-1,0),(0,1),(0,-1),
                      (1,1),(1,-1),(-1,1),(-1,-1)):
            other = (cell[0]+di,cell[1]+dj)
            if other not in allowed or other in seen:
                continue
            if di and dj and ((cell[0]+di,cell[1]) not in allowed or
                              (cell[0],cell[1]+dj) not in allowed):
                continue
            seen.add(other)
            queue.append(other)
    if best is not None:
        route = plan(start,best,points,cfg,known_free)
        if route:
            return route,best
    return [],None


def follow(pose: Pose, path, cfg: Config, points=(), loaded=False):
    """Adaptive lookahead, curvature and obstacle/goal velocity regulation."""
    if not path:
        return 0.0,0.0
    goal = path[-1]
    speed_cap = min(cfg.max_linear, cfg.loaded_max_linear) if loaded else cfg.max_linear
    lookahead = max(0.35, min(0.7, 0.35+speed_cap))
    previous = (pose.x,pose.y)
    remaining = lookahead
    look = goal
    for waypoint in path:
        length = distance(previous,waypoint)
        if length >= remaining and length > 1e-8:
            fraction = remaining/length
            look = (previous[0]+fraction*(waypoint[0]-previous[0]),
                    previous[1]+fraction*(waypoint[1]-previous[1]))
            break
        remaining -= length
        previous = waypoint
    d = max(0.01,distance((pose.x,pose.y),look))
    error = wrap(math.atan2(look[1]-pose.y,look[0]-pose.x)-pose.yaw)
    if abs(error) > 0.45:
        return 0.0,max(-cfg.max_angular,min(cfg.max_angular,1.8*error))
    curvature = 2*math.sin(error)/d
    speed = min(speed_cap, max(0.04, distance((pose.x,pose.y),goal)*0.7))
    speed = min(speed, speed_cap/(1+0.5*abs(curvature)))
    nearest = min((distance((pose.x,pose.y),p) for p in points), default=float('inf'))
    if nearest < cfg.stop_distance+0.6:
        speed *= max(0.15,min(1.0,(nearest-cfg.stop_distance)/0.6))
    omega = max(-cfg.max_angular,min(cfg.max_angular,speed*curvature))
    return speed,omega


def too_close(pose: Pose, points, cfg: Config):
    return any(distance((pose.x,pose.y),p) < cfg.stop_distance for p in points
               if all(math.isfinite(v) for v in p))
