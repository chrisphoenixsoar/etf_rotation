'''

author:phoenix
    
'''


import pandas as pd
import numpy as np
import quantstats as qs
from function import *
from config import *
import glob
import matplotlib.pyplot as plt
from functools import reduce
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数



def backtest_for_rotation(path, rotation_list, start_time, end_time, usecols,
                     factor_config_list, indi_config_dict, strategy_config):
    '''
     
    '''
    # 先读取基准数据
    benchmark = import_benchmark_index(index_path, start_time, end_time)
    # 读取数据+计算指标
    df = read_index_and_cal_factor(benchmark, path, rotation_list, usecols, 
                                    factor_config_list, indi_config_dict)
    # 轮动策略+过滤：封装到strategy
    strategy = strategy_config['strategy']
    para = strategy_config['para']
    cls = __import__('strategy.%s' % strategy, fromlist=('',))
    df = getattr(cls, 'rotation_strategy')(df, para, start_date=start_time, rotation_list=rotation_list, time_col='date')

    # 收盘才能确定风格，实际的持仓pos要晚一周期。
    df['pos'] = df['style'].shift(1)

    # 删除持仓为nan的天数
    df.dropna(subset=['pos'], inplace=True)

    # 计算策略的整体涨跌幅strategy_pct
    for symbol in rotation_list:
        df.loc[df['pos'] == symbol, 'strategy_pct'] = df[f'{symbol}_pct']
    df.loc[df['pos'] == 'cash', 'strategy_pct'] = 0

    # 调仓时间
    df.loc[df['pos'] != df['pos'].shift(1), 'trade_time'] = df['date']

    # 将调仓日的涨跌幅修正为开盘价买入涨跌幅
    for symbol in rotation_list:
        df.loc[(df['trade_time'].notnull()) & (df['pos'] == symbol), 'strategy_pct_adjust'] = df[f'{symbol}_close'] / (
            df[f'{symbol}_open'] * (1 + trade_rate)) - 1
    df.loc[df['trade_time'].isnull(), 'strategy_pct_adjust'] = df['strategy_pct']

    # 在尾盘卖出，扣除卖出手续费 
    df.loc[(df['trade_time'].shift(-1).notnull()) & (df['pos'] != 'cash'), 'strategy_pct_adjust'] = (1 + df[
        'strategy_pct']) * (1 - trade_rate) - 1

    # 空仓的日子，涨跌幅用0填充
    df['strategy_pct_adjust'].fillna(value=0.0, inplace=True)
    del df['strategy_pct'], df['style']
    df.reset_index(drop=True, inplace=True)

    # 计算净值
    for symbol in rotation_list:
        df[f'{symbol}_net'] = df[f'{symbol}_close'] / df[f'{symbol}_close'][0]
    df['strategy_net'] = (1 + df['strategy_pct_adjust']).cumprod()
    
    benchmark['date']=pd.to_datetime(benchmark['date'])
    benchmark.index = benchmark['date']

    benchmark=benchmark[(benchmark.index>=df.loc[0,'date']) & (benchmark.index<=df.loc[len(df)-1,'date'])]
    df.index=df['date']

    # benchmark=benchmark['close']
    
    qs.reports.html(returns=df['strategy_net'],benchmark=benchmark['index_close'],output=f"report_{strategy_config['strategy']}.html")
    # 评估策略的好坏
    # res = evaluate_investment(df, 'strategy_net', time='date')
    # print(res)

    # # 绘制图片
    # plt.plot(df['date'], df['strategy_net'], label='strategy')
    # for symbol in rotation_list:
    #     plt.plot(df['date'], df[f'{symbol}_net'], label=f'{symbol}_net')
    # plt.legend()
    # plt.show()
    # 保存文件
    # print(df.tail(10))
    df.to_csv(f"{strategy_config['strategy']}.csv", encoding='gbk', index=False)


if __name__ == '__main__':
    backtest_for_rotation(path, rotation_list, start_time, end_time, usecols,
                     factor_config_list, indi_config_dict, strategy_config)



