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
    def updateGroupList(self, group='Meta_semiCon_newEnergy', market='us'):
        s = self.c_[market][group]['list']
        #ret, data = self.ctx_.modify_user_security("A", ModifyUserSecurityOp.DEL, ['HK.00700'])
        #ret, data = self.ctx_.modify_user_security("A", ModifyUserSecurityOp.MOVE_OUT, ['HK.00700'])
        l = [f'US.{i}' for i in  s.split() ]
        print(l)
        ret, data = self.ctx_.modify_user_security(group, ModifyUserSecurityOp.ADD, l)
        if ret != RET_OK:
            self.log.critical(data); assert False, data
            return
        print(data)
        pass


    def getSecuritiesList(self, groupName = None):
        if groupName is None:
            groupName = self.g_
        ret, data = self.ctx_.get_user_security(groupName)
        if ret != RET_OK:
            self.log.critical(data); assert False, data
            return None
        return data
    def show(self, groupName = None):
        data  = self.getSecuritiesList(groupName)
        display(data[['code','name']])
        pass

    def close(self):
        if self.ctx_ is  None:
            return
        self.ctx_.close()
        self.ctx_ = None
        pass

    pass

if __name__ == '__main__':
    logInit()
    u = UserSecurity()
    g  = 'Meta_semiCon_newEnergy'
    g  = 'Real_Estate'
    g  = sys.argv[1]
    u.updateGroupList(g,'us')
    #u.update()
    u.show(g)
    #u.show()
    u.close()
    sys.exit(0)
