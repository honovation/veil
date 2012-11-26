from __future__ import unicode_literals, print_function, division

if '__main__' == __name__:
    import sys
    import argparse
    import pprint
    from .installer import install_resources
    from .component_installer import parse_resource

    argument_parser = argparse.ArgumentParser('Install resource')
    argument_parser.add_argument('resource', type=str, help='<installer_name>?<installer_arg1>&<installer_arg2>...')
    argument_parser.add_argument('--dry-run', help='list the resources required and installed or not', action='store_true')
    argument_parser.add_argument('--installer-provider', help='for non-builtin resource')
    args = argument_parser.parse_args(sys.argv[1:])

    resource = parse_resource(args.resource)
    installer_providers = [args.installer_provider] if args.installer_provider else []
    if args.dry_run:
        dry_run_result = {}
        install_resources(dry_run_result, installer_providers, [resource])
        pprint.pprint(dry_run_result)
    else:
        install_resources(None, installer_providers, [resource])

