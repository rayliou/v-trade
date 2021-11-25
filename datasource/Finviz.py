#!/usr/bin/env python3
# coding=utf-8


'''
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
            userDataDir='./userData',
            executablePath='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            args=['--disable-infobars',
                    f'--window-size={width},{height}',
                        '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    ])
        self.page_ = await self.browser_.newPage()
        return self.page_

    def getInsidersBuyLatest(self):
        return self.loop_.run_until_complete(self.getInsidersBuyLatest_())

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
    pass


if __name__ == '__main__':
    f = Finviz()
    df = f.getInsidersBuyLatest()
    display(df)

    sys.exit(0)

