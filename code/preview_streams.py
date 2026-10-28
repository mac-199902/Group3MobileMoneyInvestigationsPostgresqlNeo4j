import sys
import pprint
from itertools import islice
import mobile_money_generator as g

mode = sys.argv[1] if len(sys.argv) > 1 else "info"

if mode == "info":
    print("g.dataset_info():")
    pprint.pprint(g.dataset_info(), sort_dicts=False, width=110)
    print("\ng.FIELDS:")
    pprint.pprint(g.FIELDS, sort_dicts=False, width=110)

else:
    streams = {
        "customers": g.iter_customers,
        "accounts": g.iter_accounts,
        "devices": g.iter_devices,
        "account_devices": g.iter_account_devices,
        "transfers": g.iter_transfers,
    }
    for name, make_iterator in streams.items():
        print(f"--- {name}: first 10 records ---")
        for row in islice(make_iterator(), 10):
            print(row)