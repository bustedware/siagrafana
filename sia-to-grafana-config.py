import requests, json, re, sys

with open("siagrafana.json", 'r') as json_file:
    siahosts = json.load(json_file)

grafanaBaseUrl = siahosts['grafana_host']
headers = {"Content-Type": "application/json", "Accept": "application/json", "Authorization": "Bearer " + siahosts['grafana_api_token']}


def grafanaGetAPIKeys():
    url = grafanaBaseUrl + "/api/auth/keys"
    r = requests.get(url, headers=headers)
    return r.json()

def grafanaGetDataSources():
    url = grafanaBaseUrl + "/api/datasources"
    r = requests.get(url, headers=headers)
    return r.json()

def grafanaGetDashboards():
    highest_id = 0
    url = grafanaBaseUrl + "/api/search?query="
    r = requests.get(url, headers=headers)
    dashboards = {
        d['title']:  {"id": d["id"], "uid": d["uid"]}
        for d in r.json()
    }
    for d in dashboards.keys():
        if dashboards[d]['id'] > highest_id:
            highest_id = dashboards[d]['id']
    return highest_id, dashboards

def grafanaGetSiaDataSources():
    datasources = grafanaGetDataSources()
    datasources = {
        d['name']:  d["uid"]
        for d in datasources
        if d["name"] in ['hostd','renterd','walletd']
    }
    return datasources

def grafanaManageDashboard(dashboard):
    payload = {
        "dashboard": dashboard,
        # "folderUid": None,
        "message": "created by sia automation",
        "overwrite": True
    }
    url = grafanaBaseUrl + "/api/dashboards/db"
    r = requests.post(url, headers=headers,data=json.dumps(payload))
    resp = r.json()
    if 'message' in resp:
        print(resp)
        return False
    else:
        if 'status' in resp:
            return resp['status'] == 'success'
        else:
            return False

def generateSiaDashboard(siaservice, dsid, dashboard_meta = None):
    with open('grafana.'+siaservice+'.template.json', 'r') as json_file:
        data = json_file.read()
    substring_to_replace = "<"+siaservice.upper()+"UID>"
    dashboard_json = json.loads(re.sub(substring_to_replace, dsid, str(data)))
    if dashboard_meta == None:
        dashboard_json['id'] = None
        dashboard_json['title'] = siaservice
    else:
        dashboard_json['id'] = dashboard_meta['id']
        dashboard_json['uid'] = dashboard_meta['uid']
    with open('grafana.'+siaservice+'.json', 'w') as json_file:
        json_file.write(json.dumps(dashboard_json,indent=4))
    return dashboard_json

def grafanaCreateSiaDashboard(siaservice, dashboard_meta = None):
    dashboard = generateSiaDashboard(siaservice, datasources[siaservice], dashboard_meta)
    return grafanaManageDashboard(dashboard)

# services = ['hostd','renterd','walletd']
services = ['hostd', 'walletd']
datasources = grafanaGetSiaDataSources()
highest_id, dashboards = grafanaGetDashboards()
siadashboards = {'hostd':None,'renterd':None,'walletd':None}
for key in dashboards.keys():
     if key in services:
        siadashboards[key] = dashboards[key]

for service in services:
    grafanaCreateSiaDashboard(service, siadashboards[service])
