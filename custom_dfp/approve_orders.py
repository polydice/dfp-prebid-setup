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
    This code approves all eligible draft and pending orders.
"""


import argparse
import datetime
from googleads import ad_manager
from dfp.client import get_client
from .dfp_settings import *


def get_order_service():
    dfp_client = get_client()
    return dfp_client.GetService('OrderService', version=DFP_SERVICE_VERSION)


def get_orders_by_advertiser(advertiserId, print_orders=False):
    statement = (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
                 .Where("status in ('DRAFT', 'PENDING_APPROVAL') \
                         AND advertiserId = :advertiserId \
                         AND isArchived = FALSE \
                         AND name LIKE 'Prebid %'")
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
                    msg = 'Order with ID {id} and name {name} was found.\n'.format(
                        id=order['id'],
                        name=order['name']
                    )
                    print(msg)
                statement.offset += ad_manager.SUGGESTED_PAGE_LIMIT
            else:
                print('No additional orders found.')
                break

    return statement


def main(advertiserId):
    orders_approved = 0

    order_service = get_order_service()
    statement = get_orders_by_advertiser(advertiserId)

    while True:
        statement_string = statement.ToStatement()
        response = order_service.getOrdersByStatement(statement_string)

        if 'results' in response and len(response['results']) > 0:
            for order in response['results']:
                msg = 'Order with id "{id}", name "{name}", and status "{status}" will be approved.' \
                    .format(
                        id=order['id'],
                        name=order['name'],
                        status=order['status'])
                print(msg)

            result = order_service.performOrderAction(
                {'xsi_type': 'ApproveOrders'},
                statement_string
            )
            if result and int(result['numChanges']) > 0:
                orders_approved += int(result['numChanges'])
            statement.offset += ad_manager.SUGGESTED_PAGE_LIMIT
        else:
            break

    if orders_approved > 0:
        print('Number of orders approved: %s' % orders_approved)
    else:
        print('No orders were approved.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Approve orders')
    parser.add_argument('--advertiserId', help='Advertiser / Company ID')

    args = parser.parse_args()

    if args.advertiserId:
        main(args.advertiserId)
