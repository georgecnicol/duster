# basically a depth first graph traversal and json parsing exercise
# where the application is automating crypto intelligence research
# for dusting attacks to find accounts of value associated with attack
# if mulitple addresses are included in a file, one address per line
# the product application was unstable so I had to heavily rate limit
# the requests using sleep function.



import requests, argparse
import time # rate limiting

######## vars #####################
wallet_address = ''
coin = ''
auth = ''
false = 'false'
date_min = '2021-01-01T00:00:00.000Z'
date_max = '2022-01-08T00:00:00.000Z'
viewed_addresses = set()
headers = {"Content-Type": "application/json"}


######## api endpoints used ###########
screen_url = "https://api.xxxxx.com/public/v1/screening/addresses"              (company name withheld)
# payload = [{"address": "w62rY42GcmqNsXUzSStKeq", "chain": "bitcoin"}]         (example, not real address)
# payload = [{"address": x, "chain": args.coin[0]} for x in wallet_address]     (documentation)
transaction_url = "https://api.xxxx.com/insights/v3/transaction/address"        (company name withheld)
# payload = {"address":{"address":"ONV2ZLVRBIJVKS4FKJQ7O7NBVV","chain":"xlm"},  (example, not a real address)
#           "includeRawTx":false,"limit":25,"offset":0,"organizationId":123,"truncateUtxos":false,"assetAddresses":null,
#           "fromDate":null,"tillDate":null,"direction":"in"}


######### parse args #######
parser = argparse.ArgumentParser()
parser.set_defaults(cred_path = './creds.txt')
parser.add_argument('-c', dest = 'coin', nargs = 1, required = True, help = "coin, eg: bitcoin, stellar")
parser.add_argument('-d', dest = 'depth', nargs = 1, required = True, type = int, choices = range(1,5) , help = "depth first traversal max depth")
group = parser.add_mutually_exclusive_group(required = True)
group.add_argument('-a', dest = 'address',  help = "Either an address or a file containing multiple addresses")
group.add_argument('-f', dest = 'file_path', help = "But not both. Addresses must all be of same asset type")

args = parser.parse_args()


######## handle auth ##############
with open(args.cred_path, 'r') as fh:
  creds = fh.read()
  creds = creds.split(',')
  auth = (creds[0],creds[1])


######## set the coin chain ##############
coin = args.coin[0]


######## set the depth ##############
depth = args.depth[0]


######## get the address(es) #############
if args.address:
  wallet_address = [args.address]
else:
  with open(args.file_path, 'r') as fh:
    wallet_address = fh.read().strip()
    wallet_address = wallet_address.split('\n')


def screen_address(address):
  time.sleep(1)
  payload = [{"address": address, "chain": coin}]
  response = requests.post(screen_url, json=payload, headers=headers, auth=auth)
  screen_result = ''
  for result in response.json():
    if len(result['addressRiskIndicators']) > 0 or len(result['entities']) > 0:
      screen_result = f'endpoint\n'
      if len(result['addressRiskIndicators']) > 0:
        screen_result += f"{result['address']} Risk Indicators: "
        for indicator in result['addressRiskIndicators']:
          screen_result += f"{indicator['categoryRiskScoreLevelLabel']} risk of {indicator['category']} due to/ from {indicator['riskType']}.\n"

      if len(result['entities']) > 0:
        screen_result += f"{result['address']} Entities: "
        for entity in result['entities']:
          screen_result += f"{entity['riskScoreLevelLabel']} risk of {entity['category']} due to/from {entity['entity']}.\n"

  return screen_result


def get_transactions(address):
  time.sleep(1)
  next_set = set()
  payload2 = {"address": {"address": address, "chain": coin}, "includeRawTx":False,"limit":25,"offset":0,"organizationId":123,"truncateUtxos":False,"assetAddresses":None, "fromDate":date_min,"tillDate":date_max,"direction":"in"}
  response2 = requests.post(transaction_url, json=payload2, headers=headers, auth=auth)
  for transaction in response2.json()['data']['transactions']:
    next_set.add(f"{transaction['from'][0]['address']}")
  return next_set

# screen results are a stop condition
def addr_recurse(depth, addr_set):
  result = ''
  count = 0

  for addr in addr_set:
    time.sleep(2)  # rate limit
    if addr not in viewed_addresses:  # first check to see if going in circles
      viewed_addresses.add(addr)
      intermediate_result = screen_address(addr)
      if intermediate_result != '':   #we have a stopping condition
        result += intermediate_result
      elif depth < 1:  # we are at max depth so we are done
        result += intermediate_result
      else: # ok, now you can do recursive things
        intermediate_result = addr_recurse(depth-1, (get_transactions(addr)))
        if intermediate_result != '':
          result += addr + ' --> ' + intermediate_result

  return result

if __name__ == '__main__':
  print(addr_recurse(depth, wallet_address))
  print(f'Number of addresses scanned: {len(viewed_addresses)}')

