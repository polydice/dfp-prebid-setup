#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
from enum import IntEnum
from itertools import count
from sys import argv, exit

import settings
from dfp.exceptions import (
    BadSettingException,
    MissingSettingException
)
from tasks import add_new_prebid_partner


DFP_USER_EMAIL_ADDRESS = "albert@thepolydice.com"

"""
    THESE arrays is the data copied from spreadsheet given from PM.
"""
ORDER_DICT = {
    'KEY': 'VALUE'
}
ADVERTISER_DICT = {
    'KEY': 'VALUE'
}
BIDDER_CODES = {
    'FAN': 'audienceNetwork',
    'AppNexus': 'appnexus',
    'Appier': 'appier',
    'Innity': 'innity',
    'OpenX': 'openx'
}


def get_order_name(ad_network, adunit_name, width, height):
    new_ad_network = ad_network

    try:
        new_ad_network = ORDER_DICT[ad_network]
    except KeyError:
        pass

    return f"Prebid {new_ad_network} {adunit_name} {width}x{height}"


def get_advertiser_name(ad_network):
    try:
        return ADVERTISER_DICT[ad_network]
    except:
        return ad_network


def parse_adunits_csv(target_advertiser):
    """
        Parse and refine raw adunits CSV file
        wrt. target_advertiser.
    """

    def parse_label_fields(row):
        row_without_empty = list(map(lambda e: e.strip() or "None", row))
        return IntEnum('Attr', zip(row_without_empty, count()))

    with open('adunits.csv', newline='') as csvfile:
        input_data = list(csv.reader(csvfile, delimiter=','))

        Label = parse_label_fields(input_data[0])
        input_data = input_data[1:]

        input_data = list(filter(
            lambda row: row[Label.adnetwork] == target_advertiser,
            input_data
        ))

        ad_networks = []
        ad_units = []
        sizes = []

        for row in input_data:
            # print("\t".join([
            #     row[Label.master_adunit],
            #     row[Label.size]])
            # )
            ad_units.append(row[Label.master_adunit])
            sizes.append(row[Label.size])
            ad_networks.append(row[Label.adnetwork])

        return {
            'ad_units': ad_units,
            'ad_networks': ad_networks,
            'sizes': sizes
        }


def create_new_settings(adunit_name, ad_network, size):
    result = settings

    advertiser_name = get_advertiser_name(ad_network)
    bidder_code = BIDDER_CODES[ad_network]
    [width, height] = size.split("x")

    order_name = get_order_name(ad_network, adunit_name, width, height)

    result.DFP_USER_EMAIL_ADDRESS = DFP_USER_EMAIL_ADDRESS
    result.DFP_ORDER_NAME = order_name
    result.DFP_ADVERTISER_NAME = advertiser_name
    result.DFP_TARGETED_AD_UNIT_NAMES = [adunit_name]
    result.DFP_PLACEMENT_SIZES = [{
        'width': width,
        'height': height
    }]
    result.PREBID_BIDDER_CODE = bidder_code

    return result


def main():
    count = 0

    targeting_sheets = parse_adunits_csv(argv[1])
    ad_units = targeting_sheets["ad_units"]
    sizes = targeting_sheets["sizes"]
    ad_networks = targeting_sheets["ad_networks"]

    for i, adunit_name in enumerate(ad_units):
        try:
            new_settings = create_new_settings(
                adunit_name,
                ad_networks[i],
                sizes[i]
            )
            add_new_prebid_partner.main(new_settings)
            count += 1
        except (BadSettingException, MissingSettingException) as error:
            exit(error)

    return count


if __name__ == "__main__":
    total_uploaded_adunits = main()
    print('{} ad units added.'.format(total_uploaded_adunits))
