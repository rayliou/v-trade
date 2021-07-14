#!/usr/bin/env python3
# coding=utf-8
import re
from futu import *
from IPython.display import display, HTML
from pyhocon import ConfigFactory
from Log import logInit




'''
- https://openapi.futunn.com/futu-api-doc/quote/modify-user-security.html
'''

class UserSecurity:
    log = logging.getLogger("main.UserSecurity")
    def __init__(self):
        self.confPath_ = 'conf/SMARTEST.conf'
        self.confPath_ = 'conf/TIPS.conf'
        self.confPath_ = 'conf/tmp.conf'
        self.c_ = ConfigFactory.parse_file(self.confPath_)
        self.g_ = 'tmp'
        self.ctx_ = OpenQuoteContext(host='127.0.0.1', port=11111)
        pass
    def update(self):
        #ret, data = self.ctx_.modify_user_security("A", ModifyUserSecurityOp.DEL, ['HK.00700'])
        #ret, data = self.ctx_.modify_user_security("A", ModifyUserSecurityOp.MOVE_OUT, ['HK.00700'])
        l = [f'US.{i}' for i in  self.c_.us.growth.keys() ]
        ret, data = self.ctx_.modify_user_security(self.g_, ModifyUserSecurityOp.ADD, l)
        if ret != RET_OK:
            self.log.critical(data); assert False, data
            return
        print(data)
        pass

    def show(self):
        ret, data = self.ctx_.get_user_security(self.g_)
        if ret != RET_OK:
            self.log.critical(data); assert False, data
            return
        display(data)
        pass

    def close(self):
        self.ctx_.close()
        pass

    pass

if __name__ == '__main__':
    logInit()
    u = UserSecurity()
    u.update()
    u.show()
    #u.show()
    u.close()
    sys.exit(0)
