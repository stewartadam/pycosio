# coding=utf-8
"""Cloud storage abstract IO Base class"""
from functools import wraps
from io import IOBase, UnsupportedOperation
from threading import Lock
from itertools import chain

from pycosio._core.compat import fsdecode, ThreadPoolExecutor


class ObjectIOBase(IOBase):
    """
    Base class to handle cloud object.

    Args:
        name (path-like object): URL or path to the file which will be opened.
        mode (str): The mode can be 'r', 'w', 'a', 'x'
            for reading (default), writing or appending
    """

    def __init__(self, name, mode='r'):
        IOBase.__init__(self)

        self._name = fsdecode(name)
        self._mode = mode

        # Thread safe stream position
        self._seek = 0
        self._seek_lock = Lock()

        # Cache for values
        self._cache = {}

        # Set to True once file is closed
        self._closed = False

        # Select supported features based on mode
        self._writable = False
        self._readable = False
        self._seekable = True

        if 'w' in mode or 'a' in mode or 'x' in mode:
            self._writable = True

        elif 'r' in mode:
            self._readable = True

        else:
            raise ValueError('Invalid mode "%s"' % mode)

    def __str__(self):
        return "<%s.%s name='%s' mode='%s'>" % (
            self.__class__.__module__, self.__class__.__name__,
            self._name, self._mode)

    __repr__ = __str__

    @property
    def mode(self):
        """
        The mode.

        Returns:
            str: Mode.
        """
        return self._mode

    @property
    def name(self):
        """
        The file name.

        Returns:
            str: Name.
        """
        return self._name

    def readable(self):
        """
        Return True if the stream can be read from.
        If False, read() will raise OSError.

        Returns:
            bool: Supports reading.
        """
        return self._readable

    def seekable(self):
        """
        Return True if the stream supports random access.
        If False, seek(), tell() and truncate() will raise OSError.

        Returns:
            bool: Supports random access.
        """
        return self._seekable

    def tell(self):
        """Return the current stream position.

        Returns:
            int: Stream position."""
        if not self._seekable:
            raise UnsupportedOperation('tell')

        with self._seek_lock:
            return self._seek

    def writable(self):
        """
        Return True if the stream supports writing.
        If False, write() and truncate() will raise OSError.

        Returns:
            bool: Supports writing.
        """
        return self._writable


def memoizedmethod(method):
    """
    Decorator that caches method result.

    Args:
        method (function): Method

    Returns:
        function: Memoized method.

    Notes:
        Target method class needs as "_cache" attribute (dict).

        It is the case of "ObjectIOBase" and all its subclasses.
    """
    method_name = method.__name__

    @wraps(method)
    def patched(self, *args, **kwargs):
        """Patched method"""
        # Gets value from cache
        try:
            return self._cache[method_name]

        # Evaluates and cache value
        except KeyError:
            result = self._cache[method_name] = method(
                self, *args, **kwargs)
            return result

    return patched


class WorkerPoolBase:
    """
    Base class that handle a worker pool.

    Args:
        max_workers (int): Maximum number of workers.
    """

    def __init__(self, max_workers=None):
        self._workers_count = max_workers

    @property
    @memoizedmethod
    def _workers(self):
        """Executor pool

        Returns:
            concurrent.futures.Executor: Executor pool"""
        # Lazy instantiate workers pool on first call
        return ThreadPoolExecutor(max_workers=self._workers_count)

    def _generate_async(self, generator):
        """
        Return the previous generator object after having run the first element
        evaluation as a background task.

        Args:
            generator (iterable): A generator function.

        Returns:
            iterable: The generator function with first element evaluated
                in background.
        """
        first_value_future = self._workers.submit(next, generator)

        def get_first_element(future=first_value_future):
            """
            Get first element value from future.

            Args:
                future (concurrent.futures._base.Future): First value future.

            Returns:
                Evaluated value
            """
            try:
                yield future.result()
            except StopIteration:
                return

        return chain(get_first_element(), generator)
