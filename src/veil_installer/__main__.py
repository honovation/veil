from __future__ import unicode_literals, print_function, division

if '__main__' == __name__:
    import sys
    import argparse
    import pprint
    from .installer import install_resources
    from .installer import dry_run
    from .installer import get_dry_run_result
    from .installer import do_install
    from .python_package_installer import python_package_resource
    from .component_installer import parse_resource

    do_install(python_package_resource(name='Jinja2'))
    argument_parser = argparse.ArgumentParser('Install resource')
    argument_parser.add_argument('resource', type=str, help='<installer_name>?<installer_arg1>&<installer_arg2>...')
    argument_parser.add_argument('--dry-run', help='list the resources required and installed or not', action='store_true')
    args = argument_parser.parse_args(sys.argv[1:])

    resource = parse_resource(args.resource)
    if args.dry_run:
        with dry_run():
            install_resources([resource])
            pprint.pprint(get_dry_run_result())
    else:
        install_resources([resource])

