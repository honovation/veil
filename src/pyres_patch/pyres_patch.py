from __future__ import unicode_literals, print_function, division
import pyres.job
import veil_component


def patch_pyres_job_to_load_component_encapsulated_job_handler_class():
    pyres.job.Job.safe_str_to_class = staticmethod(component_aware_safe_str_to_class)


def component_aware_safe_str_to_class(qualified_class_name):
    segments = qualified_class_name.split('.')
    class_name = segments[-1]
    qualified_module_name = '.'.join(segments[:-1])
    module = veil_component.force_import_module(qualified_module_name)
    if hasattr(module, class_name):
        return getattr(module, class_name)
    else:
        raise Exception('Can not find {} in {}'.format(class_name, qualified_module_name))
