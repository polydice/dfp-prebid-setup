from time import sleep
from googleads import ad_manager
from .services import *
from custom_tasks.parse_sponsorship_items import *

order_service = DfpServices.order_service()
line_item_service = DfpServices.line_item_service()


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


def main(order_id, rate_start_from):
    # Create statement object to only select line items with even delivery rates.
    statement = (DfpServices.statement()
                 .Where(('orderId = :orderId AND isArchived=False'))
                 .WithBindVariable('orderId', int(order_id))
                 .Limit(100))

    # Get line items by statement.
    response = line_item_service.getLineItemsByStatement(
        statement.ToStatement())

    """
        'costPerUnit': {
            'currencyCode': 'TWD',
            'microAmount': 24000000
        }
    },
    """
    line_items = response['results']
    if 'results' in response and len(line_items) == 77:
        # Update each local line item by changing its delivery rate type.
        updated_line_items = []

        for item in line_items:
            target_item_name = f"criteo: HB ${rate_start_from}.0"
            if item['name'] == target_item_name and item['lineItemType'] == 'SPONSORSHIP':
                item['name'] = item['name'] + " (DUP)"
                updated_line_items.append(item)

        # Update line items remotely.
        line_items = line_item_service.updateLineItems(updated_line_items)

        # Display results.
        if line_items:
            for line_item in line_items:
                print('Line item with id "%s", belonging to order id "%s", named '
                      '"%s"' % (line_item['id'], line_item['orderId'], line_item['name']))
        else:
            print('No line items were updated.')
    else:
        print('No line items found to update.')


def archive_line_items(order_id):
    pql = ' '.join((
        "orderId = :orderId AND",
        "lineItemType = 'SPONSORSHIP' AND",
        "isArchived = False AND",
        "name LIKE '%(DUP)'"
    ))
    statement = (DfpServices.statement()
                 .Where(pql)
                 .WithBindVariable('orderId', int(order_id))
                 .Limit(10))

    # Get line items by statement.
    response = line_item_service.getLineItemsByStatement(
        statement.ToStatement())

    if has_query_result(response):
        line_items = response['results']
        for item in line_items:
            print(
                f"Line items with {item['name']} belonging to {item['orderName']} will get archived")

    num_line_items_archived = 0

    while True:
        result = line_item_service.performLineItemAction(
            {'xsi_type': 'ArchiveLineItems'}, statement.ToStatement())

        if result and int(result['numChanges']) > 0:
            num_line_items_archived += int(result['numChanges'])
            statement.offset += ad_manager.SUGGESTED_PAGE_LIMIT
        else:
            break

        if num_line_items_archived > 0:
            print('Number of line-items archived: {}'.format(num_line_items_archived))
        else:
            print('No line-items were archived.')


if __name__ == '__main__':
    # Initialize client object.
    targets = parse_sponsorship_items()

    for target in targets:
        order = get_order(target['orderName'])
        if order:
            # main(order['id'], target['rate_start_from'])
            archive_line_items(order['id'])
