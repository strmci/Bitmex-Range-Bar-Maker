import json
import websockets
import asyncio


class BitmexWebsocketReceiver:

    RECONNECT_DELAY = 30

    def __init__(self, uri, callback, logger):
        self.uri = uri
        self.callback = callback
        self.ws = None
        self.logger = logger

    async def connect(self):
        self.logger.info('Opening WebSocket connection...')
        self.ws = await websockets.connect(self.uri)
        self.logger.info('WebSocket connected')

    async def run_receive(self):
        await self.connect()
        while True:
            try:
                await self.read_messages()
            except (websockets.ConnectionClosedOK, websockets.ConnectionClosedError):
                self.logger.info('Connection closed, reconnecting...')
                await asyncio.sleep(self.RECONNECT_DELAY)
                await self.connect()
            except Exception as e:
                self.logger.info('Unknown exception: %s' % e)
                await asyncio.sleep(self.RECONNECT_DELAY)
                await self.connect()

    async def read_messages(self):
        while True:
            ws_msg = await self.ws.recv()
            ws_msg = json.loads(ws_msg)
            data = ws_msg.get('data', None)
            last_price = data[0].get('lastPrice', None) if data else None
            if last_price:
                await self.callback(last_price)
