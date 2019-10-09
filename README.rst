**This is a Zabbix template + script useful to monitor Varnish High Availability (VHA) Agent instances:**

1. Copy ``zabbix-vha-agent.py`` to ``/usr/local/bin/``.

2. Grant sudo permissions to the ``zabbix`` user to execute the ``/usr/local/bin/zabbix-vha-agent.py`` script. This is required to access contents of VHA Agent status files.

3. Add the ``vha_agent.discovery`` and ``vha_agent.stats`` user parameters to Zabbix::

    UserParameter=vha_agent.discovery[*],sudo /usr/local/bin/zabbix-vha-agent.py -i '$1' --default-vha-agent-status-file '/var/lib/vha-agent/vha-status' discover $2
    UserParameter=vha_agent.stats[*],sudo /usr/local/bin/zabbix-vha-agent.py -i '$1' --default-vha-agent-status-file '/var/lib/vha-agent/vha-status' stats

4. Generate the VHA Agent template template using the Jinja2 skeleton and import it::

    $ pip install jinja2-cli
    $ jinja2 \
        -D version={4.0,4.2,4.4} \
        [-D name='VHA Agent'] \
        --strict -o template.xml template-app-vha-agent.j2

5. Link hosts to the template. Beware you must set a value for the ``{$VHA_AGENT.LOCATIONS}`` macro (comma-delimited list of VHA Agent status files). Usually you should leave its value blank when running a single VHA Agent instance per server. Additional macros and contexts are available for further customizations.
