#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
:url: https://github.com/allenta/zabbix-template-for-vha-agent
:copyright: (c) 2016-2021 by Allenta Consulting S.L. <info@allenta.com>.
:license: BSD, see LICENSE.txt for more details.
'''

from __future__ import absolute_import, division, print_function, unicode_literals
import json
import re
import subprocess
import sys
from argparse import ArgumentParser

TYPE_COUNTER = 1
TYPE_GAUGE = 2
TYPE_OTHER = 3
TYPES = (TYPE_COUNTER, TYPE_GAUGE, TYPE_OTHER)

ITEMS = (
    (r'uptime', TYPE_GAUGE),
    (r'n_trans', TYPE_COUNTER),
    (r'n_insert', TYPE_COUNTER),
    (r'n_dropped', TYPE_COUNTER),
    (r'n_req_total', TYPE_COUNTER),
    (r'n_req_failed', TYPE_COUNTER),
    (r'n_backlog', TYPE_GAUGE),
    (r'n_backlog_(?:.+)', TYPE_GAUGE),
)

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
        stats = _stats(instance, options.default_vha_agent_status_file)
        for item in stats.items:
            result['%(instance)s.%(name)s' % {
                'instance': _safe_zabbix_string(instance),
                'name': _safe_zabbix_string(item.name),
            }] = item.value

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
            stats = _stats(instance, options.backends_re)
            for subject in stats.subjects(options.subject):
                discovery['data'].append({
                    '{#LOCATION}': instance,
                    '{#LOCATION_ID}': _safe_zabbix_string(instance),
                    '{#SUBJECT}': subject,
                    '{#SUBJECT_ID}': _safe_zabbix_string(subject),
                })

    # Render output.
    sys.stdout.write(json.dumps(discovery, sort_keys=True, indent=2))


###############################################################################
## HELPERS
###############################################################################

class Item(object):
    '''
    A class to hold all relevant information about an item in the stats: name,
    value, type and subject (type & value).
    '''

    def __init__(
            self, name, value, type, subject_type=None, subject_value=None):
        # Set name and value.
        self._name = name
        self._value = value
        self._type = type
        self._subject_type = subject_type or 'items'
        self._subject_value = subject_value

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value

    @property
    def type(self):
        return self._type

    @property
    def subject_type(self):
        return self._subject_type

    @property
    def subject_value(self):
        return self._subject_value

    def aggregate(self, value):
        # Aggregate another value. Only counter and gauges can be aggregated.
        # In any other case, mark this item's value as discarded.
        if self.type in (TYPE_COUNTER, TYPE_GAUGE):
            self._value += value
        else:
            self._value = None


class Stats(object):
    '''
    A class to hold results for a call to _stats: keeps all processed items and
    all subjects seen per subject type and provides helper methods to build and
    process those items.
    '''

    def __init__(self, items_definitions, subjects_patterns, log_handler=None):
        # Build items regular expression that will be used to match item names
        # and discover item types.
        items_re = dict((type, []) for type in TYPES)
        for item_re, item_type in items_definitions:
            items_re[item_type].append(item_re)
        self._items_patterns = dict(
            (type, re.compile(r'^(?:' + '|'.join(res) + r')$'))
            for type, res in items_re.items())

        # Set subject patterns that will be used to assign subject type and
        # subject values to items.
        self._subjects_patterns = subjects_patterns

        # Other initializations.
        self._log_handler = log_handler or sys.stderr.write
        self._items = {}
        self._subjects = {}

    @property
    def items(self):
        # Return all items that haven't had their value discarded because an
        # invalid aggregation.
        return (item for item in self._items.values() if item.value is not None)

    def add(self, name, value, type=None, subject_type=None,
            subject_value=None):
        # Add a new item to the internal state or simply aggregate it's value
        # if an item with the same name has already been added.
        if name in self._items:
            self._items[name].aggregate(value)
        else:
            # Build item.
            item = self._build_item(
                name, value, type, subject_type, subject_value)

            if item is not None:
                # Add new item to the internal state.
                self._items[item.name] = item

                # Also, register this item's subject in the corresponding set.
                if item.subject_type != None and item.subject_value != None:
                    if item.subject_type not in self._subjects:
                        self._subjects[item.subject_type] = set()
                    self._subjects[item.subject_type].add(item.subject_value)

    def get(self, name, default=None):
        # Return current value for a particular item or the given default value
        # if that item is not available or has had it's value discarded.
        if name in self._items and self._items[name].value is not None:
            return self._items[name].value
        else:
            return default

    def subjects(self, subject_type):
        # Return the set of registered subjects for a given subject type.
        return self._subjects.get(subject_type, set())

    def log(self, message):
        self._log_handler(message)

    def _build_item(
            self, name, value, type=None, subject_type=None,
            subject_value=None):
        # Initialize type if none was provided.
        if type is None:
            type = next((
                type for type in TYPES
                if self._items_patterns[type].match(name) is not None), None)

        # Filter invalid items.
        if type not in TYPES:
            return None

        # Initialize subject_type and subject_value if none were provided.
        if subject_type is None and subject_value is None:
            for subject, subject_re in self._subjects_patterns.items():
                if subject_re is not None:
                    match = subject_re.match(name)
                    if match is not None:
                        subject_type = subject
                        subject_value = match.group(1)
                        break

        # Return item instance.
        return Item(
            name=name,
            value=value,
            type=type,
            subject_type=subject_type,
            subject_value=subject_value
        )


def _stats(location, default_vha_agent_status_file):
    # Initializations.
    stats = Stats(ITEMS, SUBJECTS)

    # Fetch stats from VHA agent status file.
    try:
        f = open(location or default_vha_agent_status_file, 'r')
    except IOError as e:
        stats.log(str(e))
    else:
        with f:
            for line in f:
                # Extract item name and item value.
                name, value = [v.strip() for v in line.split('=', 1)]

                # Add item to the result.
                stats.add(name, value)

    # Done!
    return stats


def _safe_zabbix_string(value):
    # Return a modified version of 'value' safe to be used as part of:
    #   - A quoted key parameter (see https://www.zabbix.com/documentation/5.0/manual/config/items/item/key).
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
