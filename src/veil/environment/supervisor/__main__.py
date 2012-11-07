import sys
from .supervisor_launcher import bring_up_programs
from .supervisor_launcher import bring_down_supervisor

if '__main__' == __name__:
    if 'up' == sys.argv[1]:
        bring_up_programs(*sys.argv[2:])
    elif 'down' == sys.argv[1]:
        bring_down_supervisor(*sys.argv[2:])