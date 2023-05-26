import pandas as  pd
import tushare as ts
from datetime import datetime
import backtrader as bt
import matplotlib
class gloVar:
    buy_count = 0
    sell_count = 0

class Bollstrategy(bt.Strategy):
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s,%s' % (dt.isoformat(), txt))

    def __init__(self):
        # 指定价格序列
        self.dataclose = self.datas[0].close

        #交易订单状态初始化
        self.order = None

        #计算布林线
        ##使用自带的indicators中自带的函数计算出支撑线和压力线，period设置周期，默认是20
        self.lines.top = bt.indicators.BollingerBands(self.datas[0], period=20).top
        self.lines.bot = bt.indicators.BollingerBands(self.datas[0], period=20).bot

    def next(self):
        # 检查订单状态
        if self.order:
            print("等待成交")
            return

        # 检查持仓
        if not self.position:
            # 没有持仓，买入开仓
            if self.dataclose <= self.lines.bot[0]:
                print("================")
                print("收盘价跌破lower线，执行买入")
                self.order = self.buy()
        else:
            # 手里有持仓，判断卖平
            if self.dataclose >= self.lines.top[0]:
                print("======================")
                print("收盘价超过upper线，执行卖出")
                self.order = self.sell()

    def notify(self, order):

        if order.status in [order.Submitted, order.Accepted]:
            if order.status in [order.Submitted]:
                self.log("提交订单......")
            if order.status in [order.Accepted]:
                self.log("接受订单......")
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enougth cash
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            if order.isbuy():
                self.log('执行买入, %.2f' % order.executed.price)
                gloVar.buy_count = gloVar.buy_count + 1
            elif order.issell():
                self.log('执行卖出, %.2f' % order.executed.price)
                gloVar.sell_count = gloVar.sell_count + 1
            self.bar_executed = len(self)

        self.log("订单完成......")
        print("======================")
        # Write down: no pending order
        self.order = None


token = '6aecc221a107b6aa227fb3d1765d85c0eeacfa2a4abf4d6d98b57023'
ts.set_token(token)
pro = ts.pro_api(timeout=60)
# 指定股票代码
ts_code = '000001.SZ'
code = '000001'
start_date = '20200101'
# 获取数据
def get_data(start):
    df = ts.pro_bar(ts_code=ts_code, adj='qfq', start_date=start)
    df = df.iloc[::-1]
    df.index = pd.to_datetime(df.trade_date)
    df['openinterest'] = 0
    df = df[['open', 'high', 'low', 'close', 'vol', 'openinterest']]
    df = df.rename(columns={'vol': 'volume'})
    return df

start_time = '2020-01-01'
accept_date ='2022-12-01'  # 查找这个日期是买入卖出点的股票

#加载数据
start = datetime.strptime(start_time, "%Y-%m-%d")
end = datetime.strptime(accept_date, "%Y-%m-%d")
buy_count = 0   # 买入次数
sell_count = 0   # 卖出次数
k_line_data = get_data(start.date().strftime("%Y%M%D"))
print(k_line_data)
k_line_data.to_csv("csvfile\\" + ts_code + ".csv")
data = bt.feeds.PandasData(dataname=k_line_data, fromdate=start, todate=end)

# 加载backtrader引擎
back_trader = bt.Cerebro()
# 将数据传入
back_trader.adddata(data)
# 策略加进来
back_trader.addsizer(bt.sizers.FixedSize, stake=2000)
# 设置以收盘价成交，作弊模式
back_trader.broker.set_coc(True)
# 账号资金初始化
startCash = 100000
back_trader.broker.set_cash(startCash)
# 设置手续费
back_trader.broker.setcommission(commission=0.001)


# 布林线规则：跌破下轨，买入；超过上轨，卖出
back_trader.addstrategy(Bollstrategy)

# 输出初始化数据
d1 = start.date().strftime("%Y-%m-%d")
d2 = end.date().strftime("%Y-%m-%d")
print(f'初始化资金：{startCash},回测时间：{d1}：{d2}')
# 开启回测
result = back_trader.run()

# Print out the final result
print('最终资金: %.2f' % back_trader.broker.getvalue())
profit_ratio = (int(back_trader.broker.getvalue()) - startCash) / startCash * 100
print('投资收益率: %.2f%%' % profit_ratio)

print('买入次数：%s ；卖出次数：%s' % (gloVar.buy_count, gloVar.sell_count))
print("股票代码：%s" %ts_code)
# Plot the result
back_trader.plot()

