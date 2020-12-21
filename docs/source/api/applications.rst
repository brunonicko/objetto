Applications (objetto.applications)
===================================

.. automodule:: objetto.applications

Application Class
-----------------

.. autoclass:: objetto.applications.ApplicationMeta
   :members: _roots, _root_names

.. autoclass:: objetto.applications.Application

   .. automethod:: objetto.applications.Application.read_context()
   .. automethod:: objetto.applications.Application.write_context()
   .. automethod:: objetto.applications.Application.temporary_context()

Root Descriptor
---------------
.. autofunction:: objetto.applications.root

Root Descriptor Class
---------------------
.. autoclass:: objetto.applications.ApplicationRoot
   :members: obj_type, priority, kwargs

   .. automethod:: objetto.applications.ApplicationRoot.__get__
   .. automethod:: objetto.applications.ApplicationRoot.__hash__
   .. automethod:: objetto.applications.ApplicationRoot.__eq__
   .. automethod:: objetto.applications.ApplicationRoot.__repr__
   .. automethod:: objetto.applications.ApplicationRoot.to_dict
