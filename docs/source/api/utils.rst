Utils (objetto.utils)
=====================

.. automodule:: objetto.utils

Caller Module
-------------
.. automodule:: objetto.utils.caller_module
   :members:

Custom Representations
----------------------
.. automodule:: objetto.utils.custom_repr
   :members:

Dummy Context
-------------
.. automodule:: objetto.utils.dummy_context
   :members:

Factoring
---------
.. automodule:: objetto.utils.factoring
   :members:

Lazy Import
-----------
.. automodule:: objetto.utils.lazy_import
   :members:

List Operations
---------------
.. automodule:: objetto.utils.list_operations
   :members:

Qualified Name
--------------

.. automodule:: objetto.utils.qualname
   :members:

Recursive Representation
------------------------
.. automodule:: objetto.utils.recursive_repr

   .. autodecorator:: objetto.utils.recursive_repr.recursive_repr

Re-Raise Context
----------------
.. automodule:: objetto.utils.reraise_context
   :members:

Simplify Exceptions
-------------------
.. automodule:: objetto.utils.simplify_exceptions

   .. autodecorator:: objetto.utils.simplify_exceptions.simplify_exceptions

Storage
-------
.. automodule:: objetto.utils.storage

   .. autoclass:: objetto.utils.storage.AbstractStorage

      .. automethod:: objetto.utils.storage.AbstractStorage.update
      .. automethod:: objetto.utils.storage.AbstractStorage.query
      .. automethod:: objetto.utils.storage.AbstractStorage.to_dict

   .. autoclass:: objetto.utils.storage.Storage

      .. automethod:: objetto.utils.storage.Storage.to_dict
      .. automethod:: objetto.utils.storage.Storage.update
      .. automethod:: objetto.utils.storage.Storage.query
      .. automethod:: objetto.utils.storage.Storage.evolver

   .. autoclass:: objetto.utils.storage.StorageEvolver
      :members: updates

      .. automethod:: objetto.utils.storage.StorageEvolver.to_dict
      .. automethod:: objetto.utils.storage.StorageEvolver.update
      .. automethod:: objetto.utils.storage.StorageEvolver.query
      .. automethod:: objetto.utils.storage.StorageEvolver.persistent
      .. automethod:: objetto.utils.storage.StorageEvolver.fork
      .. automethod:: objetto.utils.storage.StorageEvolver.is_dirty
      .. automethod:: objetto.utils.storage.StorageEvolver.reset
      .. automethod:: objetto.utils.storage.StorageEvolver.commit

Subject-Observer
----------------
.. automodule:: objetto.utils.subject_observer

   .. autoclass:: objetto.utils.subject_observer.Subject

      .. automethod:: objetto.utils.subject_observer.Subject.__deepcopy__
      .. automethod:: objetto.utils.subject_observer.Subject.__copy__
      .. automethod:: objetto.utils.subject_observer.Subject.__reduce__
      .. automethod:: objetto.utils.subject_observer.Subject.wait
      .. automethod:: objetto.utils.subject_observer.Subject.send
      .. automethod:: objetto.utils.subject_observer.Subject.register_observer
      .. automethod:: objetto.utils.subject_observer.Subject.deregister_observer
      .. automethod:: objetto.utils.subject_observer.Subject.get_token

   .. autoclass:: objetto.utils.subject_observer.Observer

      .. automethod:: objetto.utils.subject_observer.Observer.__observe__
      .. automethod:: objetto.utils.subject_observer.Observer.start_observing
      .. automethod:: objetto.utils.subject_observer.Observer.stop_observing

   .. autoclass:: objetto.utils.subject_observer.ObserverToken
      :members: observer

      .. automethod:: objetto.utils.subject_observer.ObserverToken.wait

   .. autoclass:: objetto.utils.subject_observer.ObserverExceptionInfo

Type Checking
-------------
.. automodule:: objetto.utils.type_checking
   :members:

Weak Reference
--------------
.. automodule:: objetto.utils.weak_reference

   .. autoclass:: objetto.utils.weak_reference.WeakReference

      .. automethod:: objetto.utils.weak_reference.WeakReference.__hash__
      .. automethod:: objetto.utils.weak_reference.WeakReference.__eq__
      .. automethod:: objetto.utils.weak_reference.WeakReference.__ne__
      .. automethod:: objetto.utils.weak_reference.WeakReference.__repr__
      .. automethod:: objetto.utils.weak_reference.WeakReference.__str__
      .. automethod:: objetto.utils.weak_reference.WeakReference.__call__
      .. automethod:: objetto.utils.weak_reference.WeakReference.__reduce__
