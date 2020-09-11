# Ticket: https://polydice.slack.com/archives/CB0RD9RJS/p1591609045334600?thread_ts=1589179466.201100&cid=CB0RD9RJS

import time
import settings
from googleads import ad_manager
from custom_dfp.services import *
from dfp.exceptions import (
    BadSettingException,
    MissingSettingException
)
from .parse_sponsorship_items import *
from .parse_adunits_csv import *
import custom_tasks.add_new_prebid_partner


order_service = DfpServices.order_service()
line_item_service = DfpServices.line_item_service()

DFP_USER_EMAIL_ADDRESS = "albert@thepolydice.com"
ORDER_ID = '2695925690'
PLACEMENT_SIZES_DELIMITER = ';'
ADVERTISER_NAME = 'Criteo'
AD_NETWORK = 'criteo'


def get_order(orderName):
    statement = (DfpServices.statement()
                 .Where(f"name = :orderName")
                 .WithBindVariable('orderName', orderName))
    response = order_service.getOrdersByStatement(
        statement.ToStatement())

    if has_query_result(response):
        return response['results'][0]
    else:
        return None


def create_new_settings(adunit_name, size, price_min=0):
    result = settings
    if 'AMP' in adunit_name:
        result = settings_amp
    elif 'Android' in adunit_name or 'iPhone' in adunit_name or 'App' in adunit_name:
        result = settings_app

    placement_sizes = None
    if PLACEMENT_SIZES_DELIMITER in size:
        def transform(sz):
            [w, h] = sz.split('x')
            return {'width': w, 'height': h}
        placement_sizes = list(
            map(transform, size.split(PLACEMENT_SIZES_DELIMITER)))
    else:
        [w, h] = size.split('x')
        placement_sizes = [{'width': w, 'height': h}]

    result.DFP_USER_EMAIL_ADDRESS = DFP_USER_EMAIL_ADDRESS
    result.DFP_ADVERTISER_NAME = ADVERTISER_NAME
    result.DFP_TARGETED_AD_UNIT_NAMES = [adunit_name]
    result.DFP_PLACEMENT_SIZES = placement_sizes
    result.PREBID_BIDDER_CODE = AD_NETWORK
    result.PREBID_PRICE_BUCKETS = {
        **result.PREBID_PRICE_BUCKETS,
        # > price_min
        'min': price_min + result.PREBID_PRICE_BUCKETS['increment']
    }

    return result


def print_settings(settings):
    for name, value in settings.__dict__.items():
        if 'DFP' in name or 'PREBID' in name:
            print(f"{name}:   {value}")
    print("-------------------\n")


def main():
    count = 0

    sheets = parse_adunits_csv()
    unit_index_table = {v: i for i, v in enumerate(sheets["ad_units"])}
    sizes = sheets["sizes"]
    actual_sizes = sheets["actual_sizes"]
    ad_networks = sheets["ad_networks"]
    adnetwork_units = sheets["adnetwork_units"]

    targets = parse_sponsorship_items()

    for i, target in enumerate(targets):
        try:
            unit = target['unit']
            config_index = unit_index_table[unit]
            new_settings = create_new_settings(
                unit,
                actual_sizes[config_index],
                target['rate_start_from']
            )

            order = get_order(target['orderName'])
            if order:
                new_settings.DFP_ORDER_ID = order['id']
                new_settings.DFP_ORDER_NAME = order['name']
                custom_tasks.add_new_prebid_partner.main(
                    new_settings, dry_run=False)
            else:
                print('Order not found, exit...')
                exit(1)
        except (BadSettingException, MissingSettingException) as error:
            exit(error)

    return count


if __name__ == "__main__":
    num_updated = main()
    if num_updated:
        print(f"{num_updated} orders was successfully updated")
