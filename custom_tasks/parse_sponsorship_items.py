import csv
from enum import IntEnum
from itertools import count


def remove_item_spaces(ls):
    return list(map(lambda s: s.replace(' ', ''), ls))


def parse_sponsorship_items():
    def parse_label_fields(row):
        row_without_empty = list(map(lambda e: e.strip() or "None", row))
        return IntEnum('Attr', zip(row_without_empty, count()))

    with open('sponsorship_items.csv', newline='') as csvfile:
        input_data = list(csv.reader(csvfile, delimiter=','))

        Label = parse_label_fields(input_data[0])
        input_data = input_data[1:]

        result = []
        for row in input_data:
            order = row[Label['Order']]
            unit = row[Label['Ad unit']]
            rate_greater_than = int(row[Label['Rate greater than']])
            result.append({
                'unit': unit,
                'orderName': order,
                'rate_start_from': rate_greater_than
            })

        return result


if __name__ == "__main__":
    result = parse_sponsorship_items()

    for item in result:
        print(item)
        break
