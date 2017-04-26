**This is a Zabbix template + discovery & sender script useful to monitor Varnish High Availability (VHA) Agent instances:**

1. Copy ``zabbix-vha-agent.py`` to ``/usr/local/bin/``.

2. Grant sudo permissions to the ``zabbix`` user to execute the ``/usr/local/bin/zabbix-vha-agent.py`` script. This is required to access contents of VHA Agent status files.

3. Add the ``vha_agent.discovery`` user parameter to Zabbix::

    UserParameter=vha_agent.discovery[*],sudo /usr/local/bin/zabbix-vha-agent.py -i '$1' discover $2

4. Add a new job to the ``zabbix`` user crontab (beware of the ``-i`` and ``-s`` options). This will submit VHA Agent metrics through Zabbix Sender::

    * * * * * sudo /usr/local/bin/zabbix-vha-agent.py send -c /etc/zabbix/zabbix_agentd.conf -s dev > /dev/null 2>&1

5. Import the VHA Agent template (``template-app-vha-agent.xml`` file).

6. Add an existing / new host to the ``Varnish Cache servers`` group and link it to the ``Template App VHA Agent`` template. Beware you must set a value for the ``{$VHA_AGENT_LOCATIONS}`` macro (comma-delimited list of VHA Agent status files). Usually you should leave its value blank when running a single VHA Agent instance per server (i.e. the default location will be used: ``/var/lib/vha-agent/vha-status``).

7. Enable triggers and trigger prototypes according with your preferences.
