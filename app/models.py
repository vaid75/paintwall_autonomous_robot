# app/models.py
from pydantic import BaseModel, Field
from typing import List

class Obstacle(BaseModel):
    x: float = Field(..., description="bottom-left x in meters")
    y: float = Field(..., description="bottom-left y in meters")
    width: float = Field(..., description="width in meters")
    height: float = Field(..., description="height in meters")

class GenerateRequest(BaseModel):
    wall_width: float
    wall_height: float
    step: float = 0.1
    obstacles: List[Obstacle] = []

class GenerateResponse(BaseModel):
    id: int
    path_length: int
