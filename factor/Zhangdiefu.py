def signal(df, *args):
    """
     计算n日涨跌幅
    """
    n = args[0]
    df['Zhangdiefu_bh_%s' %n] = df['close'].pct_change(periods=n)

    return df