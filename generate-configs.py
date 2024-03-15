import requests, json, sys
from requests.auth import HTTPBasicAuth

try:
    print('reading siagrafana.json')
    with open("siagrafana.json", 'r') as json_file:
        siahosts = json.load(json_file)
except:
    print('unable to read siagrafana.json')
    sys.exit()

config_header = """# sia global config
global:
  scrape_interval: 15s # Set the scrape interval to every 15 seconds. Default is every 1 minute.
  evaluation_interval: 15s # Evaluate rules every 15 seconds. The default is every 1 minute.
  # scrape_timeout is set to the global default (10s).

scrape_configs:
"""

def get_prometheus_job(un, pw, job_name, metrics_path, hosts):
    retstr = """  - job_name: """ + job_name.split("?")[0] + """
    metrics_path: """ + metrics_path.split("?")[0] + """
    basic_auth:
      username: '""" + un + """'
      password: '""" + pw + """'"""
    if "?" in job_name:
        retstr = retstr + """
    params:
      """
        params = job_name.split("?")[1].split("&")
        # offset=0&limit=100
        for idx, param in enumerate(params):
            kv = param.split("=")
            retstr = retstr + kv[0] + ": [" + kv[1] + ("""]
      """, "]")[idx == len(params)-1]
    retstr = retstr + """
    static_configs:
      - targets:
"""
    for host in hosts:
        retstr = retstr + "        - " + host + "\n"
    return retstr

def get_wallets(un, pw, host):
    wallets = []
    url = "http://" + host + "/prometheus/wallets"
    r = requests.get(url, auth=HTTPBasicAuth(un, pw))
    for wallet in list(r.json().keys()):
        if wallet != "primary":
            wallets.append(wallet)
    return wallets

services = []

## WALLETD
walletd_jobs = ""
if "walletd_hosts" in siahosts:
    services.append("walletd")
    for host in siahosts["walletd_hosts"]:
        wallets = get_wallets("", siahosts["walletd_api_pwd"], host)
        for endpoint in siahosts["walletd_endpoints"]:
            if ":name" in endpoint:
                for wallet in wallets:
                    job_name = endpoint.replace(":name",wallet)
                    job_name = job_name.split("/")[2:]
                    job_name.insert(1,host.split(":")[0])
                    job_name.insert(2,host.split(":")[1])
                    job_name = "walletd_" + "_".join(job_name)
                    walletd_jobs = walletd_jobs + get_prometheus_job("", siahosts["walletd_api_pwd"], job_name, endpoint.replace(":name",wallet), [host]) + "\n"
    for endpoint in siahosts["walletd_endpoints"]:
        if ":name" not in endpoint:
            job_name = "walletd_" + "_".join(endpoint.split("/")[1:])
            walletd_jobs = walletd_jobs + get_prometheus_job("", siahosts["walletd_api_pwd"], job_name, endpoint, siahosts["walletd_hosts"]) + "\n"
    try:
        print('creating file prometheus.walletd.yml')
        with open('prometheus.walletd.yml', 'w') as file:
            file.write(config_header + walletd_jobs)
    except:
        print('error creating file prometheus.walletd.yml')

## HOSTD
hostd_jobs = ""
if "hostd_hosts" in siahosts:
    services.append("hostd")
    for endpoint in siahosts["hostd_endpoints"]:
        job_name = "hostd_" + "_".join(endpoint.split("/")[1:])
        hostd_jobs = hostd_jobs + get_prometheus_job("", siahosts["hostd_api_pwd"], job_name, endpoint, siahosts["hostd_hosts"]) + "\n"
    try:
        print('creating file prometheus.hostd.yml')
        with open('prometheus.hostd.yml', 'w') as file:
            file.write(config_header + hostd_jobs)
    except:
        print('error creating file prometheus.hostd.yml')

## RENTERD
renterd_jobs = ""
if "renterd_hosts" in siahosts:
    services.append("renterd")
    for endpoint in siahosts["renterd_endpoints"]:
        job_name = "renterd_" + "_".join(endpoint.split("/")[1:])
        renterd_jobs = renterd_jobs + get_prometheus_job("", siahosts["renterd_api_pwd"], job_name, endpoint, siahosts["renterd_hosts"]) + "\n"
    try:
        print('creating file prometheus.renterd.yml')
        with open('prometheus.renterd.yml', 'w') as file:
            file.write(config_header + renterd_jobs)
    except:
        print('error creating file prometheus.renterd.yml')

## ALL
sia_yml = config_header + hostd_jobs + renterd_jobs + walletd_jobs
try:
    print('creating combined file prometheus.yml (with ' + ", ".join(services) + ')')
    with open('prometheus.yml', 'w') as file:
        file.write(sia_yml)
except:
    print('error creating file prometheus.yml (with ' + ", ".join(services) + ')')