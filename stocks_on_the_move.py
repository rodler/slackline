# from __future__ import print_function
from datetime import datetime,timedelta
from slackline.core.data_factory import *
from slackline.core.engine import *
from slackline.core.utils import *
from slackline.core.logger import Logging
import cPickle
from scipy import stats
import config.som_config as config
from talib import ATR
import traceback
from pylab import plot, show
from numpy import *
from ipdb import set_trace
import numpy as np
logger = Logging(__name__,'/tmp/slackline.log').logger
# symbols = ['MSFT','AAPL','IBM','CSCO','GOOG','F','XOM','AMZN','GE','T','JPM','WFC','BAC','KO','INTC']
symbols = ['MSFT','AAPL','IBM']

def initialize_csv(context):
    context.ma_lkbk = 200
    context.atr_lkbk = 20
    context.lr_lkbk = 200
    context.max_items = 1
    context.risk_factor = 0.01

def initialize_optimization(context):
    context.ma_lkbk = context.params.rand_ma_lkbk
    context.atr_lkbk = context.params.rand_atr_lkbk
    context.lr_lkbk = context.params.rand_lr_lkbk
    context.max_items = context.params.rand_max_items
    context.risk_factor = 0.00005

def optimisation_params(params):
    params.rand_ma_lkbk = random.randint(90,190)
    params.rand_lr_lkbk = random.randint(90,190)
    params.rand_atr_lkbk = random.randint(16,25)
    params.rand_max_items = random.randint(1,len(symbols))


def handle_data_csv(context):
    long_range_slopes = []
    try:
        liq = context.performance.get_latest_performance()['portfolio_value']
    except:
        print traceback.format_exc()
        liq = 0
    new_pos_sizes = []
    isbull = []
    for symbol in context.data.items:
        hist = get_history(context,symbol,'200D','four')
        MA = mean(hist)
        isbull.append(get_current_price(context,symbol)>MA)
        try:
            lr =stats.linregress(range(len(hist)),hist)
            atr = ATR(asarray(get_history(context,symbol,'41D','two')),
                      asarray(get_history(context,symbol,'41D','three')),
                      asarray(get_history(context,symbol,'41D','four')),
                      context.atr_lkbk)[-1]
            new_pos_sizes.append(floor(liq * context.risk_factor / atr))
            long_range_slopes.append(lr[0]*abs(lr[2])*250)
        except:
            new_pos_sizes.append(np.nan)
            long_range_slopes.append(np.nan)


    tradable_symbols = argsort(long_range_slopes[::-1])[:context.max_items]
    for i,symbol in enumerate(symbols):
        if isnan(new_pos_sizes[i]) or isnan(long_range_slopes[i]): continue
        if symbol in context.portfolio.positions:
            order_size = new_pos_sizes[i] - sum(context.portfolio.positions[symbol])
            if isbull[i] and (i in tradable_symbols) and order_size:
                order(context,symbol,order_size)
            elif not isbull[i] and sum(context.portfolio.positions[symbol]):
                order(context,symbol,-sum(context.portfolio.positions[symbol]))
        else:
            order_size = new_pos_sizes[i]
            if isbull[i] and (i in tradable_symbols) and order_size:
                order(context,symbol,order_size)



def run_csv():
    data = WebDataFactory(symbols,
                          datetime(2003, 1, 1),
                          datetime(2017, 1, 1),
                          source='google')()
    # set_trace()
    strategy = Strategy(config,handle_data=handle_data_csv,initialize=initialize_csv)
    result = strategy.run(data,start=datetime(2004,7,1),finish=datetime(2016,12,12))
    cPickle.dump(result,open('results/result.pick','w'))
    plot(result.pnl)
    show()

def optimize():
    data = WebDataFactory(symbols,
                          datetime(2013, 1, 1),
                          datetime(2017, 1, 1),
                          source='google')()
    optimize = Optimize(config,
                        handle_data=handle_data_csv,
                        init_optimization=optimisation_params,
                        initialize=initialize_optimization)
    optimize.run_mc_sweep(data,numb_runs=300,start=datetime(2014,1,1),finish=datetime(2016,12,12))
    return optimize.results

if __name__=='__main__':
    run_csv()
    # optimize()


