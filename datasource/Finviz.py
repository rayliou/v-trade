#!/usr/bin/env python3
# coding=utf-8


'''
- https://pandas.pydata.org/docs/getting_started/intro_tutorials/03_subset_data.html
- https://pypi.org/project/pyppeteer/
- https://pyppeteer.github.io/pyppeteer/reference.html#environment-variables
- https://pyppeteer.github.io/pyppeteer/reference.html#elementhandle-class
'''
import asyncio,sys
from getpass import getpass
from pyppeteer import launch
from pyquery import PyQuery as pq
from bs4 import BeautifulSoup
import pandas as pd
from IPython.display import display, HTML
from datetime import datetime
from datetime import timedelta
import yfinance as yf
from ib import IBKR


'''

- Detail            : https://finviz.com/quote.ashx?t=DNUT&b=2
- InsidersBuyLatest : https://finviz.com/insidertrading.ashx?tc=1
'''

class Finviz:
    def __init__(self) -> None:
        self.loop_ = asyncio.get_event_loop()
        self.loop_.run_until_complete(self.setup())
        pass
    async def setup(self):
        width, height = 2800, 1700
        headless = True
        devtools=False
        headless = False
        self.browser_ = await launch(devtools=devtools, headless=headless,
            #userDataDir='./userData',
            executablePath='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            args=['--disable-infobars',
                    f'--window-size={width},{height}',
                        '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    ])
        self.page_ = await self.browser_.newPage()
        await self.page_.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36')
        return await self.page_.setViewport( {'width':width, 'height':height})

    async def scrollPage(self):
        js = '''
            () => new Promise((resolve) => {
            var scrollTop = -1;
            const interval = setInterval(() => {
                window.scrollBy(0, 100);
                if(document.documentElement.scrollTop !== scrollTop) {
                scrollTop = document.documentElement.scrollTop;
                return;
                }
                clearInterval(interval);
                resolve();
            }, 10);
            })
        '''
        return await self.page_.evaluate(js)

    def getInsidersBuyLatest(self, days=3, minValue=150000, minCost=10):
        df =  self.loop_.run_until_complete(self.getInsidersBuyLatest_())
        now = datetime.now()
        start = now - timedelta(days=days)
        start = start.strftime('%Y-%m-%d')

        ticker  = df['Ticker']
        owner   = df['Owner']
        dt      = df['Date']
        dt      = pd.to_datetime(
                    df['Date'] +' 2021', format='%b %d %Y')
        cost   = df['Cost '].apply(lambda x: float(x.replace(',',''))  )
        value   = df['Value ($)'].apply(lambda x: int(x.replace(',',''))  )
        share_total  = df['#Shares Total']
        dt_sec  = pd.to_datetime(
            df['SEC Form 4'] +' 2021', format='%b %d %I:%M %p %Y')
        df  = pd.DataFrame( {
            'ticker' : ticker,
            'owner' : owner,
            'Relationship' : df['Relationship'],
            'cost' : cost,
            'value' : value,

            'dt' : dt,
            'dt_sec' : dt_sec,
            }
            )
        filter = ((dt >= start) & (value >= minValue) & (cost > minCost) )
        df = df[filter].sort_values(by=['dt','value'], ascending=False)
        #df = df.sort_values(by=['dt_sec','value'], ascending=False)
        return df

    def getQuotations(self, symbolsList):
        sList  = ' '.join(set(symbolsList))
        q  = yf.download(sList,period='1d', interval='1d').iloc[-1]
        assert isinstance(q, (pd.Series, pd.DataFrame))
        r  = dict()
        if isinstance(q, pd.Series):
            r[sList] = dict(q)
            return r
        else:
            pass

        pass


    async def getInsidersBuyLatest_(self):
        #await page.goto('https://www.fido.ca/self-serve/signin')
        url ='https://finviz.com/insidertrading.ashx?tc=1'
        await self.page_.goto(url)
        await self.page_.evaluate(
            '''() =>{ Object.defineProperties(navigator,{ webdriver:{ get: () => false } }) }''')
        #doc = pq(await page.content())
        #print('1111111111111111')
        cnt = 0
        while cnt < 50:
            await asyncio.sleep(0.5); cnt += 1
            tblPath = "body > table:nth-child(5) > tbody > tr:nth-child(1) > td > table > tbody > tr:nth-child(3) > td > table.body-table > tbody"
            tboday = await self.page_.J(tblPath)
            if tboday is None:
                continue
            trs = await tboday.JJ('tr')
            innerHtml = 'n.innerHTML'
            innerText = '(n.textContent===undefined) ? n.innerText : n.textContent'
            text      = innerText
            keys = await trs[0].JJeval('td', f'nodes => nodes.map(n => {text} ) ')
            vals = [ await tr.JJeval('td', f'nodes => nodes.map(n => {text} ) ')  for tr in trs if tr != trs[0] ]
            df = pd.DataFrame(vals, columns=keys)
            return df
            #src  = await  f.getProperty('src')
            # src  = await  src.jsonValue()
        return None

    def getDetail(self):
        return self.loop_.run_until_complete(self.getDetail_())

    async def getDetail_(self):
        #await page.goto('https://www.fido.ca/self-serve/signin')
        url ='https://finviz.com/quote.ashx?t=DNUT&b=2'
        await self.page_.goto(url)
        await self.page_.evaluate(
            '''() =>{ Object.defineProperties(navigator,{ webdriver:{ get: () => false } }) }''')
        #doc = pq(await page.content())
        #print('1111111111111111')
        cnt = 0
        while cnt < 50:
            await asyncio.sleep(0.5); cnt += 1
            await self.scrollPage()
            tblPath = 'body > div:nth-child(7) > div > table:nth-child(3) > tbody'
            tboday = await self.page_.J(tblPath)
            if tboday is None:
                continue
            trs = await tboday.JJ('tr')
            innerHtml = 'n.innerHTML'
            innerText = '(n.textContent===undefined) ? n.innerText : n.textContent'
            text      = innerText
            keys = await trs[0].JJeval('td', f'nodes => nodes.map(n => {text} ) ')
            vals = [ await tr.JJeval('td', f'nodes => nodes.map(n => {text} ) ')  for tr in trs if tr != trs[0] ]
            df = pd.DataFrame(vals, columns=keys)
            return df
            #src  = await  f.getProperty('src')
            # src  = await  src.jsonValue()
        return None
    pass


if __name__ == '__main__':
    f = Finviz()
    df = f.getInsidersBuyLatest()
    #display(df); sys.exit(0)
    symList = ' '.join( df.ticker)
    ibkr = IBKR()
    dfR  = ibkr.reqMktData(symList)[['markPrice','close']]
    df  = df.join(dfR, on='ticker')
    df['T']  = df.ticker
    df['% markPrice_cost']  = (df.markPrice - df.cost)/df.cost * 100
    df['% close_cost']  = (df.close - df.cost)/df.cost * 100
    display(df)
    print( symList)
    sys.exit(0)
'''
 Ticker                 Owner                   Relationship    Date Transaction  Cost  #Shares Value ($) #Shares Total       SEC Form 4
0     VCTR   DEMARTINI RICHARD M                       Director  Nov 24         Buy  35.30  13,500   476,550        27,841  Nov 29 09:57 PM
1     MIRM          Clements Ian        Chief Financial Officer  Nov 26         Buy  13.90     750    10,425        18,561  Nov 29 09:49 PM
2     MIRM          Clements Ian        Chief Financial Officer  Nov 24         Buy  14.40     700    10,080        17,811  Nov 29 09:49 PM
'''

