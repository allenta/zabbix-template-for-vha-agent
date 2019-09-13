**This is a Zabbix template + discovery & sender script useful to monitor Varnish High Availability (VHA) Agent instances:**

1. Copy ``zabbix-vha-agent.py`` to ``/usr/local/bin/``.

2. Grant sudo permissions to the ``zabbix`` user to execute the ``/usr/local/bin/zabbix-vha-agent.py`` script. This is required to access contents of VHA Agent status files.

3. Add the ``vha_agent.discovery`` and ``vha_agent.stats`` user parameters to Zabbix::

    UserParameter=vha_agent.discovery[*],sudo /usr/local/bin/zabbix-vha-agent.py -i '$1' --default-vha-agent-status-file '/var/lib/vha-agent/vha-status' discover $2
    UserParameter=vha_agent.stats[*],sudo /usr/local/bin/zabbix-vha-agent.py -i '$1' --default-vha-agent-status-file '/var/lib/vha-agent/vha-status' stats

4. Import the VHA Agent template (``template-app-vha-agent.xml`` file).

5. Add an existing / new host to the ``Varnish Cache servers`` group and link it to the ``Template App VHA Agent`` template. Beware you must set a value for the ``{$VHA_AGENT.LOCATIONS}`` macro (comma-delimited list of VHA Agent status files). Usually you should leave its value blank when running a single VHA Agent instance per server. The following macros are available on both templates:

   * ``{$VHA_AGENT.ITEM_HISTORY_STORAGE_PERIOD}``
   * ``{$VHA_AGENT.ITEM_TREND_STORAGE_PERIOD}``
   * ``{$VHA_AGENT.ITEM_UPDATE_INTERVAL}``
   * ``{$VHA_AGENT.LAST_VALUES_TO_CHECK}``
   * ``{$VHA_AGENT.LLD_KEEP_LOST_RESOURCES_PERIOD}``
   * ``{$VHA_AGENT.LLD_UPDATE_INTERVAL}``
   * ``{$VHA_AGENT.LOCATIONS}``
   * ``{$VHA_AGENT.N_DROPPED.MAX}``
   * ``{$VHA_AGENT.N_REQ_FAILED.MAX}``
   * ``{$VHA_AGENT.PROCESSES.MIN}``
   * ``{$VHA_AGENT.UPTIME.MIN}``

   It's also possible to use **contexts** on macros, for example:

   * ``{$VHA_AGENT.LLD_UPDATE_INTERVAL:backlogs}``
   * ``{$VHA_AGENT.ITEM_HISTORY_STORAGE_PERIOD:items:n_req_total}``

6. Enable triggers and trigger prototypes according with your preferences.
