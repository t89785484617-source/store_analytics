import os
from dataclasses import dataclass
from typing import List

@dataclass
class CameraConfig:
    URL: str = os.getenv("CAMERA_URL", "rtsp://admin:Jaquio@10.11.201.6:554/live/main")
    RECONNECT_TIMEOUT: int = 5

@dataclass
class ModelConfig:
    MODEL_PATH: str = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
    TARGET_CLASSES: List[int] = None  # 0 для людей
    CONFIDENCE_THRESHOLD: float = 0.5

    def __post_init__(self):
        if self.TARGET_CLASSES is None:
            self.TARGET_CLASSES = [0]

@dataclass
class HeatmapConfig:
    SAVE_DIR: str = os.getenv("HEATMAP_SAVE_DIR", "saved_heatmaps")
    SAVE_INTERVAL: int = 300  # 5 минут
    GAUSSIAN_RADIUS: int = 30
    OVERLAY_ALPHA: float = 0.3

@dataclass
class AppConfig:
    HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("APP_PORT", "8001"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

config = AppConfig()
camera_config = CameraConfig()
model_config = ModelConfig()
heatmap_config = HeatmapConfig()