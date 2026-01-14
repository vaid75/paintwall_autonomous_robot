# 🤖 Autonomous Wall-Finishing Robot Control System



A robust, intelligent control system for autonomous wall-finishing robots with advanced path planning, obstacle avoidance, and real-time visualization capabilities.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.119+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightblue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🚀 Features

### Core Functionality
- **🧠 Intelligent Path Planning**: Advanced coverage planning algorithm for rectangular walls with obstacle avoidance
- **🎯 Real-time Visualization**: Interactive 2D web-based visualization with trajectory playback
- **🚧 Obstacle Support**: Handle windows, doors, and other rectangular obstacles
- **⚡ Performance Optimization**: Connection pooling, caching, and advanced database indexing
- **📊 Comprehensive Logging**: Detailed request/response logging with performance monitoring

### Technical Highlights
- **🗄️ Database Optimizations**: SQLite with WAL mode, connection pooling, and advanced indexing
- **💾 Caching System**: In-memory caching for frequently accessed trajectories and statistics
- **📈 Performance Monitoring**: Response time tracking and performance analytics
- **🏗️ Scalable Architecture**: Designed for real-world production use cases

## 📋 Requirements

- Python 3.8+
- FastAPI
- SQLite3
- Modern web browser (for frontend visualization)

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/wall_robot.git
cd wall_robot
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
# Start the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or for development
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 5. Access the Application
- **🌐 Web Interface**: http://localhost:8000
- **📚 API Documentation**: http://localhost:8000/docs
- **📖 Alternative API Docs**: http://localhost:8000/redoc

## 🎯 Usage Examples

### Basic Wall Coverage (5m x 5m)
```bash
curl -X POST "http://localhost:8000/generate_trajectory" \
     -H "Content-Type: application/json" \
     -d '{
       "wall_width": 5.0,
       "wall_height": 5.0,
       "step": 0.1,
       "obstacles": []
     }'
```

### Wall with Obstacles (Window Example)
```bash
curl -X POST "http://localhost:8000/generate_trajectory" \
     -H "Content-Type: application/json" \
     -d '{
       "wall_width": 5.0,
       "wall_height": 5.0,
       "step": 0.1,
       "obstacles": [
         {"x": 2.0, "y": 2.0, "width": 0.25, "height": 0.25}
       ]
     }'
```

### Retrieve Trajectory
```bash
curl "http://localhost:8000/trajectory/1"
```

### Get System Statistics
```bash
curl "http://localhost:8000/trajectories/stats"
```

## 📊 API Endpoints

### Core Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/generate_trajectory` | Generate intelligent coverage path |
| `GET` | `/trajectory/{id}` | Retrieve specific trajectory |
| `GET` | `/trajectories` | List trajectories with filtering |
| `GET` | `/trajectories/stats` | System statistics |
| `GET` | `/trajectories/performance` | Performance-based search |
| `GET` | `/` | Web interface homepage |

### Query Parameters
- `limit` (1-100): Number of results to return
- `offset` (≥0): Number of results to skip
- `wall_width` / `wall_height`: Filter by dimensions
- `min_coverage` (0-100): Minimum coverage percentage
- `min_processing_time` / `max_processing_time`: Performance filters

## 🧪 Testing

### Run All Tests
```bash
# Run tests
python -m pytest tests/test_api.py -v

# Run with coverage
python -m pytest tests/test_api.py --cov=app
```

### Test Categories
- **✅ Trajectory Generation**: Basic and obstacle-based path planning
- **✅ Validation**: Input validation and error handling
- **✅ Performance**: Response time and concurrent request testing
- **✅ Edge Cases**: Extreme scenarios and boundary conditions
- **✅ Database Operations**: CRUD operations and query performance

### Performance Benchmarks
- Path generation: < 5 seconds for 5m x 5m wall
- API response time: < 100ms for cached requests
- Concurrent requests: Supports 5+ simultaneous users
- Database queries: Optimized with advanced indexing

## 🏗️ Architecture

### Backend Components
```
app/
├── main.py          # FastAPI application with caching & logging
├── db.py            # Database layer with connection pooling
├── planner.py       # Coverage path planning algorithm
├── models.py        # Pydantic data models
└── static/          # Frontend assets
    ├── index.html   # Modern responsive UI
    └── app.js       # Interactive visualization
```

### Database Schema
```sql
CREATE TABLE trajectory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wall_width REAL NOT NULL,
    wall_height REAL NOT NULL,
    step REAL NOT NULL,
    path TEXT NOT NULL,
    obstacles TEXT NOT NULL DEFAULT '[]',
    path_length INTEGER NOT NULL DEFAULT 0,
    coverage_percentage REAL NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    processing_time_ms INTEGER NOT NULL DEFAULT 0
);
```

### Performance Optimizations
- **🔗 Connection Pooling**: Reusable database connections
- **📝 WAL Mode**: Better concurrency for SQLite
- **🔍 Advanced Indexing**: Optimized query performance
- **💾 LRU Caching**: In-memory path generation caching
- **⚡ Response Caching**: Statistics and trajectory caching

## 📈 Monitoring & Logging

### Log Files
- `robot_system.log`: Comprehensive application logs
- Request/response timing
- Performance warnings for slow requests
- Error tracking and debugging

### Metrics Tracked
- Request/response times
- Path generation performance
- Database query performance
- Cache hit/miss ratios
- System resource usage

## 🔧 Configuration

### Environment Variables
```bash
# Database configuration
DB_PATH=robot.db

# Cache settings
CACHE_TTL=300  # 5 minutes

# Logging level
LOG_LEVEL=INFO
```

### Performance Tuning
- Adjust connection pool size in `app/db.py`
- Modify cache TTL in `app/main.py`
- Configure logging levels for production
- Set appropriate step sizes for your use case

## 🚀 Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations
- Use PostgreSQL for production databases
- Implement Redis for distributed caching
- Add authentication and authorization
- Set up monitoring and alerting
- Configure load balancing for high availability

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov

# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the test cases for usage examples
3. Check the logs for error details
4. Create an issue with detailed information

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- SQLite for reliable database storage
- The robotics community for inspiration

---

**Built with ❤️ for autonomous robotics and intelligent path planning**

 
