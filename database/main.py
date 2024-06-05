import routes.public
import routes.maimai
import routes.chunithm
import routes.ci
from app import app
import asyncio

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8333, loop=asyncio.get_event_loop(), use_reloader=False)
