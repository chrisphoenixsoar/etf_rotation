import pandas as pd
import numpy as np
import quantstats as qs
from function import *
from config import *
import glob
import matplotlib.pyplot as plt
from functools import reduce
pd.set_option('expand_frame_repr', False)  
pd.set_option('display.max_rows', 5000)  



def backtest_for_rotation(path, rotation_list, start_time, end_time, usecols,
                     factor_config_list, indi_config_dict, strategy_config):
   
    # 读取基准
    benchmark = import_benchmark_index(index_path, start_time, end_time)
    # 读取数据+计算指标
    df = read_index_and_cal_factor(benchmark, path, rotation_list, usecols, 
                                    factor_config_list, indi_config_dict)
    # 轮动策略+过滤：封装在strategy
    strategy = strategy_config['strategy']
    para = strategy_config['para']
    cls = __import__('strategy.%s' % strategy, fromlist=('',))
    df = getattr(cls, 'rotation_strategy')(df, para, start_date=start_time, rotation_list=rotation_list, time_col='date')

    # 收盘确定下期标的，实际的持仓要晚一个交易日
    df['pos'] = df['style'].shift(1)

    # 删除持仓为nan的天数
    df.dropna(subset=['pos'], inplace=True)

    # 计算策略的整体涨跌幅strategy_pct
    for symbol in rotation_list:
        df.loc[df['pos'] == symbol, 'strategy_pct'] = df[f'{symbol}_pct']      #持仓标的收益率赋值给策略收益率
    df.loc[df['pos'] == 'cash', 'strategy_pct'] = 0

    # 调仓时间
    df.loc[df['pos'] != df['pos'].shift(1), 'trade_time'] = df['date']
    
    
    # 收盘前卖出持仓标的，下一交易日开盘买入新标的。这样设置的原因在于避免a股常态性低开，消除隔夜风险。
    
    # 将调仓日的新买入标的涨跌幅修正为开盘价买入涨跌幅
    for symbol in rotation_list:
        df.loc[(df['trade_time'].notnull()) & (df['pos'] == symbol), 'strategy_pct_adjust'] = df[f'{symbol}_close'] / (
            df[f'{symbol}_open'] * (1 + trade_rate)) - 1
    df.loc[df['trade_time'].isnull(), 'strategy_pct_adjust'] = df['strategy_pct']

    # 在尾盘卖出原仓位，扣除手续费 
    df.loc[(df['trade_time'].shift(-1).notnull()) & (df['pos'] != 'cash'), 'strategy_pct_adjust'] = (1 + df[
        'strategy_pct']) * (1 - trade_rate) - 1

    # 空仓期间涨跌幅用0填充
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
    benchmark['HS300']=benchmark['index_close']
   
    res = evaluate_investment(df, 'strategy_net', time='date')
    print(res)
    #生成策略报告
    qs.reports.html(returns=df['strategy_net'],benchmark=benchmark['HS300'],output=path+'\quantstats-tearsheet.html',\
                    title=f"{strategy_config['strategy']}")        
    print(f"Please review the report at {path}/quantstats-tearsheet.html")

    # # 绘图
    plt.plot(df['date'], df['strategy_net'], label='strategy')   
    plt.legend()
    plt.show()
   
    # 保存文件
    df.to_csv(f"{strategy_config['strategy']}.csv", encoding='gbk', index=False)


if __name__ == '__main__':
    backtest_for_rotation(path, rotation_list, start_time, end_time, usecols,
                     factor_config_list, indi_config_dict, strategy_config)



