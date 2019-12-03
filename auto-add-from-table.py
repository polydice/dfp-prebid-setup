import os
import subprocess

# THESE array is the data copied from spreadsheet given from PM.

ADUNITS = [
    'Blog_Post_Article_Top_MB',
    'Blog_Post_Article_Middle_MB',
    'Blog_Post_Article_Bottom_MB'
]

SIZES = [
    '300x250',
    '300x250',
    '300x250'
]

ADNETWORKS = [
    'FAN',
    'FAN',
    'FAN'
]

ORDER_DICT = {
   'FAN': 'Audience Network'
}

ADVERTISER_DICT = {
   'FAN': 'Facebook'
}


def get_order_name(ad_network):
   try:
      return ORDER_DICT[ad_network]
   except:
      return ad_network


def get_advertiser_name(ad_network):
   try:
      return ADVERTISER_DICT[ad_network]
   except:
      return ad_network


BIDDER_CODES = {
   'FAN': 'audienceNetwork',
   'AppNexus': 'appnexus',
   'ucfunnel': 'ucfunnel',
   'Bridgewell': 'bridgewell',
   'Appier': 'appier',
   'Innity': 'innity'
}

count = 0
for i, adunit_name in enumerate(ADUNITS):
   if i == 0:
      continue;
   size = SIZES[i]
   ad_network = ADNETWORKS[i]
   order_name = get_order_name(ad_network)
   advertiser_name = get_advertiser_name(ad_network)
   bidder_code = BIDDER_CODES[ad_network]

   print('Input:\nADUNIT_NAME: {}\nsize: {}\nad_network: {}\nORDER_NAME: {}\nADVERTISER_NAME: {}\nBIDDER_CODE: {}'.format(
      adunit_name, size, ad_network, order_name, advertiser_name, bidder_code))
   [width, height] = size.split("x")

   input_file = open("settings_template.py", "r")
   output_file = open("settings.py", "w")
   output_file.write(
      input_file.read()
      .replace("[[ADUNIT_NAME]]", adunit_name)
      .replace("[[WIDTH]]", width)
      .replace("[[HEIGHT]]", height)
      .replace("[[ORDER_NAME]]", order_name)
      .replace("[[ADVERTISER_NAME]]", advertiser_name)
      .replace("[[BIDDER_CODE]]", bidder_code))

   input_file.close()
   output_file.close()

   command_run = subprocess.call(["yes y | python3 -m tasks.add_new_prebid_partner"], shell=True)
   if command_run == 0:
      count += 1
   else:
      raise SystemExit(0)
      

print('Total {} ad units'.format(count))
