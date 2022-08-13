import routes.public
import routes.maimai
from app import app
import asyncio

app.run(host='0.0.0.0', port=8333, loop=asyncio.get_event_loop())
