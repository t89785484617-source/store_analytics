import os
import cv2
import numpy as np
import datetime
import json
import glob
import logging
from typing import Optional, Dict, Any

from app.config.settings import heatmap_config

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.heatmap_save_dir = heatmap_config.SAVE_DIR
        os.makedirs(self.heatmap_save_dir, exist_ok=True)
    
    def get_today_folder(self) -> str:
        """Возвращает путь к папке текущего дня"""
        today = datetime.datetime.now().strftime("%Y%m%d")
        today_folder = os.path.join(self.heatmap_save_dir, today)
        os.makedirs(today_folder, exist_ok=True)
        return today_folder
    
    def cleanup_old_heatmaps(self, current_day_folder: str) -> None:
        """Удаляет старые тепловые карты, оставляя только последнюю за каждый день"""
        try:
            # Получаем все папки с датами
            day_folders = [f for f in os.listdir(self.heatmap_save_dir) 
                          if os.path.isdir(os.path.join(self.heatmap_save_dir, f)) 
                          and f.isdigit() and len(f) == 8]
            
            for day_folder in day_folders:
                day_path = os.path.join(self.heatmap_save_dir, day_folder)
                
                # Пропускаем текущий день
                if day_path == current_day_folder:
                    continue
                
                # Ищем все файлы тепловых карт в папке дня
                data_files = glob.glob(os.path.join(day_path, "heatmap_data_*.npz"))
                image_files = glob.glob(os.path.join(day_path, "heatmap_*.png"))
                meta_files = glob.glob(os.path.join(day_path, "heatmap_meta_*.json"))
                overlay_files = glob.glob(os.path.join(day_path, "overlay_*.jpg"))
                
                # Если есть файлы, оставляем только последний набор
                if data_files:
                    # Сортируем по времени создания (последний сначала)
                    data_files.sort(reverse=True)
                    image_files.sort(reverse=True)
                    meta_files.sort(reverse=True)
                    overlay_files.sort(reverse=True)
                    
                    # Оставляем только последний data файл и соответствующие ему файлы
                    latest_data = data_files[0]
                    timestamp = latest_data.split('_')[-1].replace('.npz', '')
                    
                    # Удаляем все файлы, кроме последнего набора
                    for file_list in [data_files, image_files, meta_files, overlay_files]:
                        for file_path in file_list:
                            if timestamp not in file_path:
                                try:
                                    os.remove(file_path)
                                    logger.info(f"Removed old heatmap: {os.path.basename(file_path)}")
                                except Exception as e:
                                    logger.error(f"Error removing {file_path}: {e}")
                    
                    logger.info(f"Cleaned up old heatmaps for day {day_folder}, kept latest: {timestamp}")
                
        except Exception as e:
            logger.error(f"Error cleaning up old heatmaps: {e}")
    
    def save_heatmap_data(self, heatmap: np.ndarray, start_time: datetime.datetime, 
                         last_frame: Optional[np.ndarray] = None, 
                         stats: Optional[Dict[str, Any]] = None) -> None:
        """Сохраняет тепловую карту и связанные данные"""
        if heatmap is None or np.sum(heatmap) == 0:
            logger.warning("Attempted to save empty heatmap")
            return
        
        try:
            # Получаем папку для текущего дня
            today_folder = self.get_today_folder()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Сохраняем тепловую карту как изображение
            if np.max(heatmap) > 0:
                heatmap_norm = (heatmap / np.max(heatmap) * 255).astype(np.uint8)
                heatmap_colored = cv2.applyColorMap(heatmap_norm, cv2.COLORMAP_JET)
                image_filename = os.path.join(today_folder, f"heatmap_{timestamp}.png")
                cv2.imwrite(image_filename, heatmap_colored)
                logger.info(f"Heatmap image saved: {image_filename}")
            
            # Сохраняем данные тепловой карты в numpy формате
            data_filename = os.path.join(today_folder, f"heatmap_data_{timestamp}.npz")
            np.savez_compressed(
                data_filename,
                heatmap=heatmap,
                start_time=start_time.isoformat(),
                end_time=datetime.datetime.now().isoformat()
            )
            logger.info(f"Heatmap data saved: {data_filename}")
            
            # Сохраняем метаданные
            meta_filename = os.path.join(today_folder, f"heatmap_meta_{timestamp}.json")
            if stats:
                with open(meta_filename, 'w') as f:
                    json.dump(stats, f, indent=2)
                logger.info(f"Heatmap metadata saved: {meta_filename}")
            
            # Сохраняем изображение с наложенной тепловой картой (если есть последний кадр)
            if last_frame is not None:
                overlay_filename = os.path.join(today_folder, f"overlay_{timestamp}.jpg")
                
                # Добавляем дополнительную информацию на изображение
                overlay_with_info = last_frame.copy()
                
                # Добавляем статистику в угол изображения
                if stats:
                    stats_text = [
                        f"Time: {stats.get('total_presence_detailed', 'N/A')}",
                        f"Total Activity: {stats.get('total_activity_points', 0):.0f}",
                        f"Max Activity: {stats.get('max_activity', 0):.0f}",
                        f"Collection: {stats.get('duration_hours', 0):.1f}h"
                    ]
                    
                    # Рисуем полупрозрачный фон для текста
                    overlay_height = overlay_with_info.shape[0]
                    text_bg_height = len(stats_text) * 30 + 20
                    cv2.rectangle(overlay_with_info, 
                                (10, overlay_height - text_bg_height - 10),
                                (300, overlay_height - 10),
                                (0, 0, 0), -1)
                    cv2.rectangle(overlay_with_info, 
                                (10, overlay_height - text_bg_height - 10),
                                (300, overlay_height - 10),
                                (255, 255, 255), 1)
                    
                    # Добавляем текст статистики
                    for i, text in enumerate(stats_text):
                        y_position = overlay_height - text_bg_height + (i + 1) * 25
                        cv2.putText(overlay_with_info, text, (20, y_position),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                
                # Добавляем временную метку
                date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(overlay_with_info, date_str, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                cv2.imwrite(overlay_filename, overlay_with_info, [cv2.IMWRITE_JPEG_QUALITY, 90])
                logger.info(f"Overlay image saved: {overlay_filename}")
            
            # Очищаем старые тепловые карты
            self.cleanup_old_heatmaps(today_folder)
            
        except Exception as e:
            logger.error(f"Error saving heatmap data: {e}")
            raise
    
    def load_latest_heatmap(self) -> Optional[Dict[str, Any]]:
        """Загружает последнюю сохраненную тепловую карту"""
        try:
            # Ищем все папки с датами
            day_folders = [f for f in os.listdir(self.heatmap_save_dir) 
                          if os.path.isdir(os.path.join(self.heatmap_save_dir, f)) 
                          and f.isdigit() and len(f) == 8]
            
            if not day_folders:
                logger.info("No heatmap data found to load")
                return None
            
            # Сортируем папки по дате (последняя сначала)
            day_folders.sort(reverse=True)
            
            # Ищем последний data файл в самой свежей папке
            latest_folder = os.path.join(self.heatmap_save_dir, day_folders[0])
            heatmap_files = [f for f in os.listdir(latest_folder) if f.startswith("heatmap_data_")]
            
            if not heatmap_files:
                logger.info(f"No heatmap files found in {latest_folder}")
                return None
            
            # Берем самый свежий файл в папке
            latest_file = sorted(heatmap_files)[-1]
            filepath = os.path.join(latest_folder, latest_file)
            
            # Загружаем данные
            data = np.load(filepath)
            heatmap = data['heatmap']
            start_time = datetime.datetime.fromisoformat(data['start_time'])
            
            logger.info(f"Heatmap loaded from: {os.path.join(day_folders[0], latest_file)}")
            
            return {
                'heatmap': heatmap,
                'start_time': start_time
            }
            
        except Exception as e:
            logger.error(f"Error loading heatmap: {e}")
            return None
    
    def get_heatmap_files_info(self) -> Dict[str, Any]:
        """Возвращает информацию о всех сохраненных тепловых картах"""
        try:
            day_folders = [f for f in os.listdir(self.heatmap_save_dir) 
                          if os.path.isdir(os.path.join(self.heatmap_save_dir, f)) 
                          and f.isdigit() and len(f) == 8]
            
            heatmaps_info = {}
            total_size = 0
            
            for day_folder in sorted(day_folders, reverse=True):
                day_path = os.path.join(self.heatmap_save_dir, day_folder)
                data_files = glob.glob(os.path.join(day_path, "heatmap_data_*.npz"))
                
                if data_files:
                    # Берем последний файл дня
                    latest_file = sorted(data_files)[-1]
                    file_size = os.path.getsize(latest_file)
                    total_size += file_size
                    
                    heatmaps_info[day_folder] = {
                        'latest_file': os.path.basename(latest_file),
                        'size_mb': file_size / (1024 * 1024),
                        'file_count': len([f for f in os.listdir(day_path) if os.path.isfile(os.path.join(day_path, f))])
                    }
            
            return {
                'total_days': len(heatmaps_info),
                'total_size_mb': total_size / (1024 * 1024),
                'heatmaps_by_day': heatmaps_info
            }
            
        except Exception as e:
            logger.error(f"Error getting heatmap files info: {e}")
            return {}