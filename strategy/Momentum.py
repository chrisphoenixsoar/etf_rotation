import pandas as pd 
import numpy as np 
from function import *

def rotation_strategy(df, params, **kwargs):
    """
    轮动策略,
    :param df: 数据
    :param params:
    :return:
    """
    n = params[0]  # zhangdiefu para
    time_col = kwargs['time_col']
    # 1、轮动指标是涨跌幅20
    compare_column_list = [x for x in df.columns if f'Zhangdiefu_bh_{n}' in x]
    # style 表示轮动到了
    df["style"] = df[compare_column_list].apply(max_style, args=(compare_column_list,), axis=1)
    df['style'] = df['style'].str.split('_').str[0]   
    df['style'].fillna(method='ffill', inplace=True)
    df = df[df[time_col] >= pd.to_datetime(kwargs['start_date'])]
    # 对轮动标的进行交易条件判断
    df[f'style_Zhangdiefu_bh_{n}'] = df[compare_column_list].apply(max_value, axis=1)
    df.loc[df[f'style_Zhangdiefu_bh_{20}'] < 0.01, 'style'] = 'cash'
    return df

def batch_parameters():
    """
    生成遍历的参数
    :return:
    """
    para_list = []
    for n in [5, 10, 20, 30, 60]:
        para_list.append([n])

    return para_list