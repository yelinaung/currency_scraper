# -*- coding: utf-8 -*-
"""Scraper module"""

import json
import re
from collections import namedtuple
from datetime import datetime
from itertools import zip_longest

import cfscrape
import requests
import shortuuid
from bs4 import BeautifulSoup
from pytz import timezone


class Scraper(object):
    """Main Scraper"""

    @classmethod
    def instance(cls):
        """ new instance of Scraper """
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.kbz_url = "https://www.kbzbank.com/en"
        self.cbb_url = "http://www.cbbank.com.mm/exchange_rate.aspx"
        self.aya_url = "http://www.ayabank.com/en_US/"
        self.mab_url = "https://www.mabbank.com/"
        self.uab_url = "http://www.unitedamarabank.com"
        self.agd_url = "http://otcservice.agdbank.com.mm/utility/rateinfo?callback=?"
        self.BuySell = namedtuple('BuySell', 'currency_code buy sell')
        self.Currency = namedtuple('Currency',
                                   'id bank_code scrap_time source_time rates')
        self.MM_TZ = "+0630"
        self.ordn = re.compile(r'(?<=\d)(st|nd|rd|th)\b')

    def scrap_kbz(self):
        """ KBZ Bank Scraper """

        scrap_time = self._get_scrap_time()

        result = requests.get(self.kbz_url, stream=True)
        # kbz_temp_file = 'temp/kbz.html'

        # if not os.path.isfile(kbz_temp_file):
        # urllib.request.urlretrieve(self.kbz_url, kbz_temp_file)

        # soup = BeautifulSoup(open(kbz_temp_file).read(), "lxml")
        soup = BeautifulSoup(result.content, "lxml")
        raw_data = soup.find('div', {'class': 'exchange-rate'}).find_all(
            'div', {'class': 'col-lg-2'})
        date_row = raw_data[0]
        source_time_str = date_row.text.replace("EXCHANGE RATES", "").strip()

        # e.g 07/25/2017 +0630
        source_time_str = "{0} {1}".format(source_time_str, self.MM_TZ)

        # parse the original string
        source_time = datetime.strptime(source_time_str, '%m/%d/%Y %z')

        # reformat to epoch time
        source_time = int(datetime.strftime(source_time, "%s"))

        currencies_row = raw_data[1:]
        tmp = []
        for currency in currencies_row:
            # the parent tag "div" with
            # class attribute cannot do extract()
            del currency['class']
            for idx, value in enumerate(currency):
                extracted_value = value.extract().strip()
                if len(extracted_value) > 0:
                    # this is so hackish
                    if idx % 2 == 0:
                        tmp.append(currency.span.string.strip())
                    tmp.append(extracted_value)

        buy_sell = self._group_buy_sell(tmp=tmp)

        return self.Currency(
            id=shortuuid.uuid(),
            bank_code='kbz',
            source_time=source_time,
            scrap_time=scrap_time,
            rates=buy_sell)

    def scrap_cbb(self):
        """CB Bank scraper"""
        scrap_time = self._get_scrap_time()

        result = requests.get(self.cbb_url)
        tmp = []
        soup = BeautifulSoup(result.content, "lxml")
        raw_data = soup.find("table").find_all("tr")
        # slice the last item for the date
        source_time_str = raw_data[-1].find("td").string
        source_time_str = "{0} {1}".format(source_time_str, self.MM_TZ)

        # sample - 28/07/2017 - 10:05 AM +0630
        # parse the original string
        source_time = datetime.strptime(source_time_str,
                                        '%d/%m/%Y - %I:%M %p %z')

        # reformat to epoch time
        source_time = int(datetime.strftime(source_time, "%s"))

        # omit the first item and slice until the last time
        currencies_row = raw_data[1:-1]
        for currency in currencies_row:
            for value in currency.find_all("td"):
                tmp.append(value.string)

        buy_sell = self._group_buy_sell(tmp)

        return self.Currency(
            id=shortuuid.uuid(),
            bank_code='cbb',
            source_time=source_time,
            scrap_time=scrap_time,
            rates=buy_sell)

    def scrap_aya(self):
        """ scrapper for AYA bank"""
        scrap_time = self._get_scrap_time()
        result = requests.get(self.aya_url)
        soup = BeautifulSoup(result.content, "lxml")
        # soup = BeautifulSoup(open("temp/aya.html").read(), "lxml")

        raw_data = soup.find("table", {"class",
                                       "tablepress-id-1"}).find_all("tr")
        date_row = raw_data[0].find("td")
        tmp_date = []
        for date_content in date_row.contents:
            if date_content.string is not None:
                tmp_date.append(date_content.string.replace("\n", ""))
                source_time_str = str(' '.join(tmp_date))

        # remove ordinal str from the date
        source_time_str = self.ordn.sub('', source_time_str)
        source_time_str = "{0} {1}".format(source_time_str, self.MM_TZ)

        # sample - 31st July 2017 ( 10:50AM  ) +0630
        # parse the original string
        source_time = datetime.strptime(source_time_str,
                                        '%d %B %Y ( %I:%M %p  ) %z')
        # reformat it
        source_time = int(datetime.strftime(source_time, '%s'))
        tmp = []
        currencies_row = raw_data[1:-1]
        for currency in currencies_row:
            for value in currency.find_all("td"):
                tmp.append(value.string)

        buy_sell = self._group_buy_sell(tmp)

        return self.Currency(
            id=shortuuid.uuid(),
            bank_code='aya',
            source_time=source_time,
            scrap_time=scrap_time,
            rates=buy_sell)

    def scrap_mab(self):
        """ scrapper for MAB bank"""
        scrap_time = self._get_scrap_time()

        result = None

        scraper = cfscrape.create_scraper()
        result = scraper.get(self.mab_url)

        soup = BeautifulSoup(result.content, "lxml")
        raw_data = soup.find('div', {'class', 'exchange-box'})

        # date
        source_time_str = raw_data.find(
            'div', {'class': 'effected'}).find('span').text.strip()

        # e.g 28th July 2017 ( 10:40AM  )
        source_time_str = "{0} {1}".format(source_time_str, self.MM_TZ)

        # sample - 31/7/2017 +0630
        # parse the original string
        source_time = datetime.strptime(source_time_str, '%d/%m/%Y %z')
        # reformat it
        source_time = int(datetime.strftime(source_time, '%s'))

        # data
        tmp = []
        currencies = raw_data.find_all('p')
        currencies = list(self.grouper(currencies, 3))

        # remove the first row since it's a title
        del currencies[0]

        for currency in currencies:
            rates = list(currency)
            for rate in rates:
                tmp.append(rate.text)

        buy_sell = self._group_buy_sell(tmp)

        return self.Currency(
            id=shortuuid.uuid(),
            bank_code='mab',
            source_time=source_time,
            scrap_time=scrap_time,
            rates=buy_sell)

    def scrap_uab(self):
        """ scrapper for UAB bank """
        scrap_time = self._get_scrap_time()

        result = requests.get(self.uab_url)
        tmp = []
        soup = BeautifulSoup(result.content, "lxml")
        raw_data = soup.find('div', {'class': 'ex_rate'}).find_all(
            'div', {'class': 'ex_body'})

        # source time is not available for UAB
        # reusing scrap_time
        source_time = scrap_time

        # data
        currencies_row = raw_data[1:]
        for currency in currencies_row:
            for value in currency.select("ul li"):
                # .stripped_strings yields Python strings
                # that have had whitespace stripped
                for stripped_string in value.stripped_strings:
                    tmp.append(stripped_string)

        buy_sell = self._group_buy_sell(tmp)

        return self.Currency(
            id=shortuuid.uuid(),
            bank_code='uab',
            source_time=source_time,
            scrap_time=scrap_time,
            rates=buy_sell)

    def scrap_agd(self):
        """ scrapper for AGD bank """
        scrap_time = self._get_scrap_time()

        # source time is not available for AGD
        # reusing scrap_time
        source_time = scrap_time

        result = requests.get(self.agd_url)
        tmp = []
        raw_data = result.content.decode("utf-8")
        raw_data = raw_data.replace('?', '')
        raw_data = raw_data.replace('(', '')
        raw_data = raw_data.replace(')', '')
        raw_data = raw_data.replace(';', '')

        raw_json_string = json.loads(raw_data)

        tmp.append("USD")
        tmp.append(self._extract_with_index(raw_json_string, 7))
        tmp.append(self._extract_with_index(raw_json_string, 6))
        tmp.append("EUR")
        tmp.append(self._extract_with_index(raw_json_string, 1))
        tmp.append(self._extract_with_index(raw_json_string, 0))
        tmp.append("SGD")
        tmp.append(self._extract_with_index(raw_json_string, 3))
        tmp.append(self._extract_with_index(raw_json_string, 2))
        tmp.append("THB")
        tmp.append(self._extract_with_index(raw_json_string, 5))
        tmp.append(self._extract_with_index(raw_json_string, 4))

        buy_sell = self._group_buy_sell(tmp)

        return self.Currency(
            id=shortuuid.uuid(),
            bank_code='agd',
            source_time=source_time,
            scrap_time=scrap_time,
            rates=buy_sell)

    def _group_buy_sell(self, tmp):
        groups = list(self.grouper(tmp, 3))
        buy_sell = []
        for g in groups:
            buy_sell.append(
                self.BuySell(currency_code=g[0], buy=g[1], sell=g[2]))
        return buy_sell

    def _extract_with_index(self, data, index):
        return str(data['ExchangeRates'][index]['Rate'])

    # From itertools receipes
    # https://docs.python.org/3/library/itertools.html#itertools-recipes
    def grouper(self, iterable, n, fillvalue=None):
        "Collect data into fixed-length chunks or blocks"
        # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
        args = [iter(iterable)] * n
        return zip_longest(*args, fillvalue=fillvalue)

    def _get_scrap_time(self):
        scrap_time = datetime.now(timezone('Asia/Yangon'))
        return int(scrap_time.strftime("%s"))
