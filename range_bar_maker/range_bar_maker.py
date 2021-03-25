import os
import pandas as pd
from datetime import datetime
import json


class RangeBarMaker:

    def __init__(self, uri, publisher, logger, range_bar_percent, tick_logging_interval,
                 stop_range_bar_creation, start_range_bar_creation, minimum_bar_time, pair):
        self.uri = uri
        self.range_bar_percent = range_bar_percent
        self.publisher = publisher
        self.pair = pair

        # logger
        self.logger = logger

        # tick logging variables
        self.tick_logging_interval = tick_logging_interval
        self.counter = 0

        # volatility filter variables
        self.old_tick = 0
        self.average_tick = 0
        self.stop_range_bar_creation = stop_range_bar_creation
        self.start_range_bar_creation = start_range_bar_creation
        self.filter_volatility = 0
        self.ticks = []
        self.average_tick = 0

        # time filter variables
        self.filter_time = 0
        self.last_bar_time = datetime.now()
        self.this_bar_time = datetime.now()
        self.minimum_bar_time = minimum_bar_time

        # range bar making variables
        self.range_bar_height = 0
        self.new_bar = 0
        self.high = 0
        self.low = 100000000
        self.last_close = None
        self.bar_count = 1
        self.df = pd.DataFrame(columns=['date', 'time', 'open', 'high', 'low', 'close'])

        # csv backup
        self.csv_filename = "DB/%s_%s.csv" % (self.pair, self.range_bar_percent)
        self.load_csv()

    def load_csv(self):
        """
        This loads last price of last range bar if it is backed up in csv so it can continue creating range bars
        with last data.
        """
        # create DB directory if doesn't exist
        if not os.path.isdir("DB"):
            os.mkdir("DB")

        # try to load history and last close from file
        try:
            range_bar_file = pd.read_csv(self.csv_filename)
            df = pd.DataFrame(range_bar_file.iloc[:, :].values)
            self.last_close = df.iloc[-1][5]
            self.logger.info('Fill in last candles using files SUCCESSFUL, last close: %s' % self.last_close)
        except FileNotFoundError:
            new_history_file = open(self.csv_filename, "x")
            new_history_file.write('date,time,open,high,low,close\n')
            new_history_file.close()
            self.logger.info('Fill in last candles using files FAILED, new DB history file was created')
        except Exception as e:
            new_history_file = open(self.csv_filename, "w")
            new_history_file.write('date,time,open,high,low,close\n')
            new_history_file.close()
            self.logger.info('Fill in last candles using files FAILED, file already exists, '
                        'failed to read any data...')

    def create_json(self, df):
        """
        Prepare json to send via zmq.
        """
        message_dict = {"date": df.iloc[-1][0], "time": df.iloc[-1][1], "open": df.iloc[-1][2],
                        "high": df.iloc[-1][3], "low": df.iloc[-1][4], "close": df.iloc[-1][5], "pair": self.pair}
        return json.dumps(message_dict)

    def send_message(self, json_to_send):
        """
        Send finished bar to strategy using zmq publisher.
        """
        topic = 'RB%sp' % self.range_bar_percent
        self.publisher.send_string("%s|%s" % (topic, json_to_send))
        self.logger.info('ZMQ message sent > Topic: %s Message: %s' % (topic, json_to_send))

    def tick_logging(self, last_price, ticks_diff):
        """
        Logs every 'tick_logging_interval' tick price and absolute difference between last two ticks.
        """
        self.counter += 1
        if self.counter % self.tick_logging_interval == 0:
            self.logger.info("Price: %12s  Last tick difference: %s" % (last_price, ticks_diff))
            self.counter = 0

    def volatility_filter(self, ticks_diff):
        """
        If difference between last two ticks increase significantly, it will stop creating range bars until
        volatility decrease again to normal level.
        """
        if ticks_diff > self.stop_range_bar_creation and self.filter_volatility == 0:
            self.filter_volatility = 1
            self.logger.info('Volatility increased, stop creating range bars.')
            self.logger.info('Threshold to start creating range bars again: %s' % self.start_range_bar_creation)

        if self.filter_volatility == 1:
            self.ticks.append(ticks_diff)
            self.average_tick = sum(self.ticks) / len(self.ticks)
            if len(self.ticks) > 100:
                del self.ticks[0]
            self.logger.info('Average ticks: %s' % self.average_tick)

        if self.average_tick < self.start_range_bar_creation and self.filter_volatility == 1:
            self.filter_volatility = 0
            self.average_tick = 0
            self.ticks = []
            self.logger.info('Volatility decreased, starting to create range bars again.')

    def time_filter(self):
        """
        Every range bar has to have at least "minimum bar time" seconds so the strategy has more time to process
        all signals if eg. exchange is not responsive.
        """
        now = datetime.now()
        time_bar_difference = now - self.last_bar_time
        difference_in_secs = time_bar_difference.days * 24 * 60 * 60 + time_bar_difference.seconds
        if difference_in_secs < self.minimum_bar_time:
            if self.filter_time == 0:
                self.logger.info('Time filter activated, time of bar lower than %s seconds, '
                                    'difference in seconds: %s' % (self.minimum_bar_time, difference_in_secs))
            self.filter_time = 1

        if self.filter_time == 1 and difference_in_secs >= self.minimum_bar_time:
            self.filter_time = 0
            self.logger.info('Time filter deactivated, time of bar greater or equal than %s seconds, '
                                'difference in seconds: %s' % (self.minimum_bar_time, difference_in_secs))
        return difference_in_secs

    async def make_range_bar(self, last_price):
        """
        This function process last_price to new range bar, if it is finished - bigger than range_bar_height,
        it is saved and sent.
        """
        if self.old_tick == 0:
            self.old_tick = last_price

        # ticks diff for volatility filter and tick logging
        ticks_diff = abs(last_price - self.old_tick)

        # tick logging
        self.tick_logging(last_price, ticks_diff)

        # volatility filter
        self.volatility_filter(ticks_diff)

        # time bar filter
        difference_in_secs = self.time_filter()

        # new bar creation
        new_high = last_price
        new_low = last_price
        if self.new_bar == 0:
            self.high = 0
            self. low = 100000000
            self.new_bar = 1
            divider = self.range_bar_percent / 100
            self.range_bar_height = last_price * divider
            self.logger.info("New bar, range_bar_height: %s" % self.range_bar_height)

            if self.last_close is not None:
                last_price = self.last_close
            if self.bar_count == 1:
                self.df.loc[self.bar_count, 'open'] = last_price
                new_high = last_price
                new_low = last_price
            else:
                self.df.loc[self.bar_count, 'open'] = self.df.iloc[-1]['close']
                new_high = self.df.iloc[-1]['close']
                new_low = self.df.iloc[-1]['close']
        if new_high > self.high:
            self.high = new_high
            self.df.loc[self.bar_count, 'high'] = self.high
        if new_low < self.low:
            self.low = new_low
            self.df.loc[self.bar_count, 'low'] = self.low

        if (self.high - self.low) > self.range_bar_height:
            if self.filter_volatility == 0 and self.filter_time == 0:
                now = datetime.now()
                self.df.loc[self.bar_count, 'date'] = now.strftime("%Y%m%d")
                self.df.loc[self.bar_count, 'time'] = now.strftime("%H:%M:%S")
                self.df.loc[self.bar_count, 'close'] = last_price
                self.new_bar = 0
                self.bar_count += 1
                self.last_bar_time = datetime.now()

                # prepare data for sending and saving to file
                df_to_csv = self.df.tail(1)
                self.logger.info('New bar finished, time difference of last bars: %s' % difference_in_secs)
                self.logger.info('New bar OHLC:')
                self.logger.info(df_to_csv)

                # send bar to strategy via zmq
                json_to_send = self.create_json(df_to_csv)
                self.send_message(json_to_send)

                # save new bar to csv file
                df_to_csv.to_csv(self.csv_filename, sep=',', encoding='utf-8', header=False, index=False,
                                 float_format='%.8f', mode='a')

                if self.last_close is not None:
                    self.last_close = None

        self.old_tick = last_price

