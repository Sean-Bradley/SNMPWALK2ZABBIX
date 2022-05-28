# SNMPWALK2ZABBIX

Create a Zabbix template from an SNMPWALK response.

Note that this will not create a fully featured all bells and whistles perfect template exactly for your needs. You will need to edit the result to make it exactly whatever you want it to be.

Remember, you got it for free, and it comes with no support or warranty. Read the [license](LICENSE).

Download

```bash
wget https://raw.githubusercontent.com/Sean-Bradley/SNMPWALK2ZABBIX/master/snmpwalk2zabbix.py
```

Example usage

```bash
python3 snmpwalk2zabbix.py public 192.168.1.1 1.3.6.1.2.1
```
