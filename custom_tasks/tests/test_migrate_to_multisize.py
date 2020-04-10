import sys
import pprint
import unittest
import argparse
from dfp.client import get_client

from custom_dfp.services import *
from custom_tasks.utils import log
from custom_tasks.migrate_to_multisize.excluded_keywords import is_excluded_order

ADVERTISER_ID = '4647760051'


order_service = DfpServices.order_service()
line_item_service = DfpServices.line_item_service()
lica_service = DfpServices.lica_service()


def get_orders(advertiserId: str):
    statement = (DfpServices.statement()
                 .Where("advertiserId = :advertiserId \
                         AND status = 'APPROVED' \
                         AND isArchived = FALSE \
                         AND name LIKE 'Prebid % %x%'")
                 .WithBindVariable('advertiserId', advertiserId))
    response = order_service.getOrdersByStatement(
        statement.ToStatement())

    return response['results'] \
        if has_query_result(response) \
        else None


def get_line_items(order_name: str):
    statement = (DfpServices.statement()
                 .Where("orderName = :order_name AND status != 'PAUSED'")
                 .WithBindVariable('order_name', order_name)
                 .Limit(500))
    response = line_item_service.getLineItemsByStatement(
        statement.ToStatement())
    return response['results'] \
        if has_query_result(response) \
        else None


def determine_size(order_name: str):
    name = order_name.lower()
    if 'sticky' in name:
        if '320x100' in name:
            return (320, 50)
        else:
            return (320, 100)
    else:
        return (336, 280)


def prepare_test_data(advertiserId: str):
    """ Test data schema
        [(
            order_name,
            new_size
            [line_items_creativePlaceholders_sizes],
        )]

        line_item:
            - number of creativePlaceholders
            - number of creative sizes

        new_size: (width, height)
    """
    def get_line_item_sizes(line_item):
        creative_placeholders = line_item['creativePlaceholders']
        return list(map(
            lambda p: (p['size']['width'], p['size']['height']),
            creative_placeholders))

    def get_lica_sizes(lica):
        return list(map(lambda size: (size['width'], size['height']), lica['sizes']))

    test_data = []

    orders = get_orders(advertiserId)
    if not orders:
        log('No orders', type='warn')
        return

    log('Preparing test data...', type='progress')
    print(len(orders))
    for i, order in enumerate(orders):
        # if i > 10:
        #     break
        order_name = order['name']

        if is_excluded_order(order_name):
            continue

        new_size = determine_size(order_name)

        line_items_sizes = None

        line_items = get_line_items(order_name)
        if line_items:
            line_items_sizes = list(
                map(lambda item: get_line_item_sizes(item), line_items))

        test_data.append((
            order_name,
            new_size,
            line_items_sizes,
        ))

    return test_data


def get_size_from_order_name(order_name):
    return tuple(map(int, order_name.split(' ')[-1].split('x')))


def init_args():
    parser = argparse.ArgumentParser(
        description='Migrate single-size unit to multi-size')
    parser.add_argument(
        '--show-data',
        action='store_const',
        const=True,
        help='Print out test data retrieved from AdManager')
    return parser.parse_args()


class MigrateToMultiSizeTest(unittest.TestCase):
    test_data = prepare_test_data(ADVERTISER_ID)

    def test_line_items_new_size_setup(self):
        log('Verify every order has setup new size...', type='progress')
        for i, order in enumerate(self.test_data):
            [name, new_size, creative_placeholders_sizes] = order
            log('Test order {}'.format(name), type='progress')
            size = get_size_from_order_name(name)
            self.assertNotEqual(
                new_size,
                size
            )
            for sizes in creative_placeholders_sizes:
                self.assertEqual(len(sizes), 2)
                self.assertIn(size, sizes)
                self.assertIn(new_size, sizes)

            log('{} - Order {} passed\n'.format(i+1, name), type='passed')


if __name__ == "__main__":
    # args = init_args()

    # if args.show_data:
    #     test_data = prepare_test_data(ADVERTISER_ID)
    #     for i, item in enumerate(test_data):
    #         if i == 2:
    #             pprint.pprint(item)
    #             break
    #     sys.exit(0)

    unittest.main()
