#!/usr/bin/env python
#
# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
from googleads import ad_manager
from dfp.client import get_client
from .dfp_settings import *


def get_order_service():
    dfp_client = get_client()
    return dfp_client.GetService('OrderService', version=DFP_SERVICE_VERSION)


def get_orders_by_advertiser(advertiserId):
    statement = (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
                 .Where("advertiserId = :advertiserId \
                         AND isArchived = FALSE \
                         AND name LIKE 'Prebid %'")
                 .WithBindVariable('advertiserId', advertiserId))

    return statement


def get_archived_target_orders(advertiserId, mark):
    statement = (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
                 .Where("advertiserId = :advertiserId \
                         AND isArchived = FALSE \
                         AND name LIKE '{}Prebid %'".format(mark))
                 .WithBindVariable('advertiserId', advertiserId))
    return statement


def mark_orders(order_service, advertiserId, mark):
    # Get orders by statement.
    orders_statement = get_orders_by_advertiser(advertiserId)
    response = order_service.getOrdersByStatement(
        orders_statement.ToStatement())

    if 'results' in response and len(response['results']):
        # Update each local order object by changing its property.
        updated_orders = []
        for order in response['results']:
            # Archived orders cannot be updated.
            if not order['isArchived'] and mark not in order['name']:
                order['name'] = mark + order['name']
                updated_orders.append(order)

        # Update orders remotely.
        orders = order_service.updateOrders(updated_orders)

        # Display results.
        if orders:
            for order in orders:
                print('Order with id {}, name {}, advertiser id {}, was updated.'
                      .format(order['id'], order['name'], order['advertiserId']))


def archive_orders(order_service, advertiserId, mark):
    num_orders_archived = 0

    while True:
        orders_statement = get_archived_target_orders(advertiserId, mark)
        statement_string = orders_statement.ToStatement()
        response = order_service.getOrdersByStatement(statement_string)

        if 'results' in response and len(response['results']) > 0:
            for order in response['results']:
                msg = 'Order with id "{id}", name "{name}", and status "{status}" will be archived.'.format(
                    id=order['id'],
                    name=order['name'],
                    status=order['status'])
                print(msg)

            result = order_service.performOrderAction(
                {'xsi_type': 'ArchiveOrders'}, statement_string)

            if result and int(result['numChanges']) > 0:
                num_orders_archived += int(result['numChanges'])
            orders_statement.offset += ad_manager.SUGGESTED_PAGE_LIMIT
        else:
            break

    if num_orders_archived > 0:
        print('Number of orders archived: {}'.format(num_orders_archived))
    else:
        print('No orders were archived.')


def main(advertiserId, mark):
    order_service = get_order_service()
    mark_orders(order_service, advertiserId, mark)
    archive_orders(order_service, advertiserId, mark)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Rename(mark) orders then archive it')
    parser.add_argument('--advertiserId', help='Advertiser / Company ID')
    parser.add_argument('--mark', default='(archived)',
                        help='Archive mark that will be prepended to order name')

    args = parser.parse_args()

    if args.advertiserId:
        main(args.advertiserId, args.mark)
