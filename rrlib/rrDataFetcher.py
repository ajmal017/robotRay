# -*- coding: utf-8 -*-

"""
Created on 07 05 2019

@author: camilorojas

Data Fetcher proxy for market data
Currently Data Fetcher supports public datasources from Finviz and Yahoo.
v1 verson will support Interactive Brokers connectivity for data.

DataFetcher calls two different py files with the specific fetching logic
- rrDFPublic.py - will capture the public data sources
- rrDFIB.py - will connect and gather info from Interactive Brokers

"""

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
        self.source = config.get('datasource', 'source')
        self.timeout = int(config['urlfetcher']['Timeout'])

    def getData(self):
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        self.log.logger.debug("    About to retreive "+self.symbol)
        if (self.source == "public"):
            from rrlib.rrDFPublic import StockDFPublic as sdfp
            df = sdfp(self.symbol).getData()
        elif(self.source == "ib"):
            # implement class for ib retreival
            df = pd.DataFrame()
        else:
            self.log.logger.error("    DataFetcher source error:"+self.source)
        pd.set_option("display.max_rows", None, "display.max_columns", None)
        self.log.logger.debug("   Values loaded: \n"+str(df))
        self.log.logger.debug(
            "    DONE - Stock Data Fetcher "+str(self.symbol))
        return df

    def getIntradayData(self):
        self.log.logger.debug("    About to retreive "+self.symbol)
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        if(self.source == "public"):
            from rrlib.rrDFPublic import StockDFPublic as sdfp
            df = sdfp(self.symbol).getIntradayData()
            self.log.logger.debug("   Values loaded: \n"+str(df))
        elif(self.souce == "ib"):
            self.log.logger.debug("   Loading intraday from IB")
            # implement class for ib retreival
            df = pd.DataFrame()
        else:
            self.log.logger.error("   DataFetcher source error:"+self.source)
            df = pd.DataFrame()
        self.log.logger.debug(
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
        self.source = config.get('datasource', 'source')

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
                "    Option Data Fetcher Month outside or range, allowed 3-8 months")
            return df
