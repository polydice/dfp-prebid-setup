
import datetime
from googleads import ad_manager
from dfp.client import get_client
from .services import *

line_item_service = DfpServices.line_item_service()

ANDROID_APP_ID = 14357


def get_line_items(order_id):
    return (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
            .Where("orderId = :order_id AND status != 'PAUSED'")
            .WithBindVariable('order_id', order_id)
            .Limit(500))


def update_line_items(line_items):
    updated_line_items = []
    for i, item in enumerate(line_items):
        item['targeting']['mobileApplicationTargeting'] = {
            'mobileApplicationIds': [ANDROID_APP_ID],
            'isTargeted': True
        }
        updated_line_items.append(item)

    line_items = line_item_service.updateLineItems(updated_line_items)
    if line_items:
        for item in line_items:
            print("order {} - Line item named {} and mobileApplicationTargeting {} was updated".format(
                item['orderName'], item['name'], item['targeting']['mobileApplicationTargeting']))
    else:
        print('No line items were updated.')


def main(order_ids):
    for id in order_ids:
        statement = get_line_items(id)
        response = line_item_service.getLineItemsByStatement(
            statement.ToStatement())

        line_items = response['results']
        if 'results' in response and len(line_items) > 0:
            update_line_items(line_items)


if __name__ == '__main__':
    order_ids = [
        '2692880126',
        '2692882943',
        '2693254777'
    ]
    main(order_ids)

    # Debug - find mobile app id
    # statement = (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
    #              .Where('id = :id')
    #              .WithBindVariable('id', 751759843))
    # while True:
    #     response = line_item_service.getLineItemsByStatement(statement.ToStatement(
    #     ))
    #     if 'results' in response and len(response['results']):
    #         for line_item in response['results']:
    #             print(line_item)
    #         statement.offset += statement.limit
    #     else:
    #         break
