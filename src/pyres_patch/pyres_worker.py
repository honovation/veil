import pyres.scripts
from .pyres_patch import patch_pyres_job_to_load_component_encapsulated_job_handler_class

if '__main__' == __name__:
    patch_pyres_job_to_load_component_encapsulated_job_handler_class()
    pyres.scripts.pyres_worker()