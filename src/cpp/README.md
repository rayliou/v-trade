## flow
1. Get Daily data of SPY. 
1. Generate yyyymmDD.csv dependences. first later, last earlier
1. Get data day by day. (5 seconds)
1. Backtest.


## IBKR API compile

https://groups.io/g/twsapi/topic/c_upgrade_api_to_10_11/87904832?p=,,,20,0,0,0::recentpostdate/sticky,,,20,2,20,87904832,previd=1640328166371234878,nextid=1639126360059394114&previd=1640328166371234878&nextid=1639126360059394114

Intel did publish the source code for the library and there are several GitHub repositories. You can also grab a copy of the source from Intel directly by following the links in my post:

From https://www.intel.com/content/www/us/en/developer/articles/tool/intel-decimal-floating-point-math-library.html
Go to http://www.netlib.org/misc/intel/
Go to http://www.netlib.org/misc/intel/IntelRDFPMathLib20U2.tar.gz

make CALL_BY_REF=0 GLOBAL_RND=0 GLOBAL_FLAGS=0 UNCHANGED_BINARY_FLAGS=0 CC=/usr/local/Cellar/gcc/11.2.0_3/bin/gcc

# Redis

- https://github.com/sewenew/redis-plus-plus#redis-stream

