#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
:url: https://github.com/allenta/zabbix-template-for-vha-agent
:copyright: (c) 2016-2019 by Allenta Consulting S.L. <info@allenta.com>.
:license: BSD, see LICENSE.txt for more details.
'''

from __future__ import absolute_import, division, print_function, unicode_literals
import json
import re
import subprocess
import sys
import time
from argparse import ArgumentParser


ITEMS = re.compile(
    r'^(?:'
    r'uptime|'
    r'n_trans|'
    r'n_insert|'
    r'n_dropped|'
    r'n_req_total|'
    r'n_req_failed|'
    r'n_backlog|'
    r'n_backlog_(?:.+)'
    r')$')


SUBJECTS = {
    'items': None,
    'backlogs': re.compile(r'^n_backlog_(.+)$'),
}


###############################################################################
## 'send' COMMAND
###############################################################################

def send(options):
    # Initializations.
    rows = ''
    now = int(time.time())

    # Build Zabbix sender input.
    for instance in options.vha_agent_instances.split(','):
        instance = instance.strip()
        items = stats(instance, options.default_vha_agent_status_file)
        for name, value in items.items():
            row = '- vha_agent.stat["%(instance)s","%(key)s"] %(tst)d %(value)s\n' % {
                'instance': str2key(instance),
                'key': str2key(name),
                'tst': now,
                'value': value,
            }
            sys.stdout.write(row)
            rows += row

    # Submit metrics.
    rc, output = execute('zabbix_sender -T -r -i - %(config)s %(server)s %(port)s %(host)s' % {
        'config':
            '-c "%s"' % options.zabbix_config
            if options.zabbix_config is not None else '',
        'server':
            '-z "%s"' % options.zabbix_server
            if options.zabbix_server is not None else '',
        'port':
            '-p %d' % options.zabbix_port
            if options.zabbix_port is not None else '',
        'host':
            '-s "%s"' % options.zabbix_host
            if options.zabbix_host is not None else '',
    }, stdin=rows)

    # Check return code.
    if rc == 0:
        sys.stdout.write(output)
    else:
        sys.stderr.write(output)
        sys.exit(1)


###############################################################################
## 'discover' COMMAND
###############################################################################

def discover(options):
    # Initializations.
    discovery = {
        'data': [],
    }

    # Build Zabbix discovery input.
    for instance in options.vha_agent_instances.split(','):
        instance = instance.strip()
        if options.subject == 'items':
            discovery['data'].append({
                '{#LOCATION}': instance,
                '{#LOCATION_ID}': str2key(instance),
            })
        else:
            items = stats(instance, options.default_vha_agent_status_file)
            ids = set()
            for name in items.keys():
                match = SUBJECTS[options.subject].match(name)
                if match is not None and match.group(1) not in ids:
                    discovery['data'].append({
                        '{#LOCATION}': instance,
                        '{#LOCATION_ID}': str2key(instance),
                        '{#SUBJECT}': match.group(1),
                        '{#SUBJECT_ID}': str2key(match.group(1)),
                    })
                    ids.add(match.group(1))

    # Render output.
    sys.stdout.write(json.dumps(discovery, sort_keys=True, indent=2))


###############################################################################
## HELPERS
###############################################################################

def stats(location, default_vha_agent_status_file):
    result = {}
    try:
        with open(location or default_vha_agent_status_file, 'r') as file:
            for line in file:
                key, value = line.split('=', 1)
                if ITEMS.match(key.strip()) is not None:
                    result[key.strip()] = value.strip()
    except IOError as e:
        sys.stderr.write(str(e))
    return result


def str2key(name):
    result = name
    for char in ['(', ')', ',']:
        result = result.replace(char, '\\' + char)
    return result


def execute(command, stdin=None):
    child = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    output = child.communicate(
        input=stdin.encode('utf-8') if stdin is not None else None)[0].decode('utf-8')
    return child.returncode, output


###############################################################################
## MAIN
###############################################################################

def main():
    # Set up the base command line parser.
    parser = ArgumentParser()
    parser.add_argument(
        '-i', '--vha-agent-instances', dest='vha_agent_instances',
        type=str, required=False, default='',
        help='comma-delimited list of VHA Agent status files to get stats from')
    parser.add_argument(
        '--default-vha-agent-status-file', dest='default_vha_agent_status_file',
        type=str, required=False, default='/var/lib/vha-agent/vha-status',
        help='default VHA Agent status file')
    subparsers = parser.add_subparsers(dest='command')

    # Set up 'send' command.
    subparser = subparsers.add_parser(
        'send',
        help='submit varnishstat output through Zabbix sender')
    subparser.add_argument(
        '-c', '--zabbix-config', dest='zabbix_config',
        type=str, required=False, default=None,
        help='the Zabbix agent configuration file to fetch the configuration '
             'from')
    subparser.add_argument(
        '-z', '--zabbix-server', dest='zabbix_server',
        type=str, required=False, default=None,
        help='hostname or IP address of the Zabbix server / Zabbix proxy')
    subparser.add_argument(
        '-p', '--zabbix-port', dest='zabbix_port',
        type=int, required=False, default=None,
        help='port number of server trapper running on the Zabbix server / '
             'Zabbix proxy')
    subparser.add_argument(
        '-s', '--zabbix-host', dest='zabbix_host',
        type=str, required=False, default=None,
        help='host name as registered in the Zabbix frontend')

    # Set up 'discover' command.
    subparser = subparsers.add_parser(
        'discover',
        help='generate Zabbix discovery schema')
    subparser.add_argument(
        'subject', type=str, choices=SUBJECTS.keys(),
        help="dynamic resources to be discovered")

    # Parse command line arguments.
    options = parser.parse_args()

    # Check required arguments.
    if options.command == 'send':
        if options.zabbix_config is None and options.zabbix_server is None:
            parser.print_help()
            sys.exit(1)

    # Execute command.
    globals()[options.command](options)
    sys.exit(0)

if __name__ == '__main__':
    main()
