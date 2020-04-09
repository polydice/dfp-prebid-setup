import csv
from enum import IntEnum
from itertools import count


def parse_adunits_csv():
    """
        Parse and refine raw adunits CSV file
    """

    def parse_label_fields(row):
        row_without_empty = list(map(lambda e: e.strip() or "None", row))
        return IntEnum('Attr', zip(row_without_empty, count()))

    with open('adunits.csv', newline='') as csvfile:
        input_data = list(csv.reader(csvfile, delimiter=','))

        Label = parse_label_fields(input_data[0])
        input_data = input_data[1:]

        ad_networks = []
        ad_units = []
        sizes = []

        for row in input_data:
            ad_units.append(row[Label.master_adunit])
            sizes.append(row[Label.size])
            ad_networks.append(row[Label.adnetwork])

        return {
            'ad_units': ad_units,
            'ad_networks': ad_networks,
            'sizes': sizes
        }


if __name__ == "__main__":
    targeting_sheets = parse_adunits_csv()
    ad_units = targeting_sheets["ad_units"]
    sizes = targeting_sheets["sizes"]
    ad_networks = targeting_sheets["ad_networks"]

    print(sizes)
