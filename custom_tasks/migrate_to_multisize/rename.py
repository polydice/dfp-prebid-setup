import re
import argparse
from googleads import ad_manager
from dfp.client import get_client

from custom_dfp.services import *
from custom_tasks.utils import log
from .excluded_keywords import is_excluded_order

order_service = DfpServices.order_service()
line_item_service = DfpServices.line_item_service()
lica_service = DfpServices.lica_service()
creative_service = DfpServices.creative_service()


def get_orders(advertiserId):
    statement = (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
                 .Where("advertiserId = :advertiserId \
                         AND status = 'DRAFT' \
                         AND isArchived = FALSE \
                         AND name LIKE '(TEST) Prebid %'")
                 .WithBindVariable('advertiserId', advertiserId))

    response = order_service.getOrdersByStatement(
        statement.ToStatement())

    return response['results'] \
        if has_query_result(response) \
        else None


def get_line_items(order_id: str):
    statement = (DfpServices.statement()
                 .Where("orderId = :order_id AND status != 'PAUSED'")
                 .WithBindVariable('order_id', order_id)
                 .Limit(500))
    response = line_item_service.getLineItemsByStatement(
        statement.ToStatement())
    return response['results'] \
        if has_query_result(response) \
        else None


def get_licas(line_item_id):
    statement = (ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)
                 .Where('lineItemId = :lineItemId')
                 .WithBindVariable('lineItemId', line_item_id))
    response = lica_service.getLineItemCreativeAssociationsByStatement(
        statement.ToStatement())
    return response['results'] \
        if has_query_result(response) \
        else None


def get_creatives(order_name):
    statement = (DfpServices.statement()
                 .Where("name LIKE 'appier: HB Prebid Appier Blog_Post_Article_Bottom_MB %'")
                 .WithBindVariable('order_name', order_name))
    response = creative_service.getCreativesByStatement(
        statement.ToStatement())
    return response['results'] \
        if has_query_result(response) \
        else None


def rename_creatives(order):
    order_name = order['name'].replace('(TEST) ', '')
    creatives = get_creatives(order_name)
    if creatives:
        for creative in creatives:
            log(creative['id'], ' - ', creative['name'])


def rename_orders(orders):
    def strip(name):
        return re.sub('\d+x\d+', '',  name).strip()

    for order in orders:
        if not is_excluded_order(order['name']):
            new_order_name = strip(order['name'])
            rename_creatives(order)


def main(advertiserId):
    orders = get_orders(advertiserId)
    if orders:
        rename_orders(orders)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Remove widthxheight from order names and creative names')
    parser.add_argument('advertiserId')
    args = parser.parse_args()

    if args.advertiserId:
        main(args.advertiserId)
