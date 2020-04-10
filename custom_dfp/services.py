from googleads import ad_manager
from dfp.client import get_client


DFP_SERVICE_VERSION = 'v201911'


class DfpServices:

    dfp_client = get_client()

    @classmethod
    def order_service(cls):
        return cls.dfp_client.GetService(
            'OrderService', version=DFP_SERVICE_VERSION)

    @classmethod
    def line_item_service(cls):
        return cls.dfp_client.GetService(
            'LineItemService', version=DFP_SERVICE_VERSION)

    @classmethod
    def lica_service(cls):
        return cls.dfp_client.GetService(
            'LineItemCreativeAssociationService', version=DFP_SERVICE_VERSION)

    @classmethod
    def creative_service(cls):
        return cls.dfp_client.GetService(
            'CreativeService', version=DFP_SERVICE_VERSION)

    @staticmethod
    def statement():
        return ad_manager.StatementBuilder(version=DFP_SERVICE_VERSION)


def has_query_result(response):
    return 'results' in response and len(response['results']) > 0


if __name__ == "__main__":
    print(DfpServices.line_item_service())
