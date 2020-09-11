#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import re
from sys import argv, exit
import settings
import settings_amp
import settings_app
from dfp.exceptions import (
    BadSettingException,
    MissingSettingException
)
from tasks import add_new_prebid_partner
from .parse_adunits_csv import *

from custom_dfp.services import *
order_service = DfpServices.order_service()

DFP_USER_EMAIL_ADDRESS = "albert@thepolydice.com"

"""
    THESE arrays is the data copied from spreadsheet given from PM.
"""
ORDER_DICT = {
    'FAN': 'Audience Network'
}

ADVERTISER_DICT = {
    'FAN': 'Facebook'
}

BIDDER_CODES = {
    'FAN': 'audienceNetwork',
    'AppNexus': 'appnexus',
    'Appier': 'appier',
    'Innity': 'innity',
    'OpenX': 'openx',
    'Teads': 'teads',
    'ucfunnel': 'ucfunnel',
    'Criteo': 'criteo',
    'IndexExchange': 'ix',
    'VerizonMedia': 'onemobile'
}

PLACEMENT_SIZES_DELIMITER = ','


def get_order(name):
    statement = (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
                 .Where("status = 'DRAFT' \
                         AND isArchived = FALSE \
                         AND name LIKE '{}'".format(name)))

    response = order_service.getOrdersByStatement(
        statement.ToStatement())

    results = response['results'] \
        if has_query_result(response) \
        else None

    if results:
        return results[0]


def replace_app_adunit_name(adunit_name):
    return re.sub(r"iPhone|Android", "App", adunit_name, flags=re.IGNORECASE)


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
    result = settings
    if 'AMP' in adunit_name:
        result = settings_amp
    elif 'Android' in adunit_name or 'iPhone' in adunit_name or 'App' in adunit_name:
        result = settings_app

    advertiser_name = get_advertiser_name(ad_network)
    bidder_code = BIDDER_CODES[ad_network]

    placement_sizes = None
    if PLACEMENT_SIZES_DELIMITER in size:
        def transform(sz):
            [w, h] = sz.split('x')
            return {'width': w, 'height': h}
        placement_sizes = list(
            map(transform, size.split(PLACEMENT_SIZES_DELIMITER)))
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


def debug_log(new_settings):
    log_string = ',  '.join((new_settings.DFP_ORDER_NAME,
                             str(new_settings.DFP_PLACEMENT_SIZES),
                             new_settings.DFP_CURRENCY_CODE,
                             str(new_settings.PREBID_PRICE_BUCKETS)
                             ))
    print(log_string)


def is_order_uploaded(ordername):
    statement = (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
                 .Where("status = 'DRAFT' \
                         AND isArchived = FALSE \
                         AND name LIKE '{}'".format(ordername)))

    response = order_service.getOrdersByStatement(
        statement.ToStatement())

    # orders = response['results']
    return has_query_result(response)


def main():
    count = 0

    targeting_sheets = parse_adunits_csv()
    ad_units = list(map(replace_app_adunit_name, targeting_sheets["ad_units"]))
    sizes = targeting_sheets["sizes"]
    actual_sizes = targeting_sheets["actual_sizes"]
    ad_networks = targeting_sheets["ad_networks"]
    adnetwork_units = targeting_sheets["adnetwork_units"]

    for i, adunit_name in enumerate(ad_units):
        try:
            new_settings = create_new_settings(
                adunit_name,
                ad_networks[i],
                actual_sizes[i]
            )
            print(f"Sizes: {new_settings.DFP_PLACEMENT_SIZES}")

            # debug_log(new_settings)

            if not is_order_uploaded(new_settings.DFP_ORDER_NAME):
                add_new_prebid_partner.main(new_settings)
                count += 1
            else:
                print(f"The order {new_settings.DFP_ORDER_NAME} is uploaded.")

            # Prevent QuotaError
            # https://developers.google.com/ad-manager/api/troubleshooting#QuotaError.EXCEEDED_QUOTA
            time.sleep(2)
        except (BadSettingException, MissingSettingException) as error:
            exit(error)

    return count


if __name__ == "__main__":
    total_uploaded_adunits = main()
    print(f'{total_uploaded_adunits} ad units was created.')
