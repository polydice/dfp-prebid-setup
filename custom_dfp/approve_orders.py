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


import datetime
from googleads import ad_manager
from .services import *

order_service = DfpServices.order_service()

ADVERTISER_ID = 4824733092


def get_orders_by_advertiser(print_orders=False):
    statement = (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
                 .Where("status in ('DRAFT', 'PENDING_APPROVAL') \
                         AND advertiserId = :advertiserId \
                         AND isArchived = FALSE")
                 .WithBindVariable('advertiserId', ADVERTISER_ID))

    if print_orders:
        while True:
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
                statement.offset += 20
            else:
                print('No additional orders found.')
                break

    return statement


def get_app_orders():
    statement = (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
                 .Where("status = 'DRAFT' \
                         AND isArchived = FALSE \
                         AND name LIKE 'Prebid % iCook_Android_%'"))

    return statement


def main():
    orders_approved = 0

    statement = get_orders_by_advertiser()
    # statement = get_app_orders()

    while True:
        response = order_service.getOrdersByStatement(statement.ToStatement())

        if 'results' in response and len(response['results']) > 0:
            for order in response['results']:
                msg = 'Order with id "{id}", name "{name}", and status "{status}" will be approved.' \
                    .format(
                        id=order['id'],
                        name=order['name'],
                        status=order['status'])
                print(msg)
            print(f'Total {len(response["results"])} orders will be apporved')

            result = order_service.performOrderAction(
                {'xsi_type': 'ApproveOrders'},
                statement.ToStatement()
            )
            if result and int(result['numChanges']) > 0:
                orders_approved += int(result['numChanges'])
            statement.offset += ad_manager.SUGGESTED_PAGE_LIMIT
        else:
            break

    if orders_approved > 0:
        print(f'{orders_approved} orders have been approved')
    else:
        print('None of orders approved.')


if __name__ == '__main__':
    main()
