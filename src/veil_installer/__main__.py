from __future__ import unicode_literals, print_function, division
import veil_component

if '__main__' == __name__:
    import sys
    import argparse
    import pprint
    from .installer import install_resources
    from .installer import set_upgrading
    from .installer import set_downloading_while_dry_run
    from .installer import dry_run
    from .installer import get_dry_run_result
    from .component_installer import parse_resource

    argument_parser = argparse.ArgumentParser('Install resource')
    argument_parser.add_argument('resource', type=str, help='<installer_name>?<installer_arg1>&<installer_arg2>...')
    argument_parser.add_argument('--upgrade', help='check latest version and upgrade if found new version', action='store_true')
    argument_parser.add_argument('--dry-run', help='list the resources required and installed or not', action='store_true')
    argument_parser.add_argument('--download-only', help='download necessary files, but do not install them, and it implies dry-run',
        action='store_true')
    args = argument_parser.parse_args(sys.argv[1:])

    if veil_component.VEIL_ENV_TYPE in ('development', 'test'):
        veil_component.start_recording_dynamic_dependencies()

    resource = parse_resource(args.resource)
    if args.upgrade:
        set_upgrading(True)
    if args.download_only:
        set_downloading_while_dry_run(True)
        with dry_run():
            install_resources([resource])
    elif args.dry_run:
        with dry_run():
            install_resources([resource])
            pprint.pprint(get_dry_run_result())
    else:
        install_resources([resource])
