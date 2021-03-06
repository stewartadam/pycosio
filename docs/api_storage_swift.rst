pycosio.storage.swift
=====================

OpenStack Swift

Mount
-----

An OpenStack Swift project can be mounted using the Pycosio ``mount`` function.

``storage_parameters`` await arguments to pass to the
``swiftclient.client.Connection`` class from ``python-swiftclient`` Python
library.

This example shows the mount of OpenStack Swift with a minimal configuration:

.. code-block:: python

    import pycosio

    # Mount OpenStack Swift manually (Minimal configuration)
    pycosio.mount(storage='swift', storage_parameters=dict(
            authurl='my_auth_url',
            user='my_user',
            key='my_key',
            auth_version='3',
            os_options=dict(
                region_name='my_region',
                project_id='my_project'
            )
        )
    )

    # Call of pycosio on an OpenStack Swift object.
    with pycosio.open(
            'https://objects.my_cloud.com/v1/my_project/my_container/my_object',
            'rt') as file:
        text = file.read()


Limitation
~~~~~~~~~~

Only one configuration per OpenStack project can be mounted simultaneously.

Files objects classes
---------------------

.. automodule:: pycosio.storage.swift
   :members:
   :inherited-members:

.. toctree::
   :maxdepth: 2
