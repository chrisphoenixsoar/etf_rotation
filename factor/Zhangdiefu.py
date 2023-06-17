

def signal(df, *args):
    """
     
    """
    n = args[0]
    df['Zhangdiefu_bh_%s' %n] = df['close'].pct_change(periods=n)

    return df