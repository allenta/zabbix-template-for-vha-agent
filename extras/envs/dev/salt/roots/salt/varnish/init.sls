varnish.4.1-plus-repository:
  pkgrepo.managed:
    - humanname: Varnish 4.1 Plus
    - name: deb https://{{ pillar['varnish-plus']['user'] }}:{{ pillar['varnish-plus']['password'] }}@repo.varnish-software.com/ubuntu/ trusty varnish-4.1-plus
    - file: /etc/apt/sources.list.d/varnish.list
    - enabled: 1
    - key_url: https://{{ pillar['varnish-plus']['user'] }}:{{ pillar['varnish-plus']['password'] }}@repo.varnish-software.com/GPG-key.txt
    - require_in:
      - pkg: varnish.packages

varnish.4.1-plus-non-free-repository:
  pkgrepo.managed:
    - humanname: Varnish 4.1 Plus VAC
    - name: deb https://{{ pillar['varnish-plus']['user'] }}:{{ pillar['varnish-plus']['password'] }}@repo.varnish-software.com/ubuntu/ trusty non-free
    - file: /etc/apt/sources.list.d/varnish.list
    - enabled: 1
    - key_url: https://{{ pillar['varnish-plus']['user'] }}:{{ pillar['varnish-plus']['password'] }}@repo.varnish-software.com/GPG-key.txt
    - require_in:
      - pkg: varnish.packages

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
