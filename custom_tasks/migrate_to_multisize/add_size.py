#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pprint
import argparse
from zeep.helpers import serialize_object
from googleads import ad_manager
from dfp.client import get_client

from custom_dfp.services import *
from custom_tasks.parse_adunits_csv import *
from custom_tasks.utils import log


order_service = DfpServices.order_service()
line_item_service = DfpServices.line_item_service()
lica_service = DfpServices.lica_service()

DRY_RUN = False


def get_orders(advertiserId):
    return (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
            .Where("advertiserId = :advertiserId \
                         AND status = 'APPROVED' \
                         AND isArchived = FALSE \
                         AND name LIKE 'Prebid %'")
            .WithBindVariable('advertiserId', advertiserId))


def get_line_items(order_id):
    return (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
            .Where("orderId = :order_id AND status != 'PAUSED'")
            .WithBindVariable('order_id', order_id)
            .Limit(500))


def get_new_size(order_name):
    if '320x100' in order_name:
        return (320, 50)
    elif '320x50' in order_name:
        return (320, 100)
    elif '300x250' in order_name:
        return (336, 280)
    else:
        return ()


def add_size_to_lica(line_item, sizes):
    statement = (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
                 .Where('lineItemId = :lineItemId')
                 .WithBindVariable('lineItemId', line_item['id']))
    while True:
        response = lica_service.getLineItemCreativeAssociationsByStatement(
            statement.ToStatement())
        licas = response['results']
        if 'results' in response and len(licas):
            updated_licas = []

            for lica in licas:
                new_creative_sizes = []
                creative_size = lica['sizes'][0]
                new_creative_sizes.append(creative_size)
                for size in sizes:
                    new_creative_sizes.append(
                        {
                            'width': size[0],
                            'height': size[1],
                            'isAspectRatio': False
                        },
                    )
                lica['sizes'] = new_creative_sizes
                updated_licas.append(lica)

            if not DRY_RUN:
                licas = lica_service.updateLineItemCreativeAssociations(
                    updated_licas)
                for lica in licas:
                    new_size = lica['sizes'][1]
                    log('LICA with item id {}, creative id {} was updated with new size {}x{}.'.format(
                        lica['lineItemId'], lica['creativeId'], new_size['width'], new_size['height']))
            # else:
            #     log('num licas: ', len(licas))
            #     pprint.pprint(lica['sizes'])

            statement.offset += statement.limit
        else:
            break


def add_size_to_line_items(response, sizes):
    line_items = response['results']
    num_line_items = len(line_items)

    if 'results' not in response or num_line_items <= 0:
        log('No line items found...', type='warn')
        return

    orderName = line_items[0]['orderName']
    for i, line_item in enumerate(line_items):
        updated_line_items = []
        new_creative_placeholders = []
        creative_placeholders = line_item['creativePlaceholders']

        if line_item['isArchived']:
            log('The line item was archived, skip it...', type='warn')
            continue

        if len(creative_placeholders) > 1:
            log('{} - this is an multi-size line item'.format(orderName), type='passed')
            continue

        placeholder = serialize_object(creative_placeholders[0])
        new_creative_placeholders.append(placeholder)

        for size in sizes:
            log('{} ({} line items) - try adding size {}x{}'
                .format(orderName,
                        num_line_items,
                        size[0], size[1]),
                type='progress')

            new_creative_placeholders.append(
                {
                    **placeholder,
                    'size': {
                        'width': size[0],
                        'height': size[1],
                        'isAspectRatio': False
                    }
                }
            )
        line_item['creativePlaceholders'] = new_creative_placeholders
        updated_line_items.append(line_item)

    if not DRY_RUN:
        line_items = line_item_service.updateLineItems(
            updated_line_items)

        if line_items:
            for line_item in line_items:
                log("order {} - Line item with id {}, named {}, size: {} was updated".format(
                    line_item['orderName'], line_item['id'], line_item['name'], line_item['creativePlaceholders'][0]['size']))
        else:
            log('No line items were updated.')

    for i, line_item in enumerate(updated_line_items):
        add_size_to_lica(line_item, sizes)


def main(advertiserId):
    # sheets = parse_adunits_csv()
    # ad_units = sheets["ad_units"]
    # sizes = sheets["sizes"]
    # sizes = list(map(lambda size: [int(v) for v in size.split('x')], sizes))
    # size_map = {name: sizes[i] for i, name in enumerate(ad_units)}

    # ad_networks = sheets["ad_networks"]
    statement = get_orders(advertiserId)
    response = order_service.getOrdersByStatement(statement.ToStatement())

    found = []
    updated_orders = []
    orders = response['results']

    # Migrate each order's line items and corresponding creatives
    if 'results' in response and len(orders) > 0:
        orders = list(filter(lambda order: 'x' in order['name'], orders))
        simple_order_names = list(
            map(lambda o: o['name'].split(' ')[2], orders))

        for i, order in enumerate(orders):
            order_name = order['name']
            # if simple_order_names[i] in size_map:
            #     size = size_map[simple_order_names[i]]
            # new_sizes = [(336, 280), (300, 250)]
            new_sizes = [get_new_size(order_name)]
            if 'AMP' in order_name or () in new_sizes:
                continue
            if () not in new_sizes:
                statement = get_line_items(order['id'])
                line_items_response = line_item_service.getLineItemsByStatement(
                    statement.ToStatement())
                add_size_to_line_items(line_items_response, new_sizes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Migrate single-size unit to multi-size')
    parser.add_argument('advertiserId')
    args = parser.parse_args()

    if args.advertiserId:
        main(args.advertiserId)
