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

"""
    This code unarchives target orders.
"""


import datetime
from googleads import ad_manager
from dfp.client import get_client


ACTION = 'UnarchiveOrders'
OPENX_ID = 4832733284
VERSION = 'v201911'


def get_order_service():
    dfp_client = get_client()
    return dfp_client.GetService('OrderService', version=VERSION)


def get_orders_by_advertiser(advertiserId, print_orders=False):
    statement = (ad_manager.StatementBuilder(version=VERSION)
                 .Where("advertiserId = :advertiserId \
                         AND isArchived = TRUE \
                         AND name LIKE 'Prebid OpenX %'")
                 .WithBindVariable('advertiserId', advertiserId))

    if print_orders:
        while True:
            order_service = get_order_service()
            response = order_service.getOrdersByStatement(
                statement.ToStatement()
            )
            if 'results' in response and len(response['results']) > 0:
                for order in response['results']:
                    # Print out some information for each order.
                    msg = 'Order with ID {id}, name {name}, isArchived={isArchived} was found.\n'.format(
                        id=order['id'],
                        name=order['name'],
                        isArchived=order['isArchived']
                    )
                    print(msg)
                statement.offset += ad_manager.SUGGESTED_PAGE_LIMIT
            else:
                print('No additional orders found.')
                break

    return statement


def main():
    orders_unarchived = 0

    while True:
        order_service = get_order_service()
        statement = get_orders_by_advertiser(OPENX_ID)
        statement_string = statement.ToStatement()
        response = order_service.getOrdersByStatement(statement_string)

        if 'results' in response and len(response['results']) > 0:
            for order in response['results']:
                msg = 'Order with id "{id}", name "{name}", and status "{status}" will be unarchived.' \
                    .format(
                        id=order['id'],
                        name=order['name'],
                        status=order['status'])
                print(msg)

            result = order_service.performOrderAction(
                {'xsi_type': ACTION}, statement_string)

            if result and int(result['numChanges']) > 0:
                orders_unarchived += int(result['numChanges'])

            statement.offset += ad_manager.SUGGESTED_PAGE_LIMIT
        else:
            break

    if orders_unarchived > 0:
        print('Number of orders unarchived: {}'.format(orders_unarchived))
    else:
        print('No orders were unarchived.')


if __name__ == '__main__':
    main()
