General tips
============

- A Varnish Plus license is required to setup the development environment. The Vagrantfile of the project assumes the following environment variables are defined:
    - ``VARNISH_PLUS_USER``, including the username of your Varnish Plus license.
    - ``VARNISH_PLUS_PASSWORD``, including the password if your Varnish Plus license.

- Helper script: ``/vagrant/extras/envs/dev/start-services.sh``.

- Templates:
    1. ``http://192.168.100.174/zabbix``
        - Default username/password is ``admin``/``zabbix``.

    2. In 'Configuration > Templates' click on 'Import' and select ``template-app-vha-agent.xml``.

    3. In 'Configuration > Hosts' click on 'Create host':
        - Host name: ``dev``
        - Group: ``Varnish Cache servers``
        - Linked templates: ``Template App VHA Agent``
