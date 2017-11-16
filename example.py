#!/usr/bin/env python
# -*- coding: utf-8 -*-

import scraper


def run_scraper():
    data = []

    my_scraper = scraper.Scraper()

    kbz = my_scraper.scrap_kbz()._asdict()
    for index, item in enumerate(kbz.get('rates')):
        kbz['rates'][index] = item._asdict()

    data.append(kbz)

    cbb = my_scraper.scrap_cbb()._asdict()
    for index, item in enumerate(cbb.get('rates')):
        cbb['rates'][index] = item._asdict()

    data.append(cbb)

    aya = my_scraper.scrap_aya()._asdict()
    for index, item in enumerate(aya.get('rates')):
        aya['rates'][index] = item._asdict()

    data.append(aya)

    mab = my_scraper.scrap_mab()._asdict()
    for index, item in enumerate(mab.get('rates')):
        mab['rates'][index] = item._asdict()

    data.append(mab)

    uab = my_scraper.scrap_uab()._asdict()
    for index, item in enumerate(uab.get('rates')):
        uab['rates'][index] = item._asdict()

    data.append(uab)

    agd = my_scraper.scrap_agd()._asdict()
    for index, item in enumerate(agd.get('rates')):
        agd['rates'][index] = item._asdict()

    data.append(agd)

    central_bank = my_scraper.scrap_central_bank()._asdict()
    for index, item in enumerate(central_bank.get('rates')):
        central_bank['rates'][index] = item._asdict()

    data.append(central_bank)

    print(data)


if __name__ == "__main__":
    run_scraper()
