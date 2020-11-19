**This is a Zabbix template + script useful to monitor Varnish High Availability (VHA) Agent instances:**

1. Copy ``zabbix-vha-agent.py`` to ``/usr/local/bin/``.

2. Add the ``vha_agent.discovery`` and ``vha_agent.stats`` user parameters to Zabbix::

    UserParameter=vha_agent.discovery[*],sudo /usr/local/bin/zabbix-vha-agent.py -i '$1' --default-vha-agent-status-file '/var/lib/vha-agent/vha-status' discover $2
    UserParameter=vha_agent.stats[*],sudo /usr/local/bin/zabbix-vha-agent.py -i '$1' --default-vha-agent-status-file '/var/lib/vha-agent/vha-status' stats

   You'll have to grant ``zabbix`` user sudo permissions to execute the ``/usr/local/bin/zabbix-vha-agent.py`` script. This is required to access contents of VHA Agent status files.

3. Import the template. You may download the appropriate version from `the releases page <https://github.com/allenta/zabbix-template-for-vha-agent/releases/latest/>`_ or generate it using the Jinja2 skeleton::

    $ pip install jinja2-cli
    $ jinja2 \
        -D version={4.0,4.2,4.4,5.0,5.2} \
        [-D name='VHA Agent'] \
        [-D description=''] \
        --strict -o template.xml template-app-vha-agent.j2

4. Link hosts to the template. Beware you must set a value for the ``{$VHA_AGENT.LOCATIONS}`` macro (comma-delimited list of VHA Agent status files). Usually you should leave its value blank when running a single VHA Agent instance per server. Additional macros and contexts are available for further customizations.
