import os
import socket
import logging
from flask_app import create_app
from livereload import Server

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
    app = create_app()

    # Let livereload serve instead of app.run()
    port = find_free_port()
    logging.info(f"Starting live‑reload Flask on http://127.0.0.1:{port}")

    server = Server(app.wsgi_app)
    # watch templates and static folders (adjust paths as needed)
    server.watch('flask_app/templates/')
    server.watch('flask_app/static/')
    # you can also watch your Python files if you like:
    server.watch('flask_app/**/*.py')

    server.serve(
        host='127.0.0.1',
        port=port,
        debug=True,
        use_reloader = False,
        restart_delay=0.2  # tweak if you like
    )
