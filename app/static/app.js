// Enhanced Wall Robot Control System Frontend
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const wIn = document.getElementById("w");
const hIn = document.getElementById("h");
const stepIn = document.getElementById("step");
const status = document.getElementById("status");
const obstaclesContainer = document.getElementById("obstacles-container");
const addObstacleBtn = document.getElementById("add-obstacle");

// State management
let path = [];
let obstacles = [];
let animId = null;
let idx = 0;
let scale = 100;
let currentTrajectory = null;

// Initialize with a default obstacle (window example)
let obstacleCounter = 0;

function addObstacleInput() {
  const obstacleDiv = document.createElement('div');
  obstacleDiv.className = 'obstacle-item';
  obstacleDiv.innerHTML = `
    <input type="number" placeholder="X (m)" step="0.1" min="0" value="2" />
    <input type="number" placeholder="Y (m)" step="0.1" min="0" value="2" />
    <input type="number" placeholder="Width (m)" step="0.1" min="0.1" value="0.25" />
    <input type="number" placeholder="Height (m)" step="0.1" min="0.1" value="0.25" />
    <button class="remove-obstacle" onclick="removeObstacle(this)">Remove</button>
  `;
  obstaclesContainer.appendChild(obstacleDiv);
}

function removeObstacle(button) {
  button.parentElement.remove();
}

function getObstaclesFromInputs() {
  const obstacleItems = obstaclesContainer.querySelectorAll('.obstacle-item');
  const obstacles = [];
  
  obstacleItems.forEach(item => {
    const inputs = item.querySelectorAll('input');
    if (inputs.length >= 4) {
      const x = parseFloat(inputs[0].value) || 0;
      const y = parseFloat(inputs[1].value) || 0;
      const width = parseFloat(inputs[2].value) || 0.1;
      const height = parseFloat(inputs[3].value) || 0.1;
      
      if (width > 0 && height > 0) {
        obstacles.push({ x, y, width, height });
      }
    }
  });
  
  return obstacles;
}

function clearCanvas() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function drawWall(wallW, wallH) {
  const margin = 40;
  scale = Math.min((canvas.width - margin) / wallW, (canvas.height - margin) / wallH);
  
  // Draw wall boundary
  ctx.strokeStyle = "#2c3e50";
  ctx.lineWidth = 3;
  ctx.strokeRect(20, 20, wallW * scale, wallH * scale);
  
  // Draw wall fill
  ctx.fillStyle = "#ecf0f1";
  ctx.fillRect(20, 20, wallW * scale, wallH * scale);
  
  // Draw grid lines for better visualization
  ctx.strokeStyle = "#bdc3c7";
  ctx.lineWidth = 1;
  ctx.setLineDash([2, 2]);
  
  const stepSize = parseFloat(stepIn.value);
  const gridStep = stepSize * scale;
  
  for (let x = 20; x <= 20 + wallW * scale; x += gridStep) {
    ctx.beginPath();
    ctx.moveTo(x, 20);
    ctx.lineTo(x, 20 + wallH * scale);
    ctx.stroke();
  }
  
  for (let y = 20; y <= 20 + wallH * scale; y += gridStep) {
    ctx.beginPath();
    ctx.moveTo(20, y);
    ctx.lineTo(20 + wallW * scale, y);
    ctx.stroke();
  }
  
  ctx.setLineDash([]);
}

function drawObstacles(obstacles) {
  obstacles.forEach((obs, index) => {
    const x = 20 + obs.x * scale;
    const y = 20 + obs.y * scale;
    const width = obs.width * scale;
    const height = obs.height * scale;
    
    // Draw obstacle
    ctx.fillStyle = "#e74c3c";
    ctx.fillRect(x, y, width, height);
    
    // Draw obstacle border
    ctx.strokeStyle = "#c0392b";
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, width, height);
    
    // Draw obstacle label
    ctx.fillStyle = "white";
    ctx.font = "12px Arial";
    ctx.textAlign = "center";
    ctx.fillText(`O${index + 1}`, x + width/2, y + height/2 + 4);
  });
}

function drawPathStatic(pathPoints, wallW, wallH, obstacles = []) {
  clearCanvas();
  drawWall(wallW, wallH);
  drawObstacles(obstacles);
  
  if (pathPoints.length === 0) return;
  
  // Draw path
  ctx.strokeStyle = "#3498db";
  ctx.lineWidth = 2;
  ctx.beginPath();
  
  let [x0, y0] = pathPoints[0];
  ctx.moveTo(20 + x0 * scale, 20 + y0 * scale);
  
  for (let i = 1; i < pathPoints.length; i++) {
    const [x, y] = pathPoints[i];
    ctx.lineTo(20 + x * scale, 20 + y * scale);
  }
  ctx.stroke();
  
  // Draw start and end points
  const start = pathPoints[0];
  const end = pathPoints[pathPoints.length - 1];
  
  // Start point (green)
  ctx.fillStyle = "#27ae60";
  ctx.beginPath();
  ctx.arc(20 + start[0] * scale, 20 + start[1] * scale, 6, 0, Math.PI * 2);
  ctx.fill();
  
  // End point (red)
  ctx.fillStyle = "#e74c3c";
  ctx.beginPath();
  ctx.arc(20 + end[0] * scale, 20 + end[1] * scale, 6, 0, Math.PI * 2);
  ctx.fill();
  
  // Draw path direction arrows
  ctx.strokeStyle = "#2c3e50";
  ctx.lineWidth = 1;
  for (let i = 0; i < pathPoints.length - 1; i += Math.max(1, Math.floor(pathPoints.length / 20))) {
    const [x1, y1] = pathPoints[i];
    const [x2, y2] = pathPoints[i + 1];
    drawArrow(20 + x1 * scale, 20 + y1 * scale, 20 + x2 * scale, 20 + y2 * scale);
  }
}

function drawArrow(x1, y1, x2, y2) {
  const angle = Math.atan2(y2 - y1, x2 - x1);
  const arrowLength = 8;
  const arrowAngle = Math.PI / 6;
  
  ctx.beginPath();
  ctx.moveTo(x2, y2);
  ctx.lineTo(x2 - arrowLength * Math.cos(angle - arrowAngle), y2 - arrowLength * Math.sin(angle - arrowAngle));
  ctx.moveTo(x2, y2);
  ctx.lineTo(x2 - arrowLength * Math.cos(angle + arrowAngle), y2 - arrowLength * Math.sin(angle + arrowAngle));
  ctx.stroke();
}

function drawRobotAt(point) {
  const [x, y] = point;
  const cx = 20 + x * scale;
  const cy = 20 + y * scale;
  
  // Robot body
  ctx.fillStyle = "#f39c12";
  ctx.beginPath();
  ctx.arc(cx, cy, 8, 0, Math.PI * 2);
  ctx.fill();
  
  // Robot border
  ctx.strokeStyle = "#e67e22";
  ctx.lineWidth = 2;
  ctx.stroke();
  
  // Robot direction indicator
  ctx.strokeStyle = "#2c3e50";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(cx + 12, cy);
  ctx.stroke();
}

function updateStats(trajectory) {
  document.getElementById('path-length').textContent = trajectory.path_length || '-';
  document.getElementById('coverage').textContent = `${trajectory.coverage_percentage || 0}%`;
  document.getElementById('processing-time').textContent = `${trajectory.processing_time_ms || 0}ms`;
  
  const efficiency = trajectory.path_length && trajectory.processing_time_ms 
    ? Math.round(trajectory.path_length / trajectory.processing_time_ms * 1000) 
    : 0;
  document.getElementById('efficiency').textContent = `${efficiency} pts/s`;
  
  document.getElementById('stats').style.display = 'grid';
}

async function generateAndLoad() {
  const wallW = parseFloat(wIn.value);
  const wallH = parseFloat(hIn.value);
  const step = parseFloat(stepIn.value);
  const obstacles = getObstaclesFromInputs();
  
  // Validation
  if (wallW <= 0 || wallH <= 0) {
    status.textContent = "❌ Invalid wall dimensions";
    return;
  }
  
  if (step <= 0 || step > Math.min(wallW, wallH)) {
    status.textContent = "❌ Invalid step size";
    return;
  }
  
  // Validate obstacles
  for (let i = 0; i < obstacles.length; i++) {
    const obs = obstacles[i];
    if (obs.x < 0 || obs.y < 0 || obs.x + obs.width > wallW || obs.y + obs.height > wallH) {
      status.textContent = `❌ Obstacle ${i + 1} is outside wall boundaries`;
      return;
    }
  }
  
  status.textContent = "🔄 Generating intelligent path...";
  
  try {
    const body = {
      wall_width: wallW,
      wall_height: wallH,
      step: step,
      obstacles: obstacles
    };
    
    const res = await fetch("/generate_trajectory", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body)
    });
    
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Generation failed');
    }
    
    const data = await res.json();
    const trajRes = await fetch(`/trajectory/${data.id}`);
    const traj = await trajRes.json();
    
    path = Array.isArray(traj.path) ? traj.path : JSON.parse(traj.path);
    currentTrajectory = traj;
    
    status.textContent = `✅ Path generated! ID: ${data.id}, Length: ${path.length} points`;
    drawPathStatic(path, wallW, wallH, obstacles);
    updateStats(traj);
    idx = 0;
    
  } catch (error) {
    status.textContent = `❌ Error: ${error.message}`;
    console.error('Generation error:', error);
  }
}

// Animation functions
function startAnimation() {
  if (!path.length) return;
  if (animId) return;
  
  function frame() {
    clearCanvas();
    drawPathStatic(path, parseFloat(wIn.value), parseFloat(hIn.value), getObstaclesFromInputs());
    drawRobotAt(path[idx]);
    
    // Draw progress indicator
    ctx.fillStyle = "rgba(0,0,0,0.7)";
    ctx.fillRect(10, 10, 200, 30);
    ctx.fillStyle = "white";
    ctx.font = "14px Arial";
    ctx.fillText(`Progress: ${idx + 1}/${path.length}`, 20, 30);
    
    idx++;
    if (idx >= path.length) {
      idx = 0;
      cancelAnimationFrame(animId);
      animId = null;
      status.textContent = "✅ Animation completed!";
    } else {
      animId = requestAnimationFrame(frame);
    }
  }
  
  animId = requestAnimationFrame(frame);
}

function pauseAnimation() {
  if (animId) {
    cancelAnimationFrame(animId);
    animId = null;
  }
}

function resetAnimation() {
  pauseAnimation();
  idx = 0;
  if (path.length) {
    clearCanvas();
    drawPathStatic(path, parseFloat(wIn.value), parseFloat(hIn.value), getObstaclesFromInputs());
  }
}

// Event listeners
document.getElementById("generateBtn").addEventListener("click", generateAndLoad);
document.getElementById("play").addEventListener("click", startAnimation);
document.getElementById("pause").addEventListener("click", pauseAnimation);
document.getElementById("reset").addEventListener("click", resetAnimation);
document.getElementById("add-obstacle").addEventListener("click", addObstacleInput);

// Initialize with default obstacle
addObstacleInput();

// Make removeObstacle globally available
window.removeObstacle = removeObstacle;
