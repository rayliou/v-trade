#!/usr/bin/env python3
# coding=utf-8
import re,sys
from futu import *
from IPython.display import display, HTML
import numpy as np
import matplotlib.pyplot as plt


'''
- American Option Pricing with QuantLib and Python: http://gouthamanbalaraman.com/blog/american-option-pricing-quantlib-python.html

https://qsctech-sange.github.io/option-price
https://github.com/QSCTech-Sange/Options-Calculator/blob/master/Backend/Option.py
pip install option-price

- https://numpy.org/doc/stable/user/index.html
- https://numpy.org/doc/stable/reference/generated/numpy.linspace.html
- https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.plot.html#matplotlib.pyplot.plot
- https://openapi.futunn.com/futu-api-doc/trade/get-position-list.html
- Breakeven Point 盈亏平衡点

蒙特卡洛 American Option Price Boyle, Broadie Glasserman[1997] by Meier(2000)
'''

def BG(CallPutFlag, S,X,T,r,b, Sig,m, Branches, nSimulations):
    z  = 1 if CallPutFlag == 'CALL' else -1
    Drift  = (b-Sig ** 2/2 )* T /(m-1)
    SigSqrdt = Sig * sqrt(T/(m-1))
    Discdt = exp(-r*T/(m-1))
    for Estimator in range(1,2):
        EstimatorSum = 0
        for simulation in range(1,nSimulations):
            pass
    pass

class OptionBroadieGlasserman:
    CALL = 0
    PUT  = 1
    def __init__(self, k, premium,delta = 0.5, t=1, opType=CALL):
        pass
    pass
def QuantLibOptionPrice():
    '''
    - https://quantlib-python-docs.readthedocs.io/en/latest/pricing_engines.html#vanilla-options
    '''
    import QuantLib as ql
    import matplotlib.pyplot as plt
    #%matplotlib inline
    ql.__version__

    maturity_date = ql.Date(15, 1, 2016)
    spot_price = 127.62
    strike_price = 130
    volatility = 0.20 # the historical vols or implied vols
    dividend_rate =  0.0163
    option_type = ql.Option.Call

    risk_free_rate = 0.001
    day_count = ql.Actual365Fixed()
    calendar = ql.UnitedStates()

    calculation_date = ql.Date(8, 5, 2015)
    ql.Settings.instance().evaluationDate = calculation_date

    payoff = ql.PlainVanillaPayoff(option_type, strike_price)
    settlement = calculation_date
    am_exercise = ql.AmericanExercise(settlement, maturity_date)
    american_option = ql.VanillaOption(payoff, am_exercise)
    eu_exercise = ql.EuropeanExercise(maturity_date)
    european_option = ql.VanillaOption(payoff, eu_exercise)


    spot_handle = ql.QuoteHandle(
        ql.SimpleQuote(spot_price)
    )
    flat_ts = ql.YieldTermStructureHandle(
        ql.FlatForward(calculation_date, risk_free_rate, day_count)
    )
    dividend_yield = ql.YieldTermStructureHandle(
        ql.FlatForward(calculation_date, dividend_rate, day_count)
    )
    flat_vol_ts = ql.BlackVolTermStructureHandle(
        ql.BlackConstantVol(calculation_date, calendar, volatility, day_count)
    )
    bsm_process = ql.BlackScholesMertonProcess(spot_handle,
                                            dividend_yield,
                                            flat_ts,
                                            flat_vol_ts)


    steps = 200
    binomial_engine = ql.BinomialVanillaEngine(bsm_process, "crr", steps)
    american_option.setPricingEngine(binomial_engine)
    print (american_option.NPV())


    def binomial_price(option, bsm_process, steps):
        binomial_engine = ql.BinomialVanillaEngine(bsm_process, "crr", steps)
        option.setPricingEngine(binomial_engine)
        return option.NPV()

    steps = range(5, 200, 1)
    eu_prices = [binomial_price(european_option, bsm_process, step) for step in steps]
    am_prices = [binomial_price(american_option, bsm_process, step) for step in steps]
    # theoretican European option price
    european_option.setPricingEngine(ql.AnalyticEuropeanEngine(bsm_process))
    bs_price = european_option.NPV()


    plt.plot(steps, eu_prices, label="European Option", lw=2, alpha=0.6)
    plt.plot(steps, am_prices, label="American Option", lw=2, alpha=0.6)
    plt.plot([5,200],[bs_price, bs_price], "r--", label="BSM Price", lw=2, alpha=0.6)
    plt.xlabel("Steps")
    plt.ylabel("Price")
    plt.ylim(6.7,7)
    plt.title("Binomial Tree Price For Varying Steps")
    plt.legend()
    plt.show()





    pass



if __name__ == '__main__':
    QuantLibOptionPrice()
    sys.exit(0)
    #ironCondor()

'''

some_option = Option(european=False,
                    kind='put',
                    s0=27.8,
                    k=33,
                    sigma=0.428,
                    r=0.01, start='2021-06-26', end='2021-07-29', dv=0)

x = some_option.getPrice()
y = some_option.getPrice(method='MC',iteration = 500000)
z = some_option.getPrice(method='BT',iteration = 10000)
x,y,z
'''
