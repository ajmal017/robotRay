# -*- coding: utf-8 -*-

import sys
import os
from bs4 import BeautifulSoup as bs
import urllib
from urllib.error import URLError, HTTPError
import pandas as pd
from finvizfinance.quote import finvizfinance


class StockDataFetcher():
    # StockDataFetcher class

    def __init__(self, symbol):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrLogger import logger
        self.symbol = symbol
        self.log = logger()
        self.log.logger.debug("    Init Stock Data Fetcher "+str(symbol))
        # timeout import
        import configparser
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        self.timeout = int(config['urlfetcher']['Timeout'])

    def getData(self):
        self.log.logger.debug("    About to retreive "+self.symbol)
        stock = finvizfinance(self.symbol)
        self.log.logger.debug("      For: "+self.symbol+" data:"+str(stock.TickerFundament()))
        df = pd.DataFrame(stock.TickerFundament().items(), columns=['key', 'value'])
        pd.set_option("display.max_rows", None, "display.max_columns", None)
        self.log.logger.debug("   Values loaded: \n"+str(df))
        self.log.logger.info(
            "    DONE - Stock Data Fetcher "+str(self.symbol))
        return df

    def getIntradayData(self):
        self.log.logger.debug("    About to retreive "+self.symbol)
        stock = finvizfinance(self.symbol)
        self.log.logger.debug("      For: "+self.symbol+" data:"+str(stock.TickerFundament()))
        df = pd.DataFrame()
        # df = pd.DataFrame(columns=['stock', 'price', '%Change', '%Volume'])
        df = df.append({'stock': self.symbol, 'price': stock.TickerFundament().get('Price'),
                        '%Change': float(stock.TickerFundament().get('Change').strip('%'))/100,
                        '%Volume':
                        float(stock.TickerFundament().get('Rel Volume'))}, ignore_index=True)
        self.log.logger.debug("   Values loaded: \n"+str(df))
        self.log.logger.info(
            "    DONE - Stock Intraday Data Fetcher "+str(self.symbol))
        return df


class OptionDataFetcher():

    def __init__(self, symbol):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from rrlib.rrLogger import logger
        self.symbol = symbol
        self.log = logger()
        self.log.logger.debug("    Init Option Data Fetcher for "+symbol)
        # timeout import
        import configparser
        config = configparser.ConfigParser()
        config.read("rrlib/robotRay.ini")
        self.timeout = int(config['urlfetcher']['Timeout'])

    # Strike int, month is int and the number of months after today
    def getData(self, month, strike):
        # https://finance.yahoo.com/quote/WDAY200117P00160000
        # Get the put value for specified month 3-8
        from rrlib.rrOptions import OptionManager
        month = int(month)
        df = pd.DataFrame(columns=['key', 'value'])
        i = 0
        if (3 <= month <= 8):
            try:
                putURL = OptionManager.getPutFormater(
                    self.symbol, month, strike)
                # print(putURL)
                url = "https://finance.yahoo.com/quote/"+putURL
                self.log.logger.debug("    URL \n"+str(url))
                sauce = urllib.request.urlopen(
                    url, timeout=self.timeout).read()
            except HTTPError as e:
                self.log.logger.error(
                    "      HTTP Error= "+str(e.code)+" for stock "+self.symbol)
                return df
            except URLError as e:
                self.log.logger.error(
                    "      URL Error= "+str(e.code)+" for stock "+self.symbol)
                return df
            else:
                soup = bs(sauce, 'html.parser')
                data = soup.findAll(
                    "td", {"class": "Ta(end) Fw(600) Lh(14px)"})
                self.log.logger.debug(str(data))
                for tableData in soup.findAll("td", {"class": "C($primaryColor) W(51%)"}):
                    df = df.append(
                        {'key': tableData.span.text}, ignore_index=True)
                    try:
                        df.at[i, 'value'] = data[i].span.text
                    except Exception:
                        df.at[i, 'value'] = data[i].text
                    else:
                        df.at[i, 'value'] = data[i].text
                    i = i+1
                if len(df) > 0:
                    price = soup.find(
                        "span", {"class": "Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)"})
                    self.log.logger.debug(
                        "    Done pricing loaded: \n"+str(price.text))
                    df = df.append(
                        {'key': 'price', 'value': price.text}, ignore_index=True)
                self.log.logger.debug("    Done Option loaded: \n"+str(df))
                self.log.logger.debug(
                    "    Getting Option loaded: "+self.symbol+" for month "+str(month))
                return df
        else:
            self.log.logger.error(
                "    Month outside or range, allowed 3-8 months")
            return df
