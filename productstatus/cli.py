"""
Command-line interface to the Productstatus server.
"""

import sys
import traceback
import json
import argparse

import productstatus.api
import productstatus.exceptions


class Client(object):
    def __init__(self):
        self.subparsers = {}

    def setup_basic_parser(self):
        self.parser = argparse.ArgumentParser(add_help=False)
        self.parser.add_argument('server', help='Productstatus server to communicate with')
        self.parser.add_argument('--help', required=False, action='store_true', help='Print help')
        self.parser.add_argument('--username', required=False, help='Productstatus user name')
        self.parser.add_argument('--api_key', required=False, help='Productstatus API key')

    def setup_preliminary_parser(self):
        self.setup_basic_parser()
        self.parser.add_argument('...', nargs=argparse.REMAINDER)

    def setup_sub_commands(self):
        self.setup_preliminary_parser()
        args = self.parser.parse_args()
        self.api = productstatus.api.Api(args.server, username=args.username, api_key=args.api_key)
        self.api._get_schema_from_server()
        self.main_schema = self.api._schema

        # Create a new parser with all sub-commands
        self.setup_basic_parser()
        self.subparser = self.parser.add_subparsers(dest='_subparser')
        for key in self.main_schema.keys():
            self.subparsers[key] = self.subparser.add_parser(
                key,
                add_help=False,
                help='Interact with the %s resource' % key,
                )

    def pprint_json_string(self, json_data):
        hash_ = json.loads(json_data)
        self.pprint(hash_)

    def pprint(self, hash_):
        print(json.dumps(hash_, sort_keys=True, indent=4, separators=(',', ': ')))

    def args_in_schema(self, args_dict):
        schema_keys = self.schema['fields'].keys()
        a = {}
        for key in args_dict:
            if args_dict[key] is None:
                continue
            # Remote queries may have modifier such as field__gte, whereas the
            # schema only contains the 'field' part.
            base_key = key.split('__')[0]
            if base_key in schema_keys:
                a[key] = args_dict[key]
        return a

    def exec_get(self, args_dict):
        resource = self.collection[args_dict['uuid']]
        serialized = resource._serialize()
        self.pprint_json_string(serialized)

    def exec_search(self, args_dict):
        args = self.args_in_schema(args_dict)
        qs = self.collection.objects
        qs.filter(**args)
        resources = [json.loads(x._serialize()) for x in qs]
        self.pprint(resources)

    def exec_create(self, args_dict):
        args = self.args_in_schema(args_dict)
        resource = self.collection.create()
        [setattr(resource, key, value) for key, value in args.items()]
        resource._unserialize()
        resource.save()
        serialized = resource._serialize()
        self.pprint_json_string(serialized)

    def setup_parameters(self, subcommand):
        self.setup_basic_parser()
        self.parser.add_argument(subcommand, help='The literal string "%s"' % subcommand)
        self.collection = getattr(self.api, subcommand)
        self.schema = self.collection.schema
        self.subparser = self.parser.add_subparsers(dest='action')
        self.subparsers = {}
        for action in ['search', 'create', 'get']:
            self.subparsers[action] = self.subparser.add_parser(action)
            self.subparsers[action].set_defaults(func=getattr(self, 'exec_%s' % action))
        for action in ['search', 'create']:
            for key, value in self.schema['fields'].items():
                self.subparsers[action].add_argument('--%s' % key, help=value['help_text'])
        for action in ['get']:
            self.subparsers[action].add_argument('uuid', help='The UUID of a %s object' % subcommand)

    def _exec(self, args, args_dict):
        """
        Execute command set by func attribute.
        Catch exceptions, print traceback and exit program with proper exit_code.
        """
        try:
            args.func(args_dict)
        except productstatus.exceptions.UnauthorizedException:
            self._exit(2)
        except productstatus.exceptions.NotFoundException:
            self._exit(3)
        except productstatus.exceptions.ServiceUnavailableException:
            self._exit(4)
        except productstatus.exceptions.ProductstatusException:
            self._exit(255)
        except:
            self._exit(1)

    def _exit(self, exit_code):
        traceback.print_exc()
        sys.exit(exit_code)

    def main(self):
        self.setup_sub_commands()
        args, unknown = self.parser.parse_known_args()
        self.setup_parameters(args._subparser)
        args, unknown = self.parser.parse_known_args()
        args_dict = vars(args)
        # This very filthy filter ensures that remote filter extensions are
        # applied magically, at the cost of breaking local syntax checking.
        for i in xrange(0, len(unknown), 2):
            args_dict[unknown[i].strip('--')] = unknown[i+1]
        if args.help:
            self.parser.print_help()
            return

        self._exec(args, args_dict)

if __name__ == '__main__':
    client = Client()
    client.main()
