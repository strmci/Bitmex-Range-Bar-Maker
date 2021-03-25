# Range Bar Maker

This program receives the last bitcoin price from bitmex exchange via websocket connection and uses it to create and send range bars to trading strategies. Every range bar is created with a different height - as a percentage (parameter RANGE_BAR_PERCENT) of the last close. When the range bar is finished it is saved and sent via zeromq message to the trading strategy. Saved range bars can be used to backtest strategies, eg. with Multicharts software.

## Range bar filters:
Created range bars can be bigger than RANGE_BAR_PERCENT because of two filters:

volatility filter: 
When the price difference between the last two prices increases significantly (the difference between last two prices is bigger than STOP_RANGE_BARS_CREATION), the range bar maker stops creating new range bars until the volatility got back to normal (parameter START_RANGE_BAR_CREATION).

time filter: 
Every bar has to have MINIMUM_BAR_TIME seconds as its minimum duration, this ensures strategies have enough time to process orders.

Installation:

Python version: 3.7
 
To install requirements and related Python packages: 

`pip install -r requirements.txt`

Run:

`python -m range_bar_maker`

Check range_bar_maker/config.py to change adjustable parameters.

If you find this repo useful or you would like to collaborate on range bar strategies send me a message to strmci@protonmail.com.
