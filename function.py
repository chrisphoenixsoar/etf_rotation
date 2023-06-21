import os
import pandas as pd
import numpy as np
from multiprocessing import Pool, cpu_count
from functools import reduce



def adjusted_day(df, model='qfq'):
    '''
    复权
    model:qfq-前复权，hfq-后复权
    '''
    # 计算复权涨跌幅
    df['change'] = df['close'] / df['pre_close'] - 1
    df['adj'] = (1 + df['change']).cumprod()
    df['close_old'] = df['close']  # 记录没有复权的价格
    if model == 'hfq':
        # 计算后复权价
        df['close'] = df['adj'] * (df.iloc[0]['close'] / df.iloc[0]['adj'])
    elif model == 'qfq':
        # 计算前复权价
        df['close'] = df['adj'] * (df.iloc[-1]['close'] / df.iloc[-1]['adj'])
    # 计算复权的开盘价、最高价、最低价
    df['open'] = df['open'] / df['close_old'] * df['close']
    df['high'] = df['high'] / df['close_old'] * df['close']
    df['low'] = df['low'] / df['close_old'] * df['close']
    del df['adj'], df['close_old'], df['change']

    return df

def import_benchmark_index(path, start, end):
    """
    time_col:time col name
    """
    # 导入业绩比较基准 
    benchmark = pd.read_csv(path + '/sh000300.csv', encoding='gbk', parse_dates=['date'])
    benchmark.drop_duplicates(subset=['date'], inplace=True)
    benchmark.sort_values(by='date', inplace=True)
    benchmark['基准涨跌幅'] = benchmark['close'].pct_change()
    benchmark['基准涨跌幅'].fillna(value=benchmark['close'] / benchmark['open'] - 1, inplace=True)  # 第一天的涨跌幅
    benchmark.rename(columns={'amount': '基准成交量'}, inplace=True)
    benchmark['index_close']=benchmark['close']
    # 只保留需要的数据
    benchmark = benchmark[['date', '基准涨跌幅', '基准成交量','index_close']]
    benchmark.reset_index(inplace=True, drop=True)

    return benchmark

def read_index_and_cal_factor(benchmark, path, rotation_list, usecols, 
                                    factor_config_list, indi_config_dict):
    all_df_list = list()
    # symbol_list = list(set(rotation_list + list(indi_config_dict.keys())))
    # print(set(rotation_list))
    symbol_list = rotation_list
    for index in symbol_list:                    #逐个读入etf行情数据
        # print(index)               
        df = pd.read_csv(path + f'/{index}.csv',  parse_dates=["date"])       
        symbol = index
        # 将K线数据和基准数据合并，填充没有交易的数据
        df['symbol'] = df['code']
        df.drop_duplicates(subset=['date'], inplace=True)   
        df.sort_values(by='date', inplace=True)
        df = adjusted_day(df)                              #复权
        df['pre_close'] = df['close'].shift()
        df = merge_with_benchmark(df, benchmark, time_col='date')
        df['pre_close'].fillna(method='ffill', inplace=True)
        df.reset_index(inplace=True, drop=True)

        # 开始计算因子
        factor_list = []  # 用于记录因子的列名
        if symbol in rotation_list:
            for factor_config in factor_config_list:
                factor = factor_config['factor']
                factor_list.append(factor)
                cls = __import__('factor.%s' % factor, fromlist=('',))
                for n in factor_config['params_list']:
                    df = getattr(cls, 'signal')(df, n)
            df['pct'] = df['close'].pct_change(1)
            
        # 判断是否计算辅助因子
        for k in indi_config_dict.keys():
            if symbol == k:
                for factor_dict in indi_config_dict[k]:
                    factor = factor_dict['factor']
                    factor_list.append(factor)
                    cls = __import__('factor.%s' % factor, fromlist=('',))
                    para_list = factor_dict['params_list']
                    for para in para_list:
                        df = getattr(cls, 'signal')(df, para)
        # 重命名
        rename_dict = dict()
        factor_cols = list(filter(lambda x:any([y in x for y in factor_list]), df.columns))
        # print(factor_cols)
        if symbol not in rotation_list:
            _usecols = ['date'] + factor_cols
        else:
            _usecols = usecols + factor_cols
        df = df[_usecols]
        for col in _usecols:
            if col == 'date':
                continue
            rename_dict[col] = symbol + '_' + col
        df.rename(columns=rename_dict, inplace=True)
        # print(df.tail(2))
        all_df_list.append(df)       
        # print(all_df_list[0].head(10))
    
    all_df = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer'), all_df_list)
    # 删除因子为空的记录
    # all_factor_cols = list(filter(lambda x:any([y in x for y in factor_list]), df.columns))
    # all_df.dropna(subset=all_factor_cols, how="all", inplace=True)
    all_factor_cols=list(all_df.columns) 
    all_factor_cols.remove('date')
    all_df.dropna(subset=all_factor_cols, how="all", inplace=True)

    return all_df

def merge_with_benchmark(df, benchmark, time_col='candle_begin_time'):
    """
     
    :param df:  
    :param benchmark:  
    :return:
    """

    # end = df[time_col].max()  # k线结束时间
    # ===将benchmark数据合并，并且排序
    df = pd.merge(left=df, right=benchmark, on='date', how='right', sort=True, indicator=True)

    # ===对开、高、收、低、前收盘价价格进行补全处理
    # 用前一个周期的收盘价，补全收盘价的空值
    df['close'].fillna(method='ffill', inplace=True)
    # 用收盘价补全开盘价、最高价、最低价的空值
    df['open'].fillna(value=df['close'], inplace=True)
    df['high'].fillna(value=df['close'], inplace=True)
    df['low'].fillna(value=df['close'], inplace=True)

    # ===将停盘时间的某些列，数据填补为0
    fill_0_list = ['quote_volume', 'amount']
    fill_0_list = list(set(fill_0_list).intersection(set(df.columns)))
    df.loc[:, fill_0_list] = df[fill_0_list].fillna(value=0)

    # ===用前一个周期的数据，补全其余空值
    df.fillna(method='ffill', inplace=True)

    # ===删除该币种还未上市的日期
    df.dropna(subset=['symbol'], inplace=True)

    # ===判断计算当前周期是否交易
    df['是否交易'] = 1
    df.loc[df['_merge'] == 'right_only', '是否交易'] = 0

    # 删除退市之后的数据
    # df = df[df[time_col] <= end]

    # 删除不需要的字段
    df.drop(labels=['_merge', '基准涨跌幅', '基准成交量'], axis=1, inplace=True)

    df.reset_index(drop=True, inplace=True)

    return df
# 通用功能：=======================

def appendmax(sr):
    one = sr.idxmax()  # 获取 Series 的最大值的索引值
    maxindex = pd.Series(one)
    sr = sr.append(maxindex)

    return sr

def max_style(x, index_list):
    """ 
    选出值最大的那一列的列名 
    """
    x = np.array(x)
    # 下面这个加了个条件：最大值为正
    # if len(x[x > 0]) == 0:
    #     return np.nan
    # else:
    #     return index_list[np.argsort(x)[~np.isnan(np.sort(x))][-1]]
    if any(~np.isnan(np.sort(x))):
        return index_list[np.argsort(x)[~np.isnan(np.sort(x))][-1]]
    else:
        return 'cash'

def max_value(x):
    '''
    选出序列中的最大值
    '''
    x = np.array(x)
    if any(~np.isnan(np.sort(x))):
        return x[np.argsort(x)[~np.isnan(np.sort(x))][-1]]
    else:
        return -10000


def evaluate_investment(source_data, tittle,time='交易日期'):
    temp = source_data.copy()
    # ===新建一个dataframe保存回测指标
    results = pd.DataFrame()

    # ===计算累积净值
    results.loc[0, '累积净值'] = round(temp[tittle].iloc[-1], 2)

    # ===计算年化收益
    annual_return = (temp[tittle].iloc[-1]) ** (
            '1 days 00:00:00' / (temp[time].iloc[-1] - temp[time].iloc[0]) * 365) - 1
    results.loc[0, '年化收益'] = str(round(annual_return * 100, 2)) + '%'

   
    # 计算当日之前的资金曲线的最高点
    temp['max2here'] = temp[tittle].expanding().max()
    # 计算到历史最高值到当日的跌幅，drowdwon
    temp['dd2here'] = temp[tittle] / temp['max2here'] - 1
    # 计算最大回撤，以及最大回撤结束时间
    end_date, max_draw_down = tuple(temp.sort_values(by=['dd2here']).iloc[0][[time, 'dd2here']])
    # 计算最大回撤开始时间
    start_date = temp[temp[time] <= end_date].sort_values(by=tittle, ascending=False).iloc[0][time]
    # 将无关的变量删除
    temp.drop(['max2here', 'dd2here'], axis=1, inplace=True)
    results.loc[0, '最大回撤'] = format(max_draw_down, '.2%')
    results.loc[0, '最大回撤开始时间'] = str(start_date)
    results.loc[0, '最大回撤结束时间'] = str(end_date)

    # ===年化收益/回撤比 
    results.loc[0, '年化收益/回撤比'] = round(annual_return / abs(max_draw_down), 2)

    return results.T
