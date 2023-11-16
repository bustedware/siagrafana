# Sia for Telegraf

1. Run the following command to generage a file named `sia-telegraf-http-inputs.conf`

```
python3 sia-to-telegraf-config.py
```

2. Plugin the result files contents into an existing telegraf.conf

3. Restart telegraf

### notes

types with `replaceme_` need to be ommited manually from the `sia-telegraf-http-inputs.conf` or that portion of code should filter out those endpoints.