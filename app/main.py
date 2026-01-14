# app/main.py
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import time, json, logging, hashlib
from typing import Optional, Dict, Any
from functools import lru_cache
from .db import init_db, save_trajectory, get_trajectory, list_trajectories, get_trajectory_stats, search_trajectories_by_performance
from .planner import generate_coverage_path
from .models import GenerateRequest
from pathlib import Path

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('robot_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Autonomous Wall-Finishing Robot Control System",
    description="Intelligent path planning and coverage optimization for autonomous wall-finishing robots",
    version="1.0.0"
)

# Initialize database on startup (with error handling for serverless)
try:
    init_db()
except Exception as e:
    logger.warning(f"Database initialization failed: {e}. Running in serverless mode.")

# In-memory cache for frequently accessed data
trajectory_cache: Dict[str, Any] = {}
stats_cache: Dict[str, Any] = {}
CACHE_TTL = 300  # 5 minutes

def get_cache_key(wall_width: float, wall_height: float, step: float, obstacles: list) -> str:
    """Generate a cache key for trajectory parameters"""
    obstacles_str = json.dumps(sorted(obstacles, key=lambda x: (x['x'], x['y'], x['width'], x['height'])))
    content = f"{wall_width}_{wall_height}_{step}_{obstacles_str}"
    return hashlib.md5(content.encode()).hexdigest()

@lru_cache(maxsize=1000)
def cached_generate_coverage_path(wall_width: float, wall_height: float, step: float, obstacles_str: str) -> tuple:
    """Cached version of coverage path generation"""
    obstacles = json.loads(obstacles_str)
    return tuple(generate_coverage_path(wall_width, wall_height, obstacles, step))

# serve static frontend
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    logger.info(f"Request started: {request.method} {request.url.path} from {client_ip}")
    
    try:
        response = await call_next(request)
        elapsed = time.time() - start
        
        # Log response details
        logger.info(f"Request completed: {request.method} {request.url.path} - {response.status_code} - {elapsed:.4f}s")
        
        # Log slow requests
        if elapsed > 1.0:
            logger.warning(f"Slow request detected: {request.method} {request.url.path} took {elapsed:.4f}s")
            
        return response
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"Request failed: {request.method} {request.url.path} - {str(e)} - {elapsed:.4f}s")
        raise

@app.post("/generate_trajectory")
async def generate_trajectory(req: GenerateRequest):
    logger.info(f"Generating trajectory for wall {req.wall_width}x{req.wall_height} with step {req.step}")
    
    # Enhanced validation
    if req.wall_width <= 0 or req.wall_height <= 0:
        logger.warning(f"Invalid wall dimensions: {req.wall_width}x{req.wall_height}")
        raise HTTPException(status_code=400, detail="Wall dimensions must be positive")
    
    if req.step <= 0:
        logger.warning(f"Invalid step size: {req.step}")
        raise HTTPException(status_code=400, detail="Step size must be positive")
    
    if req.step > min(req.wall_width, req.wall_height):
        logger.warning(f"Step size {req.step} too large for wall {req.wall_width}x{req.wall_height}")
        raise HTTPException(status_code=400, detail="Step size too large for wall dimensions")
    
    # Validate obstacles
    obstacles = [o.dict() for o in req.obstacles]
    for i, obs in enumerate(obstacles):
        if obs['width'] <= 0 or obs['height'] <= 0:
            logger.warning(f"Invalid obstacle {i}: {obs}")
            raise HTTPException(status_code=400, detail=f"Obstacle {i} has invalid dimensions")
        if obs['x'] < 0 or obs['y'] < 0 or obs['x'] + obs['width'] > req.wall_width or obs['y'] + obs['height'] > req.wall_height:
            logger.warning(f"Obstacle {i} outside wall bounds: {obs}")
            raise HTTPException(status_code=400, detail=f"Obstacle {i} is outside wall boundaries")
    
    # Check cache first
    cache_key = get_cache_key(req.wall_width, req.wall_height, req.step, obstacles)
    if cache_key in trajectory_cache:
        cached_data = trajectory_cache[cache_key]
        if time.time() - cached_data['timestamp'] < CACHE_TTL:
            logger.info(f"Returning cached trajectory for key {cache_key[:8]}...")
            return cached_data['response']
    
    # Generate path with timing
    start_time = time.time()
    try:
        # Use cached path generation if possible
        obstacles_str = json.dumps(obstacles)
        path_tuple = cached_generate_coverage_path(req.wall_width, req.wall_height, req.step, obstacles_str)
        path = list(path_tuple)
        
        processing_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
        
        logger.info(f"Path generation completed in {processing_time}ms, generated {len(path)} points")
        
        # Save with enhanced metadata
        tid = save_trajectory(
            req.wall_width, req.wall_height, req.step, path, 
            obstacles=obstacles, processing_time_ms=processing_time
        )
        
        response_data = {
            "id": tid, 
            "path_length": len(path),
            "processing_time_ms": processing_time,
            "coverage_percentage": round(((req.wall_width * req.wall_height - sum(obs['width'] * obs['height'] for obs in obstacles)) / (req.wall_width * req.wall_height)) * 100, 2)
        }
        
        # Cache the response
        trajectory_cache[cache_key] = {
            'response': response_data,
            'timestamp': time.time()
        }
        
        return response_data
    except Exception as e:
        logger.error(f"Path generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Path generation failed: {str(e)}")

@app.get("/trajectory/{tid}")
async def get_traj(tid: int):
    logger.info(f"Retrieving trajectory {tid}")
    row = get_trajectory(tid)
    if not row:
        logger.warning(f"Trajectory {tid} not found")
        raise HTTPException(status_code=404, detail="Trajectory not found")
    
    # Return path as JSON string (tests expect a string) and obstacles as object
    path_str = row["path"] if isinstance(row["path"], str) else json.dumps(row["path"])
    obstacles = row["obstacles"] if isinstance(row["obstacles"], list) else json.loads(row["obstacles"])
    
    return {
        "id": row["id"],
        "wall_width": row["wall_width"],
        "wall_height": row["wall_height"],
        "step": row["step"],
        "path": path_str,
        "obstacles": obstacles,
        "path_length": row["path_length"],
        "coverage_percentage": row["coverage_percentage"],
        "processing_time_ms": row["processing_time_ms"],
        "created_at": row["created_at"]
    }

@app.get("/trajectories")
async def get_list(
    limit: int = Query(20, ge=1, le=100, description="Number of trajectories to return"),
    offset: int = Query(0, ge=0, description="Number of trajectories to skip"),
    wall_width: Optional[float] = Query(None, description="Filter by wall width"),
    wall_height: Optional[float] = Query(None, description="Filter by wall height"),
    min_coverage: Optional[float] = Query(None, ge=0, le=100, description="Minimum coverage percentage")
):
    logger.info(f"Listing trajectories: limit={limit}, offset={offset}, filters: width={wall_width}, height={wall_height}, min_coverage={min_coverage}")
    return list_trajectories(limit=limit, offset=offset, wall_width=wall_width, wall_height=wall_height, min_coverage=min_coverage)

@app.get("/trajectories/stats")
async def get_trajectory_statistics():
    """Get comprehensive statistics about stored trajectories"""
    logger.info("Retrieving trajectory statistics")
    return get_trajectory_stats()

@app.get("/trajectories/performance")
async def get_trajectories_by_performance(
    min_processing_time: Optional[int] = Query(None, ge=0, description="Minimum processing time in ms"),
    max_processing_time: Optional[int] = Query(None, ge=0, description="Maximum processing time in ms"),
    limit: int = Query(20, ge=1, le=100, description="Number of trajectories to return")
):
    """Search trajectories by performance characteristics"""
    logger.info(f"Searching trajectories by performance: min_time={min_processing_time}, max_time={max_processing_time}")
    return search_trajectories_by_performance(min_processing_time, max_processing_time, limit)

# Simple homepage
@app.get("/")
async def homepage():
    return FileResponse(Path(__file__).parent / "static" / "index.html")
