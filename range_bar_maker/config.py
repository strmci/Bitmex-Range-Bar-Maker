class CFG:
    # exchange variables = trading pair
    PAIR = "XBTUSD"

    # this will change how many times the last tick will be logged with logger
    TICK_LOGGING_INTERVAL = 50

    # RANGE_BAR_PERCENT = 1  if price is 10000, next bar will have a height of 100
    RANGE_BAR_PERCENT = 1

    # volatility filter
    # stop doing range bars - if difference of last two ticks is bigger than
    # STOP_RANGE_BARS_CREATION height, stop range bar creation
    STOP_RANGE_BARS_CREATION = 50
    # if average volatility decrease below START_RANGE_BAR_CREATION, start creating range bars again
    START_RANGE_BAR_CREATION = 5

    # time filter
    # every bar has to have at least MINIMUM_BAR_TIME seconds
    MINIMUM_BAR_TIME = 15

    # port for sending range bars to trading strategies
    ZMQ_PORT = 10200

