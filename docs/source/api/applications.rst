Applications (objetto.applications)
===================================

.. automodule:: objetto.applications

Application Class
-----------------

.. autoclass:: objetto.applications.ApplicationMeta
   :members: _roots, _root_names

.. autoclass:: objetto.applications.Application
   :members: is_reading, is_writing

   .. automethod:: objetto.applications.Application._get_property
   .. automethod:: objetto.applications.Application._set_property
   .. automethod:: objetto.applications.Application._delete_property
   .. automethod:: objetto.applications.Application.read_context
   .. automethod:: objetto.applications.Application.write_context
   .. automethod:: objetto.applications.Application.temporary_context
   .. automethod:: objetto.applications.Application.take_snapshot

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

Application Property Class
--------------------------
.. autoclass:: objetto.applications.ApplicationProperty
   :members: default_factory, module

   .. automethod:: objetto.applications.ApplicationProperty.fabricate_default_value

Application Snapshot Class
--------------------------

.. autoclass:: objetto.applications.ApplicationSnapshot
   :members: app