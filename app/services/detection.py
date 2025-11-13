import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Tuple, Optional
import logging

# Исправление для PyTorch 2.6
import torch
import ultralytics.nn.tasks
torch.serialization.add_safe_globals([ultralytics.nn.tasks.DetectionModel])

from app.config.settings import model_config

logger = logging.getLogger(__name__)

class DetectionService:
    def __init__(self):
        self.model = YOLO(model_config.MODEL_PATH)
        self.target_classes = model_config.TARGET_CLASSES
        
    def detect_objects(self, frame: np.ndarray) -> Tuple[np.ndarray, List]:
        """Обнаружение объектов на кадре"""
        try:
            results = self.model.track(frame, persist=True, verbose=False)
            detections = []
            
            if results[0].boxes is not None and results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                classes = results[0].boxes.cls.cpu().numpy()
                confidences = results[0].boxes.conf.cpu().numpy()
                ids = results[0].boxes.id.cpu().numpy()
                
                for box, cls, conf, id in zip(boxes, classes, confidences, ids):
                    if cls in self.target_classes and conf > model_config.CONFIDENCE_THRESHOLD:
                        x1, y1, x2, y2 = map(int, box)
                        detections.append([x1, y1, x2, y2])
                        
                        # Рисуем bounding box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        label = f"ID:{int(id)} {self.model.names[int(cls)]}: {conf:.2f}"
                        cv2.putText(frame, label, (x1, y1 - 10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            return frame, detections
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return frame, []