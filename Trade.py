#!/usr/bin/env python3
# coding=utf-8
import re
from futu import *
from IPython.display import display, HTML

from ServiceFeeStocks import ServiceFeeStocksHK,ServiceFeeStocksUS


'''
-  加密 https://openapi.futunn.com/futu-api-doc/ftapi/init.html#2009
- https://openapi.futunn.com/futu-api-doc/trade/get-position-list.html
'''

class Trade:
    def __init__(self,market='US'):
        self.market_ = market
        if 'US' == market:
            self.ctx_ = OpenUSTradeContext(host='127.0.0.1', port=11111, is_encrypt=None, security_firm=SecurityFirm.FUTUSECURITIES)
        elif 'HK' == market:
            self.ctx_ = OpenHKTradeContext(host='127.0.0.1', port=11111, security_firm=SecurityFirm.FUTUSECURITIES)
        else:
            assert False , f'Error market type {market}'
        #print('--------Order List----------')
        #ret, data = self.ctx_.order_list_query(order_id="", status_filter_list=[], code='', start='', end='', trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, refresh_cache=False)
        #print(data)

        pass

    def showPositionsFee(self):
        if 'US' == self.market_:
            sf = ServiceFeeStocksUS()
        elif 'HK' == self.market_:
            sf = ServiceFeeStocksHK()
        p = self.getPositionList()
        #https://zhuanlan.zhihu.com/p/41202576 SettingWithCopyWarning error
        p2= p[['code', 'stock_name', 'qty', 'cost_price','nominal_price',]].copy()
        #insert new coloumn
        f =  sf.fee(p.qty, p.cost_price) *2
        p2.loc[:,'fee'] = f * 2
        p2.loc[:,'low_price'] = f /p.qty + p.cost_price
        display(p2)
        pass

    def getPositionList(self):
        '''

    qty	float	持有数量，期权和期货的单位是“张”
    can_sell_qty	float	可卖数量，期权和期货的单位是“张”
    nominal_price	float	市价，3 位小数，超过四舍五入
    cost_price	float	成本价（证券账户），开仓价（期货账户）
    cost_price_valid	bool	成本价是否有效。True：有效，False：无效
    market_val	float	市值，3位精度(A 股 2 位精度)。期货为 0
    pl_ratio	float	盈亏比例（该字段为百分比字段，默认不展示 %，如 20 实际对应 20%）。（期货不适用）
    pl_ratio_valid	bool	盈亏比例是否有效。True：有效，False：无效
    pl_val	float	盈亏金额，3位精度(A 股 2 位)
    pl_val_valid	bool	盈亏金额是否有效。True：有效，False：无效
    today_pl_val	float	今日盈亏金额，3 位精度(A 股 2 位)，下同
    today_buy_qty	float	今日买入总量（期货不适用）
    today_buy_val	float	今日买入总额（期货不适用）
    today_sell_qty	float	今日卖出总量（期货不适用）
    today_sell_val	float	今日卖出总额（期货不适用）
    unrealized_pl	float	未实现盈亏（仅期货账户适用）
    realized_pl	float	已实现盈亏（仅期货账户适用）

        '''
        #print('--------Position----------')
        ret, data = self.ctx_.position_list_query(code='', pl_ratio_min=None, pl_ratio_max=None, trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, refresh_cache=False)
        return data

    def getAccount(self):
        ret, data = self.ctx_.get_acc_list()
        if ret == RET_OK:
            print(data)
            print(data['acc_id'][0])  # 取第一个账号
            print(data['acc_id'].values.tolist())  # 转为 list
        else:
            print('get_acc_list error: ', data)
        ret, data = self.ctx_.accinfo_query(trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, refresh_cache=False, currency=Currency.HKD)
        print(data)
        pass

    def close(self):
        self.ctx_.close()
        return

    def unlock(self):
        ret, data = self.ctx_.unlock_trade('xxxxxxx')
        if ret == RET_OK:
            print('unlock success!')
        else:
            print('unlock_trade failed: ', data)
        pass

    pass

if __name__ == '__main__':
    t = Trade('US')
    t.showPositionsFee()
    t.close()
    t = Trade('HK')
    t.showPositionsFee()
    t.close()
    sys.exit(0)
    d1 = pd.read_json(j,orient="index")
    sys.exit(0)
    #d1 = pd.read_json(j,orient="index")
    sys.exit(0)
