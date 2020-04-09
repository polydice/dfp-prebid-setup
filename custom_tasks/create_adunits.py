#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sys import argv, exit
import settings
import settings_amp
from dfp.exceptions import (
    BadSettingException,
    MissingSettingException
)
from tasks import add_new_prebid_partner

from .parse_adunits_csv import *


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
    'OpenX': 'openx',
    'Teads': 'teads'
}


def get_order_name(ad_network, adunit_name, width, height):
    new_ad_network = ad_network

    try:
        new_ad_network = ORDER_DICT[ad_network]
    except KeyError:
        pass

    return f"Prebid {new_ad_network} {adunit_name} {width}x{height}"


def get_multisize_order_name(ad_network, adunit_name):
    new_ad_network = ad_network

    try:
        new_ad_network = ORDER_DICT[ad_network]
    except KeyError:
        pass

    return f"Prebid {new_ad_network} {adunit_name}"


def get_advertiser_name(ad_network):
    try:
        return ADVERTISER_DICT[ad_network]
    except:
        return ad_network


def create_new_settings(adunit_name, ad_network, size):
    result = settings_amp if 'AMP' in adunit_name else settings

    advertiser_name = get_advertiser_name(ad_network)
    bidder_code = BIDDER_CODES[ad_network]

    placement_sizes = None
    if "_" in size:
        def transform(sz):
            [w, h] = sz.split('x')
            return {'width': w, 'height': h}
        placement_sizes = list(map(transform, size.split('_')))
        order_name = get_multisize_order_name(ad_network, adunit_name)
    else:
        [w, h] = size.split('x')
        placement_sizes = [{'width': w, 'height': h}]
        order_name = get_order_name(ad_network, adunit_name, w, h)

    result.DFP_USER_EMAIL_ADDRESS = DFP_USER_EMAIL_ADDRESS
    result.DFP_ORDER_NAME = order_name
    result.DFP_ADVERTISER_NAME = advertiser_name
    result.DFP_TARGETED_AD_UNIT_NAMES = [adunit_name]
    result.DFP_PLACEMENT_SIZES = placement_sizes
    result.PREBID_BIDDER_CODE = bidder_code

    return result


def main():
    count = 0

    targeting_sheets = parse_adunits_csv()
    ad_units = targeting_sheets["ad_units"]
    sizes = targeting_sheets["sizes"]
    ad_networks = targeting_sheets["ad_networks"]

    for i, adunit_name in enumerate(ad_units):
        if i > 0:
            break
        try:
            new_settings = create_new_settings(
                adunit_name,
                ad_networks[i],
                sizes[i]
            )
            # new_settings.DFP_ORDER_NAME = '(TEST)' + \
            #     new_settings.DFP_ORDER_NAME
            add_new_prebid_partner.main(new_settings)
            count += 1
        except (BadSettingException, MissingSettingException) as error:
            exit(error)

    return count


if __name__ == "__main__":
    total_uploaded_adunits = main()
    print('{} ad units added.'.format(total_uploaded_adunits))
