#!/usr/bin/env python3
# coding=utf-8
import re
from futu import *
from IPython.display import display, HTML
from pyhocon import ConfigFactory




'''
- https://openapi.futunn.com/futu-api-doc/quote/modify-user-security.html
'''

class UserSecurity:
    def __init__(self):
        self.confPath_ = 'conf/SMARTEST.conf'
        self.c_ = ConfigFactory.parse_file(self.confPath_)
        self.g_ = 'growth'
        self.ctx_ = OpenQuoteContext(host='127.0.0.1', port=11111)
        pass
    def update(self):
        #ret, data = self.ctx_.modify_user_security("A", ModifyUserSecurityOp.DEL, ['HK.00700'])
        #ret, data = self.ctx_.modify_user_security("A", ModifyUserSecurityOp.MOVE_OUT, ['HK.00700'])
        l = [f'US.{i}' for i in  self.c_.us.growth.keys() ]
        ret, data = self.ctx_.modify_user_security(self.g_, ModifyUserSecurityOp.ADD, l)
        if ret == RET_OK:
            print(data) # 返回 success
        else:
            print('error:', data)
        pass

    def show(self):
        pass

    def close(self):
        self.ctx_.close()
        pass

    pass

if __name__ == '__main__':
    u = UserSecurity()
    u.update()
    u.close()
    sys.exit(0)
