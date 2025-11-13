import cv2
import threading
import logging
from typing import Optional

from app.config.settings import camera_config
from app.services.detection import DetectionService
from app.core.heatmap import HeatmapProcessor

logger = logging.getLogger(__name__)

class Camera:
    def __init__(self):
        self.cap = cv2.VideoCapture(camera_config.URL)
        self.lock = threading.Lock()
        self.detector = DetectionService()
        self.heatmap_processor = HeatmapProcessor()
        self._setup_camera()
    
    def _setup_camera(self) -> None:
        """Настройка параметров камеры"""
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    def get_frame(self) -> Optional[bytes]:
        """Получение кадра с детекцией и тепловой картой"""
        with self.lock:
            try:
                success, frame = self.cap.read()
                if not success:
                    self._reconnect_camera()
                    return None
                
                # Детекция объектов
                frame_with_detections, detections = self.detector.detect_objects(frame)
                
                # Обновление тепловой карты если есть обнаружения
                if detections:
                    self.heatmap_processor.update_heatmap(frame, detections)
                
                # Наложение тепловой карты
                final_frame = self.heatmap_processor.apply_heatmap_overlay(frame_with_detections)
                
                # Кодирование в JPEG
                ret, jpeg = cv2.imencode('.jpg', final_frame)
                return jpeg.tobytes() if ret else None
                
            except Exception as e:
                logger.error(f"Error processing frame: {e}")
                return None
    
    def _reconnect_camera(self) -> None:
        """Переподключение к камере"""
        try:
            self.cap.release()
            self.cap = cv2.VideoCapture(camera_config.URL)
            self._setup_camera()
        except Exception as e:
            logger.error(f"Camera reconnection failed: {e}")
    
    def cleanup(self) -> None:
        """Очистка ресурсов"""
        self.cap.release()
        self.heatmap_processor.save_heatmap()