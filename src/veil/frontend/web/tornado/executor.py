from __future__ import unicode_literals, print_function, division
import contextlib
from logging import getLogger
import threading
from tornado.ioloop import IOLoop
from tornado.stack_context import  NullContext
import sys
import time
from sandal.test import get_executing_test

LOGGER = getLogger(__name__)
lock = threading.Lock()

def require_io_loop_executor():
    lock.acquire()
    try:
        test = get_executing_test()
        if not hasattr(test, '_io_loop_executor'):
            test._io_loop_executor = IOLoopExecutor(IOLoop.instance())
        return getattr(test, '_io_loop_executor')
    finally:
        lock.release()


@contextlib.contextmanager
def stop_on_exception(io_loop_executor):
    try:
        yield
    except GeneratorExit:
        pass
    except:
        LOGGER.debug('caught exception', exc_info=1)
        io_loop_executor.stop(failure=sys.exc_info())
        raise


class IOLoopExecutor(object):
    def __init__(self, io_loop):
        self.io_loop = io_loop
        self.stopped = False
        self.running = False
        self.failure = None
        self.return_value = None

    def execute(self, condition=None, timeout=10):
        """Runs the IOLoop until stop is called or timeout has passed.

        In the event of a timeout, an exception will be thrown.

        If condition is not None, the IOLoop will be restarted after stop()
        until condition() returns true.
        """
        if not self.stopped:
            if timeout:
                def timeout_func():
                    try:
                        raise Exception('Async operation timed out after {} seconds'.format(timeout))
                    except:
                        self.stop(failure = sys.exc_info())

                self.io_loop.add_timeout(time.time() + timeout, timeout_func)
            while True:
                self.running = True
                with NullContext():
                    # Wipe out the StackContext that was established in
                    # self.run() so that all callbacks executed inside the
                    # IOLoop will re-run it.
                    self.io_loop.start()
                if (self.failure is not None or
                    condition is None or condition()):
                    break
        assert self.stopped
        self.stopped = False
        if self.failure is not None:
            raise self.failure[0], self.failure[1], self.failure[2]
        result = self.return_value
        self.return_value = None
        return result

    def stop(self, return_value=None, failure=None):
        assert return_value or failure
        self.failure = failure
        self.return_value = return_value
        self.stopped = True
        if self.running:
            self.io_loop.stop()
            self.running = False

    def __enter__(self):
        self.context = stop_on_exception(self)
        return self.context.__enter__()


    def __exit__(self, type, value, traceback):
        return self.context.__exit__(type, value, traceback)

