import os

# =====回测相关参数
_ = os.path.abspath(os.path.dirname(__file__))  # 返回当前文件路径

path = os.path.abspath(os.path.join(_, 'data', 'etf'))
index_path = os.path.abspath(os.path.join(_, 'data'))


# 轮动池填入etf代码，可增减
rotation_list = ['159915.SZ', '510300.SH', '512690.SH','159632.SZ','511260.SH',\
                 '588050.SH','588200.SH','512010.SH','159857.SZ']
    


# 需要计算的因子和参数
factor_config_list = [
    {
        'factor': 'Zhangdiefu',
        'params_list': [20]
    },
    {
        'factor': 'Gap',
        'params_list': [20]
    },

]

#指数再则择时设置，相关功能待添加
indi_config_dict={}

# rank策略和参数
strategy_config = {
    'strategy':'Momentum',
    'para':[20],
}

# 回测时间
start_time = '2010-01-01'
end_time = '2023-06-08'

# 手续费
trade_rate = 1.2 / 10000  

usecols= ['date','close','pct',  'open']      