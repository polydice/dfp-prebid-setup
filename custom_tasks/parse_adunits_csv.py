import csv
from enum import IntEnum
from itertools import count


def remove_item_spaces(ls):
    return list(map(lambda s: s.replace(' ', ''), ls))


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
        adnetwork_units = []
        sizes = []
        actual_sizes = []

        for row in input_data:
            ad_units.append(row[Label.master_adunit])
            adnetwork_units.append(row[Label.adnetwork_adunits])

            sizes.append(row[Label.size])

            if row[Label.size].lower() == 'sizeless':
                actual_sizes.append(row[Label.real_sizes])
            else:
                actual_sizes.append(row[Label.size])

            ad_networks.append(row[Label.adnetwork])

        return {
            'ad_units': ad_units,
            'adnetwork_units': adnetwork_units,
            'ad_networks': ad_networks,
            'sizes': remove_item_spaces(sizes),
            'actual_sizes': remove_item_spaces(actual_sizes)
        }


if __name__ == "__main__":
    targeting_sheets = parse_adunits_csv()
    ad_units = targeting_sheets["ad_units"]
    sizes = targeting_sheets["sizes"]
    ad_networks = targeting_sheets["ad_networks"]

    print(sizes)
