import requests, json, sys, traceback, time
from requests.auth import HTTPBasicAuth

api_username = ""
api_password = sys.argv[1]

hostd_hosts = [
    "localhost:9880"
]
renterd_hosts = [
    "localhost:10880"
]
walletd_hosts = [
    "localhost:9980"
]
# TODO: dynamically retrieve api endpoints
hostd_url_paths = [
    # hostd
    "/api/alerts",
    # "/api/contracts/:id/integrity",
    # "/api/contracts/:id",
    "/api/accounts",
    # accounts funding sources ??
    "/api/metrics",
    # "/api/metrics/:interval?start=2022-01-01T00:00:00-06:00&periods=12",
    "/api/settings",
    "/api/state/consensus",
    "/api/state/host",
    "/api/syncer/peers",
    "/api/syncer/address",
    # "/api/system/dir?path=~",
    "/api/tpool/fee",
    "/api/wallet",
    # "/api/wallet/transactions?limit=100&offset=0",
    "/api/wallet/pending",
    "/api/volumes"
    # "/api/volumes/:id"
]
renterd_url_paths = [
    # renterd
    "/api/bus/accounts",
    "/api/bus/alerts",
    "/api/bus/autopilots",
    # "/api/bus/autopilots/:id",
    # "/api/bus/buckets/:name",
    "/api/bus/consensus/state",
    # "/api/bus/consensus/siafundfee/:payout",
    # "/api/bus/contract/:id",
    # "/api/bus/contract/:id/ancestors",
    # "/api/bus/contract/:id/roots",
    # "/api/bus/contract/:id/size",
    "/api/bus/contracts",
    "/api/bus/contracts/prunable",
    # "/api/bus/contracts/renewed/:id",
    # "/api/bus/contracts/set/:set",
    "/api/bus/contracts/sets",
    # "/api/bus/host/:pubkey",
    "/api/bus/hosts?offset=0&limit=-1",
    "/api/bus/hosts/allowlist",
    "/api/bus/hosts/blocklist",
    # "/api/bus/hosts/scanning?offset=0&limit=10&lastScan=2023-03-30T15%3A45%3A52%2B02%3A00",
    # "/api/bus/objects/:key",
    # "/api/bus/params/download", # in api doc but 404
    "/api/bus/params/gouging",
    "/api/bus/params/upload",
    # "/api/bus/search/objects?offset=1&limit=1&key=Garfield&bucket=mybucket",
    "/api/bus/settings",
    # "/api/bus/setting/:key",
    # "/api/bus/slabs/partial/:key?=&offset=0&length=1",
    # "/api/bus/slab/:key/objects",
    "/api/bus/state",
    "/api/bus/stats/objects",
    "/api/bus/syncer/address",
    "/api/bus/syncer/peers",
    "/api/bus/txpool/recommendedfee",
    "/api/bus/txpool/transactions", ## ** fix the api doc page
    "/api/bus/wallet",
    # "/api/bus/wallet/address", #404
    # "/api/bus/wallet/balance", #404
    "/api/bus/wallet/outputs",
    "/api/bus/wallet/pending",
    "/api/bus/wallet/transactions",
    "/api/bus/webhooks",
    "/api/autopilot/config",
    # "/api/autopilot/host/:pubkey",
    "/api/autopilot/state",
    # "/api/worker/account/:hostkey",
    "/api/worker/id",
    # "/api/worker/objects/:key",
    "/api/worker/rhp/contracts",
    "/api/worker/state",
    "/api/worker/stats/downloads",
    "/api/worker/stats/uploads"
]
walletd_url_paths = [
    # walletd
    "/api/consensus/network",
    "/api/consensus/tip",
    "/api/consensus/tipstate",
    "/api/syncer/peers",
    "/api/txpool/transactions",
    "/api/txpool/fee",
    "/api/wallets",
    # "/api/wallets/:name/addresses",
    # "/api/wallets/:name/events?offset=0&limit=100",
    # "/api/wallets/:name/balance",
    # "/api/wallets/:name/txpool",
    # "/api/wallets/:name/outputs",
]

def http_request(url):
    response = requests.get(url, auth=HTTPBasicAuth(api_username, api_password))
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print(url)
        print(f"Request failed with status code: {response.status_code}")
        sys.exit(-1)

def flatten_json(json, path):
    j = None
    paths = []
    try:
        if isinstance(json, list):
            obj = {"path": "@this", "type": "list"}
            paths.append(obj)
            return paths
        else:
            j = json
        if not isinstance(j, dict):
            return
        for key, value in j.items():
            fieldpath = ""
            if path != "":
                fieldpath = path + "." + key
            else:
                fieldpath = key
            if isinstance(value, dict):
                paths += flatten_json(j[key], fieldpath)
            else:
                obj = {"path": fieldpath}
                if isinstance(value, str):
                    obj["type"] = "string"
                elif isinstance(value, bool):
                    obj["type"] = "bool"
                elif isinstance(value, int) or isinstance(value, float):
                    obj["type"] = "uint"
                elif isinstance(value, list):
                    obj["type"] = "list"
                else:
                    obj["type"] = "replaceme_" + str(type(value))
                paths.append(obj)
    except:
        print(j)
        traceback.print_exc()
        sys.exit(1)
    return paths

def get_telegraf_header(hosts, path, measurement_name, valueType = None):
    name = measurement_name + "_" + path.split("/")[-1]
    header = "[[inputs.http]]\n"
    header = header + "  urls = [\n"
    for host in hosts:
        if host == hosts[-1]:
            header = header + "    \"http://" + host + path + "\"\n"
        else:
            header = header + "    \"http://" + host + path + "\",\n"
    header = header + "  ]\n"
    header = header + "  method = \"GET\"\n"
    header = header + "  username = \"" + api_username + "\"\n"
    header = header + "  password = \"" + api_password + "\"\n"
    if valueType is None:
        header = header + "  data_format = \"json_v2\"\n"
        header = header + "  [[inputs.http.json_v2]]\n"
        header = header + "    measurement_name = \"" + name + "\"\n"
    else:
        header = header + "  data_format = \"value\"\n"
        header = header + "  data_type = \"" + valueType + "\"\n"
    return header

def get_telegraf_input(path):
    input_type = ("field", "object")[path["type"] == "list"]
    inputstr = "    [[inputs.http.json_v2." + input_type + "]]\n"
    inputstr = inputstr + "      path = \"" + path["path"] + "\"\n"
    if "." in path["path"] and input_type == "field":
        inputstr = inputstr + "      rename = \"" + path["path"].replace(".","_") + "\"\n"
    if input_type == "field":
        inputstr = inputstr + "      type = \"" + path["type"] + "\"\n"
    return inputstr

type_long_form = {
    str: "string",
    int: "integer",
    float: "float",
}

# test
# path_map = {
#     "renterd": {
#         "hosts": [
#             "localhost:10880"
#         ], 
#         "url_paths": [
#             "/api/bus/settings",
#             "/api/bus/state"
#         ]
#     }
# }

# full
path_map = {
    "hostd": {"hosts": hostd_hosts, "url_paths": hostd_url_paths},
    "renterd": {"hosts": renterd_hosts, "url_paths": renterd_url_paths},
    "walletd": {"hosts": walletd_hosts, "url_paths": walletd_url_paths},
}

def get_telegraf_config(service, url_path, elapsed_time, json_data):
    config = "# " + service + " " + url_path + " - " + str(elapsed_time) + "\n"
    if not isinstance(json_data, dict) and not isinstance(json_data, list):
        config = config + get_telegraf_header(path_map[service]["hosts"], url_path, service, type_long_form[type(json_data)])
    else:
        fields = flatten_json(json_data, "")
        if fields is not None:
            config = config + get_telegraf_header(path_map[service]["hosts"], url_path, service)
            for field in fields:
                config = config + get_telegraf_input(field)
    return config + "\n"

tconf = {'config':"",'responses':[]}
for service, object in path_map.items():
    for url_path in object["url_paths"]:
        full_url = "http://" + path_map[service]["hosts"][0] + url_path
        start = time.time()
        json_data = http_request(full_url)
        end = time.time()
        elapsed_time = end - start
        tconf['config'] = tconf['config'] + get_telegraf_config(service, url_path, elapsed_time, json_data)
        tconf['responses'].append({'info': service + " " + url_path, 'response': json_data})

with open('sia-telegraf-http-inputs.conf', 'w') as file:
    file.write(tconf['config'])

with open('sia-api-responses.json', 'w') as file:
    for response in tconf['responses']:
        file.write(response['info'] + '\n')
        file.write(json.dumps(response['response'], indent=2) + '\n\n')

# https://api.sia.tech/hostd#1d0bd787-737a-4107-8d1c-b1ce2ddbe215 empty