import talib as ta

def signal(df, *args):
    n = args[0]
    ma = df['close'].rolling(window=n).mean()
    wma = ta.WMA(df['close'], n)
    gap = wma - ma
    df['Gap_bh_%s' %n] = gap / abs(gap).rolling(window=n).sum()