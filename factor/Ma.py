

def signal(df, *args):
    """
     
    """
    n = args[0]
    df['Ma_bh_%s' %n] = df['close'].rolling(n).mean()

    return df