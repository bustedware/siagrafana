# Grafana

1. Run prometheus with the example `prometheus.hostd.yml` or `prometheus.walletd.yml`
    - you can also generate these files running `python3 sia-to-prometheus-config.py`
2. In Grafana, add new prometheus data source pointed to your hostd metrics collector `http://prometheushost:9090` 
3. Create a new dashboard and copy `hostd-grafana.json` contents into the JSON model under the dashboard settings

*note: prometheus endpoints are available in a fork of hostd here: https://github.com/bustedware/hostd
PR submitted here: https://github.com/SiaFoundation/hostd/pull/213 to add to master hostd. Potentially
could run out of an exporter instead of adding new API endpoints

The dashboard pretty well mirrors the existing UI for hostd.

![alt text](dashboard.png)

# Sia for Telegraf

1. Run the following command to generage a file named `sia-telegraf-http-inputs.conf` and `sia-api-responses.json`

```
python3 sia-to-telegraf-config.py <hostd_api_password>
```

2. Plugin the contents of `sia-telegraf-http-inputs.conf` into an existing telegraf.conf

3. Restart telegraf

### notes

types with `replaceme_` need to be ommited manually from the `sia-telegraf-http-inputs.conf` or that portion of code should filter out those endpoints.
