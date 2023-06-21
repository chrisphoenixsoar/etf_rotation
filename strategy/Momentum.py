import pandas as pd 
import numpy as np 
from function import *

def rotation_strategy(df, params, **kwargs):
    """
    轮动策略,
    :param df: 轮动池中所有标的的因子值
    :param params:
    :return:
    """
    
    n = params[0]  
    time_col = kwargs['time_col']
    
    compare_column_list = [x for x in df.columns if f'Zhangdiefu_bh_{n}' in x]
    #选出值最大那一列的名称
    df["style"] = df[compare_column_list].apply(max_style, args=(compare_column_list,), axis=1)
    df['style'] = df['style'].str.split('_').str[0]   
    df['style'].fillna(method='ffill', inplace=True)
    df = df[df[time_col] >= pd.to_datetime(kwargs['start_date'])]
    
    # 选出序列中的最大值，对标的进行轮动的判断
    df[f'style_Zhangdiefu_bh_{n}'] = df[compare_column_list].apply(max_value, axis=1)
    df.loc[df[f'style_Zhangdiefu_bh_{20}'] < 0.005, 'style'] = 'cash'           #期间涨幅小于0.5%则持有现金
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