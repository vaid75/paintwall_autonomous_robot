# app/db.py
import sqlite3
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "robot.db"

# Connection pool for better performance
class ConnectionPool:
    def __init__(self, max_connections=10):
        self.max_connections = max_connections
        self.connections = []
        self.lock = threading.Lock()
        self.created_connections = 0
    
    def get_connection(self):
        with self.lock:
            if self.connections:
                return self.connections.pop()
            elif self.created_connections < self.max_connections:
                conn = self._create_connection()
                self.created_connections += 1
                return conn
            else:
                # Wait for a connection to be returned
                while not self.connections:
                    time.sleep(0.01)
                return self.connections.pop()
    
    def return_connection(self, conn):
        with self.lock:
            if len(self.connections) < self.max_connections:
                self.connections.append(conn)
            else:
                conn.close()
                self.created_connections -= 1
    
    def _create_connection(self):
        conn = sqlite3.connect(DB_PATH.as_posix(), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        # Optimize for performance
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        return conn

# Global connection pool
_pool = ConnectionPool()

@contextmanager
def get_conn():
    conn = _pool.get_connection()
    try:
        yield conn
    finally:
        _pool.return_connection(conn)

def init_db():
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS trajectory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wall_width REAL NOT NULL,
                wall_height REAL NOT NULL,
                step REAL NOT NULL,
                path TEXT NOT NULL,
                obstacles TEXT DEFAULT '[]',
                path_length INTEGER DEFAULT 0,
                coverage_percentage REAL DEFAULT 0.0,
                processing_time_ms INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """)
            # index to accelerate lookups by created_at or wall size queries
            cur.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON trajectory(created_at)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_wall_dims ON trajectory(wall_width, wall_height)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_coverage ON trajectory(coverage_percentage)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_processing_time ON trajectory(processing_time_ms)")
            conn.commit()
    except Exception as e:
        print(f"Database initialization error: {e}")
        # Continue without database for serverless environments

def save_trajectory(wall_width, wall_height, step, path, obstacles=None, processing_time_ms=None):
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            now = datetime.utcnow().isoformat()
            
            # Calculate path length and coverage percentage
            path_length = len(path)
            obstacles = obstacles or []
            total_obstacle_area = sum(obs['width'] * obs['height'] for obs in obstacles)
            coverage_percentage = round(((wall_width * wall_height - total_obstacle_area) / (wall_width * wall_height)) * 100, 2)
            
            cur.execute(
                """INSERT INTO trajectory (wall_width, wall_height, step, path, obstacles, path_length, 
                   coverage_percentage, processing_time_ms, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (wall_width, wall_height, step, json.dumps(path), json.dumps(obstacles), 
                 path_length, coverage_percentage, processing_time_ms, now)
            )
            conn.commit()
            tid = cur.lastrowid
            return tid
    except Exception as e:
        print(f"Database save error: {e}")
        # Return a mock ID for serverless environments
        return 1

def get_trajectory(tid):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM trajectory WHERE id = ?", (tid,))
        row = cur.fetchone()
        if not row:
            return None
        return dict(row)

def list_trajectories(limit=20, offset=0, wall_width=None, wall_height=None, min_coverage=None):
    with get_conn() as conn:
        cur = conn.cursor()
        
        # Build query with optional filters
        query = "SELECT id, wall_width, wall_height, step, path_length, coverage_percentage, processing_time_ms, created_at FROM trajectory"
        conditions = []
        params = []
        
        if wall_width is not None:
            conditions.append("wall_width = ?")
            params.append(wall_width)
        if wall_height is not None:
            conditions.append("wall_height = ?")
            params.append(wall_height)
        if min_coverage is not None:
            conditions.append("coverage_percentage >= ?")
            params.append(min_coverage)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]

def get_trajectory_stats():
    """Get comprehensive statistics about stored trajectories"""
    with get_conn() as conn:
        cur = conn.cursor()
        
        # Get basic stats
        cur.execute("""
            SELECT 
                COUNT(*) as total_trajectories,
                AVG(wall_width) as avg_wall_width,
                AVG(wall_height) as avg_wall_height,
                AVG(path_length) as avg_path_length,
                AVG(coverage_percentage) as avg_coverage,
                AVG(processing_time_ms) as avg_processing_time,
                MIN(processing_time_ms) as min_processing_time,
                MAX(processing_time_ms) as max_processing_time
            FROM trajectory
        """)
        stats = dict(cur.fetchone())
        
        # Get performance distribution
        cur.execute("""
            SELECT 
                CASE 
                    WHEN processing_time_ms < 100 THEN 'fast'
                    WHEN processing_time_ms < 500 THEN 'medium'
                    ELSE 'slow'
                END as performance_category,
                COUNT(*) as count
            FROM trajectory
            GROUP BY performance_category
        """)
        performance_dist = {row[0]: row[1] for row in cur.fetchall()}
        stats['performance_distribution'] = performance_dist
        
        return stats

def search_trajectories_by_performance(min_processing_time=None, max_processing_time=None, limit=20):
    """Search trajectories by performance characteristics"""
    with get_conn() as conn:
        cur = conn.cursor()
        
        query = "SELECT id, wall_width, wall_height, step, path_length, coverage_percentage, processing_time_ms, created_at FROM trajectory"
        conditions = []
        params = []
        
        if min_processing_time is not None:
            conditions.append("processing_time_ms >= ?")
            params.append(min_processing_time)
        if max_processing_time is not None:
            conditions.append("processing_time_ms <= ?")
            params.append(max_processing_time)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY processing_time_ms ASC LIMIT ?"
        params.append(limit)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]
