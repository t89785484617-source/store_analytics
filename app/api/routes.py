from flask import Response, render_template_string
import logging

from app.core.camera import Camera

logger = logging.getLogger(__name__)

# Инициализация камеры
camera = Camera()

def init_routes(app):
    @app.route('/')
    def index():
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Store Heatmap Analytics</title>
            <meta charset="UTF-8">
            <style>
                body { margin: 0; padding: 0; background: black; }
                img { width: 100vw; height: 100vh; object-fit: contain; }
                .info { position: absolute; top: 10px; left: 10px; color: white; background: rgba(0,0,0,0.5); padding: 10px; }
            </style>
        </head>
        <body>
            <img src="/video_feed">
        </body>
        </html>
        """)
    
    def generate_frames():
        while True:
            frame = camera.get_frame()
            if frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    @app.route('/video_feed')
    def video_feed():
        return Response(generate_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    
    @app.route('/reset_heatmap')
    def reset_heatmap():
        camera.heatmap_processor.reset_heatmap()
        return "Heatmap reset successfully"
    
    @app.route('/save_heatmap')
    def save_heatmap_route():
        camera.heatmap_processor.save_heatmap()
        return "Heatmap saved successfully"
    
    @app.route('/statistics')
    def statistics():
        stats = camera.heatmap_processor.get_statistics()
        if stats:
            return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Store Analytics</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .stats { background: #f5f5f5; padding: 20px; border-radius: 10px; }
                    .btn { padding: 10px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; text-decoration: none; display: inline-block; }
                    .reset-btn { background: #ff4444; color: white; }
                    .save-btn { background: #44ff44; color: black; }
                </style>
            </head>
            <body>
                <h2>Store Heatmap Statistics</h2>
                <div class="stats">
                    <p><strong>Collection Time:</strong> {{ duration_hours|round(2) }} hours</p>
                    <p><strong>Total Activity:</strong> {{ total_activity|round(0) }} points</p>
                    <p><strong>Max Activity in Zone:</strong> {{ max_activity|round(0) }} points</p>
                    <p><strong>Average Activity:</strong> {{ average_activity|round(2) }} points</p>
                    <p><strong>Total Presence Time:</strong> {{ total_presence }}</p>
                </div>
                <br>
                <a href="/reset_heatmap" class="btn reset-btn">Reset Statistics</a>
                <a href="/save_heatmap" class="btn save-btn">Save Heatmap Now</a>
                <br><br>
                <a href="/">Back to Camera</a>
            </body>
            </html>
            """, **stats)
        return "No statistics available"