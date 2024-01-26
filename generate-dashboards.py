import requests, json, re, sys

with open("siagrafana.json", 'r') as json_file:
    siahosts = json.load(json_file)

grafanaBaseUrl = siahosts['grafana_host']
headers = {"Content-Type": "application/json", "Accept": "application/json", "Authorization": "Bearer " + siahosts['grafana_api_key']}


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
        if d["name"] in ['hostd','renterd','walletd','sia']
    }
    if 'sia' in datasources:
        return {'sia': datasources['sia']}
    else:
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
    substring_to_replace = "<DSID>"
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

def grafanaCreateSiaDashboard(datasources, siaservice, dashboard_meta = None):
    ds = ""
    if 'sia' in datasources:
        ds = datasources['sia']
    else:
        ds = datasources[siaservice]
    dashboard = generateSiaDashboard(siaservice, ds, dashboard_meta)
    return grafanaManageDashboard(dashboard)

def getSiaDashboardIDs(dashboards):
    siadashboards = {'hostd':None,'renterd':None,'walletd':None}
    for key in dashboards.keys():
        if key in services:
            siadashboards[key] = dashboards[key]
    return siadashboards

services = ['hostd', 'renterd', 'walletd']
datasources = grafanaGetSiaDataSources()
highest_id, dashboards = grafanaGetDashboards()
siadashboards = getSiaDashboardIDs(dashboards)

for service in services:
    grafanaCreateSiaDashboard(datasources, service, siadashboards[service])
