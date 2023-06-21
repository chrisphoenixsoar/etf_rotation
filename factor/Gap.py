import talib as ta

def signal(df, *args):
    
    """
     计算n日加权移动平均和简单移动平均之差的变动幅度
    """
    
    n = args[0]
    ma = df['close'].rolling(window=n).mean()
    wma = ta.WMA(df['close'], n)
    gap = wma - ma
    df['Gap_bh_%s' %n] = gap / abs(gap).rolling(window=n).sum()
    
    return df