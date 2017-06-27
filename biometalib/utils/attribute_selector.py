#!/usr/bin/env python
import os
import sys
import readline
from textwrap import dedent
import argparse
from argparse import RawDescriptionHelpFormatter as Raw
from logging import INFO, DEBUG
from collections import defaultdict, OrderedDict

from ruamel import yaml

from pymongo import MongoClient
from fuzzywuzzy import process

from biometalib.logger import logger

_DEBUG = False

def arguments():
    """Pulls in command line arguments."""

    DESCRIPTION = """\
    """

    parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=Raw)

    db_args = parser.add_argument_group('Database Arguments')
    config = parser.add_argument_group('Inputs')

    db_args.add_argument("--host", dest="host", action='store', default='localhost', required=False,
                         help="Host running a mongo database. [default: localhost]")

    db_args.add_argument("--port", dest="port", action='store', type=int, required=False, default=27017,
                         help="Mongo database port. [default: 27017]")

    db_args.add_argument("--db", dest="db", action='store', required=True,
                        help="Name of the mongo database containing the biometa collection.")

    db_args.add_argument("--username", dest="username", action='store', required=False,
                        help="MongoDB username to connect with.")

    db_args.add_argument("--password", dest="password", action='store', required=False,
                        help="MongoDB password.")

    db_args.add_argument("--authenticationDatabase", dest="authDB", action='store', required=False,
                        help="MongoDB database to authenticate against.")

    config.add_argument("--config", dest="config", action='store', required=True,
                        help="YAML file to store attribute decisions")

    parser.add_argument("--debug", dest="debug", action='store_true', required=False,
                        help="Turn on debug output.")

    args = parser.parse_args()

    # Set logging level
    if args.debug:
        logger.setLevel(DEBUG)
        global _DEBUG
        _DEBUG = True
    else:
        logger.setLevel(INFO)

    return args


class BioAttribute(object):
    def __init__(self, fn):
        """Column attributes.

        Uses YAMLs to store column attributes.

        Parameters:
        -----------
        fn: str
            A YAML file.

        Methods:
        --------
        write_attributes: method
            Writes out saved attributes to YAML

        """
        self.fn = fn
        self._storage = self._load_attributes()
        self._reverse = self._make_reverse()
        self.current_attrs = [x for x in self._storage.keys() if x != 'ignore']

    def _load_attributes(self):
        """Load YAML if it exists.

        Checks if the YAML config file exits, if it does returns a dictionary
        version of the YAML.
        """
        if os.path.exists(self.fn):
            with open(self.fn, 'r') as fh:
                return yaml.load(fh, Loader=yaml.RoundTripLoader)
        else:
            return {}

    def write_attributes(self):
        """Writes current attribute.

        Writes the current attributes to YAML.
        """
        updated = OrderedDict()
        for k, v in self._reverse.items():
            try:
                updated[v].append(k)
            except:
                updated[v] = [k, ]

        updated = yaml.comments.CommentedMap(updated)
        with open(self.fn, 'w') as fh:
            yaml.dump(updated, fh, default_flow_style=False, block_seq_indent=2, Dumper=yaml.RoundTripDumper)

    def _make_reverse(self):
        """Create a reverse mapping dictionary.

        Map attribute as the key to the preferred attribute as the value.
        """
        reverse = OrderedDict()
        for k, v in self._storage.items():
            reverse[k] = k
            for i in v:
                reverse[i] = k
        return reverse

    def __getitem__(self, key):
        return self._reverse[key]

    def __setitem__(self, key, value):
        self._reverse[key] = value

    def __delitem__(self, key):
        del(self._reverse[key])

    def __iter__(self):
        return iter(self._reverse)

    def keys(self):
        return self._reverse.keys()

    def values(self):
        return self._reverse.values()

    def items(self):
        return self._reverse.items()


def connect_mongo(host, port, db, u, p, auth_db):
    client = MongoClient(host=host, port=port)
    if (u is not None) & (p is not None) & (auth_db is not None):
        client[auth_db].authenticate(u, p)
    db = client[db]
    return db['biometa']


def get_list_sample_attrs(biometa):
    cursor = biometa.aggregate([
        {'$unwind': '$sample_attributes'},
        {
            '$project': {'_id': '$sample_attributes.name'}
        }
    ])
    return set([x['_id'] for x in cursor])


def autocomplete(text, state):
    """This adds tab completion to the command line."""
    for cmd in bioAttr.current_attrs:
        if cmd.startswith(text):
            if not state:
                return cmd
            else:
                state -= 1


class bcolors:
    """This is a quick color hack to display terminal colors."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def format_examples(examples):
    """Format examples as a table with 4 columns."""
    exp = ''
    for i, example in enumerate(examples):
        if i % 4 == 3:
            exp += '{0}{1:<60}{2}\n'.format(bcolors.GREEN, example, bcolors.ENDC)
        else:
            exp += '{0}{1:<60}{2}\t'.format(bcolors.GREEN, example, bcolors.ENDC)
    return exp


def get_examples(attr):
    """Get a list of values from the database."""
    # Count the number of samples with that attribute
    num_samples = len(list(biometa.aggregate([
        {'$unwind': '$sample_attributes'},
        {'$match': {'sample_attributes.name': attr}},
    ])))

    # Count the number of projects that used attribute
    num_projects = len(list(biometa.aggregate([
        {'$unwind': '$sample_attributes'},
        {'$match': {'sample_attributes.name': attr}},
        {'$group': {'_id': '$bioproject'}},
    ])))

    # Get a list of all values from the attribute
    values = biometa.aggregate([
        {'$unwind': '$sample_attributes'},
        {'$match': {'sample_attributes.name': attr}},
        {
            '$project': {'_id': '$sample_attributes.value'}
        }
    ])

    exp = format_examples(set([x['_id'] for x in values]))
    print(dedent( """
        There were {0}{2:,}{1} BioSamples and {0}{3:,}{1} BioProjects that had this attribute.
        Here are the values:\n\n{4}\n
        """.format(bcolors.YELLOW, bcolors.ENDC, num_samples, num_projects, exp)))


def format_similar(attrs):
    """Format similar attribute names.

    Attributes that are already in our selected list color in yellow.
    """
    atr = ''
    for i, attr in enumerate(attrs):
        if attr in bioAttr.current_attrs:
            color = bcolors.YELLOW
        else:
            color = bcolors.GREEN

        if i % 4 == 3:
            atr += '{0}{1:<60}{2}\n'.format(color, attr, bcolors.ENDC)
        else:
            atr += '{0}{1:<60}{2}\t'.format(color, attr, bcolors.ENDC)

    return atr


def get_similar(attr):
    """Print a list of similar attributes based on fuzzy string matching."""
    choices = list(set(sample_attrs).union(set(bioAttr.current_attrs)))
    similar = [x[0] for x in process.extract(attr, sample_attrs, limit=20)]
    similar_fmt = format_similar(similar)
    print("Current similar attributes you have already selected include:\n\n{0}".format(similar_fmt))


def get_user_input(attr):
    """Interact with the user."""
    print('Current Attribute: \t{0}{1:>30}{2}\n'.format(bcolors.RED, attr, bcolors.ENDC))

    ui = input(dedent("""
          Type "e" to get examples or "s" to get a list of similar attributes.
          Do you want to keep, rename, or ignore this attribute?
          [k/r/i/e/s]: """))

    if ui == 'k':   # Keep attribute
        bioAttr[attr] = attr
        bioAttr.current_attrs.append(attr)
        os.system('clear')
    elif ui == 'i':     # Ignore attribute
        bioAttr[attr] = 'ignore'
        os.system('clear')
    elif ui == 'r':     # Rename attribute
        newName = input('Type in new name: ')
        bioAttr[attr] = newName
        bioAttr.current_attrs.append(newName)
        os.system('clear')
    elif ui == 'e':     # show example values
        get_examples(attr)
        get_user_input(attr)
    elif ui == 's':     # show similar attributes
        get_similar(attr)
        get_user_input(attr)
    elif ui == 'n':      # skip
        os.system('clear')
        pass
    elif ui == 'quit':      # Exit program
        return False
    else:       # Something else
        print('\nType "n" if you really want to skip or "quit" to exit, otherwise select a valid option.')
        get_user_input(attr)


def main():
    # Import commandline arguments.
    args = arguments()

    # Set up autocomplete for later
    readline.parse_and_bind("tab: complete")
    readline.set_completer(autocomplete)

    # Get current biological attributes
    global bioAttr
    bioAttr = BioAttribute(args.config)

    # connect to db
    global biometa
    biometa = connect_mongo(args.host, args.port, args.db, args.username, args.password, args.authDB)

    # Get list of column attributes
    global sample_attrs
    sample_attrs = get_list_sample_attrs(biometa)

    # Only look at attributes not already in our YAML
    filter_attrs = [x for x in sample_attrs if x not in bioAttr]

    # Iterate over novel attributes and figure out what to do with them
    os.system('clear')
    print(dedent("""
                 Welcome to the attribute selector. This is tool is intended in
                 helping come up with a list of sample attribute types. There
                 are {0}{1:,}{2} attributes that we are going to go through. If
                 at any point you want to stop just type "quit" and all of your
                 changes will be saved to your YAML.\n\n
                 """.format(bcolors.YELLOW, len(filter_attrs), bcolors.ENDC)))

    try:
        for attr in sorted(filter_attrs):
            if get_user_input(attr) is not None:
                break
    finally:
        # Write results
        bioAttr.write_attributes()


if __name__ == '__main__':
    main()
