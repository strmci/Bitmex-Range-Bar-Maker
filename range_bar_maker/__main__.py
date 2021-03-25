import asyncio
import zmq
from .websocket_receiver import BitmexWebsocketReceiver
from .range_bar_maker import RangeBarMaker
from .config import CFG
from .logger import get_logger


async def main():
    # bitmex websocket
    bitmex_ws_uri = "wss://www.bitmex.com/realtime?subscribe=instrument:" + CFG.PAIR

    # create ZMQ publisher
    zmq_context = zmq.Context()
    zmq_publisher = zmq_context.socket(zmq.PUB)
    zmq_publisher.bind("tcp://*:%s" % CFG.ZMQ_PORT)

    # logger
    logger = get_logger()

    # run range bar maker with websocket connection
    range_bar_maker = RangeBarMaker(bitmex_ws_uri, zmq_publisher, logger,
                                    CFG.RANGE_BAR_PERCENT, CFG.TICK_LOGGING_INTERVAL, CFG.STOP_RANGE_BARS_CREATION,
                                    CFG.START_RANGE_BAR_CREATION, CFG.MINIMUM_BAR_TIME, CFG.PAIR)
    ws = BitmexWebsocketReceiver(range_bar_maker.uri, range_bar_maker.make_range_bar, logger)
    await ws.run_receive()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
