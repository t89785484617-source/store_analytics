import flask
import atexit
import logging
from app.config.settings import config
from app.api.routes import init_routes, camera

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_app():
    app = flask.Flask(__name__)
    
    # Инициализация маршрутов
    init_routes(app)
    
    # Функция очистки при завершении
    def cleanup():
        logging.info("Cleaning up resources...")
        camera.cleanup()
    
    atexit.register(cleanup)
    
    return app

if __name__ == '__main__':
    app = create_app()
    try:
        app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
    except KeyboardInterrupt:
        logging.info("Application stopped by user")
    except Exception as e:
        logging.error(f"Application error: {e}")
    finally:
        atexit.unregister(cleanup)
        cleanup()