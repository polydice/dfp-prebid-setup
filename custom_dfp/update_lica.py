#!/usr/bin/env python
# -*- coding: utf-8 -*-


from zeep.helpers import serialize_object
from googleads import ad_manager

from .services import *

line_item_service = DfpServices.line_item_service()
lica_service = DfpServices.lica_service()


def add_size_to_lica(line_item, size):
    statement = (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
                 .Where('lineItemId = :lineItemId')
                 .WithBindVariable('lineItemId', line_item['id']))
    while True:
        response = lica_service.getLineItemCreativeAssociationsByStatement(
            statement.ToStatement())
        if 'results' in response and len(response['results']):
            updated_licas = []
            for lica in response['results']:
                new_lica_sizes = []
                if len(lica['sizes']) == 1:
                    sz = lica['sizes'][0]
                    new_lica_sizes.extend([
                        sz,
                        {
                            'width': size[0],
                            'height': size[1],
                            'isAspectRatio': False
                        }
                    ])
                lica['sizes'] = new_lica_sizes
                updated_licas.append(lica)

            licas = lica_service.updateLineItemCreativeAssociations(
                updated_licas)
            for lica in licas:
                print('LICA with item id {}, creative id {} and sizes was updated.'.format(
                    lica['lineItemId'], lica['creativeId'], lica['sizes']))

            statement.offset += statement.limit
        else:
            break


def update_lineitems(line_items, size):
    skipped_order = None

    updated_line_items = []
    for i, line_item in enumerate(line_items):
        if not line_item['isArchived']:
            new_creative_placeholders = []
            creative_placeholders = line_item['creativePlaceholders']

            if len(creative_placeholders) == 1:
                c = serialize_object(creative_placeholders[0])
                new_creative_placeholders.extend([
                    c,
                    {
                        **c,
                        'size': {
                            'width': size[0],
                            'height': size[1],
                            'isAspectRatio': False
                        }
                    }
                ])
            else:
                skipped_order = line_item['orderName']
                break

            line_item['creativePlaceholders'] = new_creative_placeholders
            updated_line_items.append(line_item)

    if not skipped_order:
        print('🏃 Adding size config...')
        # for line_item in updated_line_items:
        #     for c in line_item['creativePlaceholders']:
        #         print(c['size'])

        # Update line items remotely.
        # line_items = line_item_service.updateLineItems(updated_line_items)

        # Display results.
        # if line_items:
        #     for line_item in line_items:
        #         print("order {} - Line item with id {}, named {}, size: {} was updated".format(
        #             line_item['orderName'], line_item['id'], line_item['name'], line_item['creativePlaceholders'][0]['size']))
        # else:
        #     print('No line items were updated.')

    return skipped_order


def add_size_to_lineitem(orderName, size):
    statement = (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
                 .Where("orderName LIKE '{} %x%' AND status != 'PAUSED'".format(orderName))
                 .Limit(500))

    # Get line items by statement.
    response = line_item_service.getLineItemsByStatement(
        statement.ToStatement())

    if 'results' in response and len(response['results']):
        print('{} ({} line items) - try adding size {}x{}'.format(
            orderName, len(response['results']), size[0], size[1]))

        line_items = response['results']
        skipped_order = update_lineitems(line_items, size)

        if skipped_order:
            print('✅ {} have setup multi-size'.format(skipped_order))
        else:
            None
            # for i, line_item in enumerate(line_items):
            #     add_size_to_lica(line_item, size)
        print()

    else:
        print('⚠️  Order {} - no line items need to update.\n'.format(orderName))


if __name__ == '__main__':
    main()
