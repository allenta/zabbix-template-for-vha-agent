#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
:url: https://github.com/allenta/zabbix-template-for-vha-agent
:copyright: (c) 2016-2020 by Allenta Consulting S.L. <info@allenta.com>.
:license: BSD, see LICENSE.txt for more details.
'''

from __future__ import absolute_import, division, print_function, unicode_literals
import json
import re
import subprocess
import sys
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
## 'stats' COMMAND
###############################################################################

def stats(options):
    # Initializations.
    result = {}

    # Build master item contents.
    for instance in options.vha_agent_instances.split(','):
        instance = instance.strip()
        items = _stats(instance, options.default_vha_agent_status_file)
        for name, value in items.items():
            result['%(instance)s.%(name)s' % {
                'instance': _safe_zabbix_string(instance),
                'name': _safe_zabbix_string(name),
            }] = value

    # Render output.
    sys.stdout.write(json.dumps(result, separators=(',', ':')))


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
                '{#LOCATION_ID}': _safe_zabbix_string(instance),
            })
        else:
            items = _stats(instance, options.default_vha_agent_status_file)
            ids = set()
            for name in items.keys():
                match = SUBJECTS[options.subject].match(name)
                if match is not None and match.group(1) not in ids:
                    discovery['data'].append({
                        '{#LOCATION}': instance,
                        '{#LOCATION_ID}': _safe_zabbix_string(instance),
                        '{#SUBJECT}': match.group(1),
                        '{#SUBJECT_ID}': _safe_zabbix_string(match.group(1)),
                    })
                    ids.add(match.group(1))

    # Render output.
    sys.stdout.write(json.dumps(discovery, sort_keys=True, indent=2))


###############################################################################
## HELPERS
###############################################################################

def _stats(location, default_vha_agent_status_file):
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


def _safe_zabbix_string(value):
    # Return a modified version of 'value' safe to be used as part of:
    #   - A quoted key parameter (see https://www.zabbix.com/documentation/4.0/manual/config/items/item/key).
    #   - A JSON string.
    return value.replace('"', '\\"')


def _execute(command, stdin=None):
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

    # Set up 'stats' command.
    subparser = subparsers.add_parser(
        'stats',
        help='collect VHA Agent stats')

    # Set up 'discover' command.
    subparser = subparsers.add_parser(
        'discover',
        help='generate Zabbix discovery schema')
    subparser.add_argument(
        'subject', type=str, choices=SUBJECTS.keys(),
        help="dynamic resources to be discovered")

    # Parse command line arguments.
    options = parser.parse_args()

    # Execute command.
    globals()[options.command](options)
    sys.exit(0)

if __name__ == '__main__':
    main()
