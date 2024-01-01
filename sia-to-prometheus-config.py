import requests
from requests.auth import HTTPBasicAuth

hostd_un = ""
hostd_pw = "hostsarecool"

hostd_hosts = [
    "localhost:9880",
]

hostd_endpoints = [
    "/prometheus/state/host",
    "/prometheus/state/consensus",
    "/prometheus/syncer/address",
    "/prometheus/syncer/peers",
    "/prometheus/alerts",
    "/prometheus/settings",
    "/prometheus/metrics",
    "/prometheus/accounts",
    "/prometheus/volumes",
    "/prometheus/sessions",
    "/prometheus/tpool/fee",
    "/prometheus/wallet",
    "/prometheus/wallet/transactions",
    "/prometheus/wallet/pending",
]

walletd_hosts = [
    "localhost:9980"
]

walletd_endpoints = [
    "/prometheus/consensus/network",
    "/prometheus/consensus/tip",
    "/prometheus/syncer/peers",
    "/prometheus/txpool/fee",
    "/prometheus/wallets/:name/balance", # name retrieved dynamically from walletd_hosts /wallets api endpoint first
    "/prometheus/wallets/:name/events", # name retrieved dynamically from walletd_hosts /wallets api endpoint first
]

walletd_un = ""
walletd_pw = "hostsarecool"

config_header = """# sia global config
global:
  scrape_interval: 15s # Set the scrape interval to every 15 seconds. Default is every 1 minute.
  evaluation_interval: 15s # Evaluate rules every 15 seconds. The default is every 1 minute.
  # scrape_timeout is set to the global default (10s).

scrape_configs:
"""

def get_prometheus_job(un, pw, job_name, metrics_path, hosts):
    retstr = """  - job_name: """ + job_name + """
    metrics_path: """ + metrics_path + """
    basic_auth:
      username: '""" + un + """'
      password: '""" + pw + """'
    static_configs:
      - targets:
"""
    for host in hosts:
        retstr = retstr + "        - " + host + "\n"
    return retstr

def get_wallets(un, pw, host):
    wallets = []
    url = "http://" + host + "/api/wallets"
    r = requests.get(url, auth=HTTPBasicAuth(un, pw))
    for wallet in list(r.json().keys()):
        if wallet != "primary":
            wallets.append(wallet)
    return wallets

## WALLETD
jobs = ""
for host in walletd_hosts:
    wallets = get_wallets(walletd_un, walletd_pw, host)
    for endpoint in walletd_endpoints:
        if ":name" in endpoint:
            for wallet in wallets:
                job_name = endpoint.replace(":name",wallet)
                job_name = job_name.split("/")[2:]
                job_name.insert(1,host.split(":")[0])
                job_name.insert(2,host.split(":")[1])
                job_name = "walletd_" + "_".join(job_name)
                jobs = jobs + get_prometheus_job(walletd_un, walletd_pw, job_name, endpoint.replace(":name",wallet), [host]) + "\n\n"

for endpoint in walletd_endpoints:
    if ":name" not in endpoint:
        job_name = "walletd_" + "_".join(endpoint.split("/")[2:])
        jobs = jobs + get_prometheus_job(walletd_un, walletd_pw, job_name, endpoint, walletd_hosts) + "\n"

with open('prometheus.walletd.yml', 'w') as file:
    file.write(config_header + jobs)

## HOSTD
jobs = ""
for endpoint in hostd_endpoints:
    job_name = "hostd_" + "_".join(endpoint.split("/")[2:])
    jobs = jobs + get_prometheus_job(hostd_un, hostd_pw, job_name, endpoint, hostd_hosts) + "\n"

with open('prometheus.hostd.yml', 'w') as file:
    file.write(config_header + jobs)