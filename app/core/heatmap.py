import numpy as np
import cv2
import datetime
import time
import logging
from typing import Optional, Dict, Any

from app.config.settings import heatmap_config
from app.services.storage import StorageService

logger = logging.getLogger(__name__)

class HeatmapProcessor:
    def __init__(self):
        self.heatmap: Optional[np.ndarray] = None
        self.heatmap_start_time = datetime.datetime.now()
        self.last_save_time = time.time()
        self.last_frame_with_heatmap: Optional[np.ndarray] = None
        self.storage = StorageService()
        
        # Загружаем последнюю тепловую карту
        self.load_heatmap()
    
    def update_heatmap(self, frame: np.ndarray, detections: list) -> None:
        """Обновление тепловой карты на основе обнаружений"""
        if self.heatmap is None:
            self.heatmap = np.zeros(frame.shape[:2], dtype=np.float32)
        
        new_heat = np.zeros(frame.shape[:2], dtype=np.float32)
        
        for box in detections:
            x1, y1, x2, y2 = box
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            
            cv2.circle(new_heat, (center_x, center_y), 
                      heatmap_config.GAUSSIAN_RADIUS, 1, -1)
        
        self.heatmap = self.heatmap + new_heat
        self._auto_save_check()
    
    def apply_heatmap_overlay(self, frame: np.ndarray) -> np.ndarray:
        """Наложение тепловой карты на кадр"""
        if self.heatmap is None or np.max(self.heatmap) == 0:
            return frame
        
        if np.max(self.heatmap) > 0:
            heatmap_norm = (self.heatmap / np.max(self.heatmap) * 255).astype(np.uint8)
        else:
            heatmap_norm = np.zeros(frame.shape[:2], dtype=np.uint8)
        
        heatmap_colored = cv2.applyColorMap(heatmap_norm, cv2.COLORMAP_JET)
        overlay = cv2.addWeighted(frame, 0.7, heatmap_colored, 0.3, 0)
        
        # Добавляем информацию
        elapsed_time = datetime.datetime.now() - self.heatmap_start_time
        total_heat = np.sum(self.heatmap)
        
        info_text = (f"Time: {elapsed_time.seconds//3600:02d}:"
                    f"{(elapsed_time.seconds%3600)//60:02d} | Activity: {total_heat:.0f}")
        
        cv2.putText(overlay, info_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        self.last_frame_with_heatmap = overlay.copy()
        return overlay
    
    def get_statistics(self) -> Optional[Dict[str, Any]]:
        """Получение статистики тепловой карты"""
        if self.heatmap is None:
            return None
            
        total_human_seconds = int(np.sum(self.heatmap))
        hours = total_human_seconds // 3600
        minutes = (total_human_seconds % 3600) // 60
        seconds = total_human_seconds % 60
        
        elapsed_time = datetime.datetime.now() - self.heatmap_start_time
        
        return {
            'total_presence': f"{hours}ч {minutes}м",
            'total_presence_detailed': f"{hours:02d}:{minutes:02d}:{seconds:02d}",
            'total_activity_points': float(np.sum(self.heatmap)),
            'max_activity': float(np.max(self.heatmap)),
            'average_activity': float(np.mean(self.heatmap)) if self.heatmap.size > 0 else 0,
            'collection_duration_hours': elapsed_time.total_seconds() / 3600,
            'duration_hours': elapsed_time.total_seconds() / 3600,
            'total_activity': float(np.sum(self.heatmap))
        }
    
    def save_heatmap(self) -> None:
        """Сохранение тепловой карты"""
        if self.heatmap is not None and np.sum(self.heatmap) > 0:
            self.storage.save_heatmap_data(
                self.heatmap, 
                self.heatmap_start_time,
                self.last_frame_with_heatmap,
                self.get_statistics()
            )
    
    def load_heatmap(self) -> None:
        """Загрузка тепловой карты"""
        loaded_data = self.storage.load_latest_heatmap()
        if loaded_data:
            self.heatmap = loaded_data['heatmap']
            self.heatmap_start_time = loaded_data['start_time']
    
    def reset_heatmap(self) -> None:
        """Сброс тепловой карты"""
        self.heatmap = None
        self.heatmap_start_time = datetime.datetime.now()
    
    def _auto_save_check(self) -> None:
        """Проверка автосохранения по таймеру"""
        current_time = time.time()
        if current_time - self.last_save_time >= heatmap_config.SAVE_INTERVAL:
            self.save_heatmap()
            self.last_save_time = current_time