# coding=utf-8
"""Microsoft Azure Blobs Storage: Base for all blob types"""
from __future__ import absolute_import  # Python 2: Fix azure import

from io import IOBase

from pycosio._core.io_base import memoizedmethod
from pycosio._core.exceptions import ObjectException
from pycosio.io import ObjectBufferedIOBase
from pycosio.storage.azure_blob._system import _AzureBlobSystem
from pycosio.storage.azure import _AzureStorageRawIOBase

# Store blob types specific classes
AZURE_BUFFERED = {}
AZURE_RAW = {}


def _new_blob(cls, name, kwargs):
    """
    Used to initialize a blob class.

    Args:
        cls (class): Class to initialize.
        name (str): Blob name.
        kwargs (dict): Initialization keyword arguments.

    Returns:
        str: Blob type.
    """
    # Try to get cached parameters
    try:
        storage_parameters = kwargs['storage_parameters'].copy()
        system = storage_parameters.get('pycosio.system_cached')

    # Or create new empty ones
    except KeyError:
        storage_parameters = dict()
        system = None

    # If none cached, create a new system
    if not system:
        system = cls._SYSTEM_CLASS(**kwargs)
        storage_parameters['pycosio.system_cached'] = system

    # Detect if file already exists
    try:
        # Also cache file header to avoid double head call
        # (in __new__ and __init__)
        storage_parameters['pycosio.raw_io._head'] = head = system.head(name)
    except ObjectException:
        # Unable to access to the file (May not exists, or may not have read
        # access permission), try to use arguments as blob type source.
        head = kwargs

    # Update file storage parameters
    kwargs['storage_parameters'] = storage_parameters

    # Return blob type
    return head.get('blob_type', system._default_blob_type)


class AzureBlobRawIO(_AzureStorageRawIOBase):
    """Binary Azure Blobs Storage Object I/O

    Args:
        name (path-like object): URL or path to the file which will be opened.
        mode (str): The mode can be 'r', 'w', 'a'
            for reading (default), writing or appending
        storage_parameters (dict): Azure service keyword arguments.
            This is generally Azure credentials and configuration. See
            "azure.storage.blob.baseblobservice.BaseBlobService" for more
            information.
        unsecure (bool): If True, disables TLS/SSL to improves
            transfer performance. But makes connection unsecure.
        blob_type (str): Blob type to use on new file creation.
            Possibles values: BlockBlob (default), AppendBlob, PageBlob.
    """
    _SYSTEM_CLASS = _AzureBlobSystem
    __DEFAULT_CLASS = True

    def __new__(cls, name, mode='r', **kwargs):
        # If call from a subclass, instantiate this subclass directly
        if cls is not AzureBlobRawIO:
            return IOBase.__new__(cls)

        # Get subclass
        return IOBase.__new__(AZURE_RAW[_new_blob(cls, name, kwargs)])

    @property
    @memoizedmethod
    def _get_to_stream(self):
        """
        Azure storage function that read a range to a stream.

        Returns:
            function: Read function.
        """
        return self._client.get_blob_to_stream


class AzureBlobBufferedIO(ObjectBufferedIOBase):
    """Buffered binary Azure Blobs Storage Object I/O

    Args:
        name (path-like object): URL or path to the file which will be opened.
        mode (str): The mode can be 'r', 'w' for reading (default) or writing
        buffer_size (int): The size of buffer.
        max_buffers (int): The maximum number of buffers to preload in read mode
            or awaiting flush in write mode. 0 for no limit.
        max_workers (int): The maximum number of threads that can be used to
            execute the given calls.
        storage_parameters (dict): Azure service keyword arguments.
            This is generally Azure credentials and configuration. See
            "azure.storage.blob.baseblobservice.BaseBlobService" for more
            information.
        unsecure (bool): If True, disables TLS/SSL to improves
            transfer performance. But makes connection unsecure.
        blob_type (str): Blob type to use on new file creation.
            Possibles values: BlockBlob (default), AppendBlob, PageBlob.
    """
    _SYSTEM_CLASS = _AzureBlobSystem
    __DEFAULT_CLASS = True

    def __new__(cls, name, mode='r', buffer_size=None, max_buffers=0,
                max_workers=None, **kwargs):
        # If call from a subclass, instantiate this subclass directly
        if cls is not AzureBlobBufferedIO:
            return IOBase.__new__(cls)

        # Get subclass
        return IOBase.__new__(AZURE_BUFFERED[_new_blob(cls, name, kwargs)])
