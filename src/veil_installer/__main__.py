from __future__ import unicode_literals, print_function, division

if '__main__' == __name__:
    import sys
    import argparse
    import pprint
    from .installer import install_resources
    from .installer import set_upgrade_mode
    from .installer import set_download_while_dry_run
    from .installer import dry_run
    from .installer import get_dry_run_result
    from .installer import UPGRADE_MODE_FAST
    from .installer import UPGRADE_MODE_LATEST
    from .installer import UPGRADE_MODE_NO
    from .component_installer import parse_resource

    argument_parser = argparse.ArgumentParser('Install resource')
    argument_parser.add_argument('resource', type=str, help='<installer_name>?<installer_arg1>&<installer_arg2>...')
    argument_parser.add_argument('--dry-run', help='list the resources required and installed or not',
        action='store_true')
    argument_parser.add_argument('--upgrade-mode',
        help='no will keep current version, latest will check remote and upgrade from remote, '
             'fast will check local and upgrade from remote only if necessary',
        choices=[UPGRADE_MODE_FAST, UPGRADE_MODE_LATEST, UPGRADE_MODE_NO])
    argument_parser.add_argument('--download-only',
        help='download necessary files from remote, but do not install them', action='store_true')
    args = argument_parser.parse_args(sys.argv[1:])

    resource = parse_resource(args.resource)
    set_upgrade_mode(args.upgrade_mode)
    if args.dry_run:
        with dry_run():
            install_resources([resource])
            pprint.pprint(get_dry_run_result())
    elif args.download_only:
        set_download_while_dry_run(True)
        with dry_run():
            install_resources([resource])
    else:
        install_resources([resource])

