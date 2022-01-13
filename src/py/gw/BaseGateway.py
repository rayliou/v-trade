#!/usr/bin/env python3
# coding=utf-8
#from ib_insync import *
import sys,time
from datetime import datetime,timedelta,date
import logging

class BaseGateway:
    log = logging.getLogger("main.BaseGateway")
    def __init__(self,config):
        self.c_ = config
        self.dataRootDir_ = self.c_.data.rootDir
        self.dataRootDir_ = '../data_test'
        self.dfBigTableHist_ = None
        self.source_ = 'unknown'
        pass

    def writeHistoricalBigTableToFile(self, withObj = None):
        tm = datetime.now().strftime('%Y%m%d-%H%M')
        filePath = f'{self.dataRootDir_}/bigtable-{self.source_}-{tm}.csv'
        if withObj is not None:
            with withObj:
                self.dfBigTableHist_.to_csv(filePath)
        else:
            self.dfBigTableHist_.to_csv(filePath)
        self.log.debug(f'Wrote file {filePath}')
        #self.conditionVar_.notify()
        pass
    def disconnect(self):
        pass
    pass


if __name__ == '__main__':
    sys.exit(0)
