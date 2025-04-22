import socket
import logging
from flask_app import create_app

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
    )
    logging.info("Logging is configured.")

if __name__ == '__main__':
    configure_logging()
    
    # Create the app using the factory
    app = create_app()
    
    port = find_free_port()
    logging.info(f"Starting Flask app on http://127.0.0.1:{port}")
    
    app.run(debug=True, port=port, threaded=True)
