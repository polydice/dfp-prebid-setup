#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
from googleads import ad_manager
from dfp.client import get_client

from custom_dfp.services import *
from custom_dfp.update_lica import add_size_to_lineitem
from .parse_adunits_csv import *


order_service = DfpServices.order_service()


def get_orders_by_advertiser(advertiserId):
    return (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
            .Where("advertiserId = :advertiserId \
                         AND status = 'APPROVED' \
                         AND isArchived = FALSE \
                         AND name LIKE 'Prebid %'")
            .WithBindVariable('advertiserId', advertiserId))


def rename_orders(advertiserId):
    def strip_size_in_name(name):
        return re.sub('\d+x\d+', '',  name).strip()

    statement = get_orders_by_advertiser(advertiserId)
    response = order_service.getOrdersByStatement(statement.ToStatement())
    orders = response['results']
    if 'results' in response and len(orders) > 0:
        for order in orders:
            print(order['name'])


def main(advertiserId):
    targeting_sheets = parse_adunits_csv()
    ad_units = targeting_sheets["ad_units"]

    sizes = targeting_sheets["sizes"]
    sizes = list(map(lambda size: [int(v) for v in size.split('x')], sizes))

    ad_networks = targeting_sheets["ad_networks"]

    statement = get_orders_by_advertiser(advertiserId)
    response = order_service.getOrdersByStatement(statement.ToStatement())

    found = []
    updated_orders = []
    orders = response['results']
    if 'results' in response and len(orders) > 0:
        for i, name in enumerate(ad_units):
            if i > 0:
                order_name = 'Prebid Appier {}'.format(name)
                add_size_to_lineitem(order_name, sizes[i])

        # for order in orders:
        #     if 'x' in order['name']:
        #         print(order['name'])
            # for i, name in enumerate(ad_units):
                # if name == order['name'].split(' ')[2]:


if __name__ == '__main__':
    main(4494037850)
