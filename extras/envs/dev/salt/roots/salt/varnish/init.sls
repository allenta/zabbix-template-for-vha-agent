varnish.6.0-plus-key:
  cmd.run:
    - runas: root
    - name: |
        set -e
        curl -L https://{{ pillar['varnish-plus']['user'] }}:{{ pillar['varnish-plus']['password'] }}@packagecloud.io/varnishplus/60/gpgkey | apt-key add -
    - require:
      - sls: global

varnish.6.0-plus-repository:
  pkgrepo.managed:
    - humanname: Varnish 6.0 Plus
    - name: deb https://{{ pillar['varnish-plus']['user'] }}:{{ pillar['varnish-plus']['password'] }}@packagecloud.io/varnishplus/60/ubuntu/ xenial main
    #- key_url: https://{{ pillar['varnish-plus']['user'] }}:{{ pillar['varnish-plus']['password'] }}@packagecloud.io/varnishplus/60/gpgkey
    - file: /etc/apt/sources.list.d/varnish.list
    - require_in:
      - pkg: varnish.packages
    - require:
      - cmd: varnish.6.0-plus-key

varnish.packages:
  pkg.installed:
    - refresh: True
    - pkgs:
      - varnish-plus
      - varnish-plus-ha

{% for name in ['varnish', 'varnish-plus-ha'] %}
varnish.disable-{{ name }}:
  service.dead:
    - name: {{ name }}
    - enable: False
  require:
    - pkg: varnish.packages
{% endfor %}
