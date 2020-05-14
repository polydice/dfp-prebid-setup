
import re
import datetime
from googleads import ad_manager
from dfp.client import get_client
from .services import *

order_service = DfpServices.order_service()
line_item_service = DfpServices.line_item_service()

APP_ID = {
    'Android': 14357,
    'iPhone': 14950
}

app_type = "iPhone"
app_id = APP_ID[app_type]  # see the key of APP_ID


def get_orders():
    statement = (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
                 .Where("status = 'DRAFT' \
                         AND isArchived = FALSE \
                         AND name LIKE 'Prebid % iCook_App_%'"))

    response = order_service.getOrdersByStatement(
        statement.ToStatement())

    return response['results'] \
        if has_query_result(response) \
        else None


def get_line_items(order_id):
    return (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
            .Where("orderId = :order_id AND status != 'PAUSED'")
            .WithBindVariable('order_id', order_id)
            .Limit(500))


def update_line_items(line_items):
    updated_line_items = []

    for i, item in enumerate(line_items):
        item['targeting']['mobileApplicationTargeting'] = {
            'mobileApplicationIds': [app_id],
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


def replace_unit_name(name):
    return re.sub(r"_(App)_", f"_{app_type}_", name, flags=re.IGNORECASE)


def main():
    updated_orders = []

    orders = get_orders()
    if orders:
        for order in orders:
            order['name'] = replace_unit_name(order['name'])
            updated_orders.append(order)

        # Update orders remotely.
        orders_with_newname = order_service.updateOrders(updated_orders)
        for order in orders_with_newname:
            print(order['name'],
                  f'renamed with its mobile platform {app_type}')
        print("\n\n")

        for order in orders:
            statement = get_line_items(order['id'])
            response = line_item_service.getLineItemsByStatement(
                statement.ToStatement())

            line_items = response['results']
            if 'results' in response and len(line_items) > 0:
                update_line_items(line_items)


if __name__ == '__main__':
    main()

    # Debug - find mobile app id
    # statement = (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
    #              .Where('id = :id')
    #              .WithBindVariable('id', 751760923))
    # while True:
    #     response = line_item_service.getLineItemsByStatement(statement.ToStatement(
    #     ))
    #     if 'results' in response and len(response['results']):
    #         for line_item in response['results']:
    #             print(line_item)
    #         statement.offset += statement.limit
    #     else:
    #         break
