import pandas as pd 
import numpy as np
import talib as ta


def sma(data, freq,window, plot_data={1:[('SMA',None, 'red')]}):
    
    df=data.copy()
    
    freq = f"{freq}min"
    df = df.resample(freq).agg({"Open": "first", "High": "max", "Low": "min", "Close": "last",  'spread':'mean','pips':'mean'}).dropna()
        
    df["returns"] = np.log(df['Close'] / df['Close'].shift(1))
    df['position']=np.nan
    df['SMA']=df['Close'].rolling(window=window).mean()
    first_cross_idx=df.index[0]
    df['Close_shifted']=df['Close'].shift(1)
    
    for i in range(len(df)):
        condition1_one_bar=((df['Open'].iloc[i]<df['SMA'].iloc[i]) & (df['Close'].iloc[i]>df['SMA'].iloc[i]))
        condition2_one_bar=((df['Open'].iloc[i]>df['SMA'].iloc[i]) & (df['Close'].iloc[i]<df['SMA'].iloc[i]))
        condition1_two_bars=((df['Close_shifted'].iloc[i]>df['SMA'].iloc[i]) & (df['Close'].iloc[i]<df['SMA'].iloc[i]))
        condition2_two_bars=((df['Close_shifted'].iloc[i]<df['SMA'].iloc[i]) & (df['Close'].iloc[i]>df['SMA'].iloc[i]))
        
           
        if condition1_one_bar or condition1_two_bars or condition2_one_bar or condition2_two_bars:
            
            first_cross_idx=df.index[i]
            break
            
    conditions=[
    (df['Close']>df['SMA']) & (df.index>=first_cross_idx),
    (df['Close']<df['SMA']) & (df.index>=first_cross_idx),
    ]
    values=[1,-1]
    df["position"] = np.select(conditions, values,0)
    
    
    
    df.dropna(inplace = True)
    
    return df

def adx(data , freq=14, window=20, down_level=25, plot_data={2:[('plus_di',None, 'green'),('minus_di',None,'red'),           ('adx','down_level', 'blue')]}):

        ''' Prepares the Data for Backtesting.
        '''
        df = data.copy()

        freq = f"{freq}min"

        df = df.resample(freq).agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "vol": "sum", 'spread':'mean','pips':'mean'}).dropna()

        df["returns"] = np.log(df['Close'] / df['Close'].shift(1))

        df['adx']=ta.ADX(df['High'],df['Low'], df['Close'], window)
        df['plus_di']=ta.PLUS_DI(df['High'],df['Low'], df['Close'], window)
        df['minus_di']=ta.MINUS_DI(df['High'],df['Low'], df['Close'], window)
        

        conditions=[ (df['plus_di']>df['minus_di']) & (df['adx']>down_level),
                     (df['minus_di']>df['plus_di']) & (df['adx']>down_level)]

        values=[1,-1]

        df['position']=np.select(conditions,values,0)

        df.dropna(inplace = True)


        return df
    
def rsi(data, freq=30, window=14, up_level=70, down_level=30,neutral_level_dist=0, bars_ob=1, plot_data={2:[('RSI',['up_level','down_level'], 'blue')]}):
    
    ''' Prepares the Data for Backtesting.
    '''
    df = data.copy()

    freq = f"{freq}min"

    df = df.resample(freq).agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "vol": "sum", 'spread':'mean','pips':'mean'}).dropna()
        
    df["returns"] = np.log(df['Close'] / df['Close'].shift(1))
    
    #calculating RSI with talib
    df['RSI']=ta.RSI(df['Close'], window)
    
    df['RSI_shifted']=df['RSI'].shift(1)
    
    df['bar_ob']=np.where(((df['RSI']>up_level) | (df['RSI']<down_level)),1,0 )
    df['temp_sum']=df['bar_ob'].eq(0).cumsum()
    df['bar_ob_sum']=df.groupby('temp_sum').bar_ob.transform('cumsum')
    
            
    
    df['bar_ob_sum']=df['bar_ob_sum'].shift(1)
    
    
    if ((neutral_level_dist==None) | (neutral_level_dist==0)):
        conditions=[((df['RSI']<up_level )& (df['RSI_shifted']>up_level)) & (df['bar_ob_sum']>=bars_ob),
                   ((df['RSI']>down_level) & (df['RSI_shifted']<down_level)) & (df['bar_ob_sum']>=bars_ob)]
         
        values=[-1,1]
            
        df['position']=np.select(conditions,values,0)
        
        df['position']=df['position'].replace(to_replace=0, method='ffill')

    else:
        
        neutral_level_up=up_level-neutral_level_dist
        neutral_level_down=down_level+neutral_level_dist
        neutral_level_max=(up_level+down_level)/2

        if (neutral_level_up < neutral_level_max) or (neutral_level_down > neutral_level_max):
            neutral_level_up=neutral_level_max
            neutral_level_down=neutral_level_max
            print(f'Neutral levels are overlapping and neutral level is set to midpoint - {neutral_level_max}')

       
        #conditions
        conditions=[((df['RSI']<up_level )& (df['RSI_shifted']>up_level)) & (df['bar_ob_sum']>=bars_ob),
                   ((df['RSI']>down_level) & (df['RSI_shifted']<down_level)) & (df['bar_ob_sum']>=bars_ob),

                   (df['RSI']<neutral_level_up )& (df['RSI_shifted']>neutral_level_up) ,
                   (df['RSI']>neutral_level_down) & (df['RSI_shifted']<neutral_level_down)]

        #to handle taking neutral position, there are additoinal conditions with values of -2 and 2
        values=[-1,1,-2,2]


        df['position']=np.select(conditions,values,0)



        df['position']=df['position'].replace(to_replace=0, method='ffill')


        df['position']=df['position'].replace({-2:0,2:0})

    
        
 
    return df