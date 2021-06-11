#!/usr/bin/env python3
# coding=utf-8
import re
from futu import *
from IPython.display import display, HTML


'''
-  加密 https://openapi.futunn.com/futu-api-doc/ftapi/init.html#2009
- https://openapi.futunn.com/futu-api-doc/trade/get-position-list.html
'''

class Trade:
    def __init__(self):
        self.ctx_ = OpenUSTradeContext(host='127.0.0.1', port=11111, is_encrypt=None, security_firm=SecurityFirm.FUTUSECURITIES)
        #self.ctx_ = OpenHKTradeContext(host='127.0.0.1', port=11111, security_firm=SecurityFirm.FUTUSECURITIES)

        #print(data)

        #print('--------Order List----------')
        #ret, data = self.ctx_.order_list_query(order_id="", status_filter_list=[], code='', start='', end='', trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, refresh_cache=False)
        #print(data)

        pass
    def getPositionList(self):
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
    t = Trade()
    d = t.getPositionList()
    display(d)
    t.close()
    sys.exit(0)
