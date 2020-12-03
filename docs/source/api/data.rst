Data
====

Data Classes
------------
.. autoclass:: objetto.data.ProtectedData
   :members: _state

   .. automethod:: objetto.data.ProtectedData._get_relationship
   .. automethod:: objetto.data.ProtectedData._get_attribute
   .. automethod:: objetto.data.ProtectedData._hash
   .. automethod:: objetto.data.ProtectedData._eq
   .. automethod:: objetto.data.ProtectedData._clear
   .. automethod:: objetto.data.ProtectedData._set
   .. automethod:: objetto.data.ProtectedData._delete
   .. automethod:: objetto.data.ProtectedData._update
   .. automethod:: objetto.data.ProtectedData.deserialize
   .. automethod:: objetto.data.ProtectedData.serialize

.. autoclass:: objetto.data.Data

Attribute Descriptors
---------------------
.. autofunction:: objetto.data.data_attribute
.. autofunction:: objetto.data.data_constant_attribute
.. autofunction:: objetto.data.data_dict_attribute
.. autofunction:: objetto.data.data_list_attribute
.. autofunction:: objetto.data.data_set_attribute
.. autofunction:: objetto.data.data_dict_cls
.. autofunction:: objetto.data.data_list_cls
.. autofunction:: objetto.data.data_set_cls

Auxiliary Data Classes
------------------------
.. autoclass:: objetto.data.DictData
   :members: _key_relationship, _state

   .. automethod:: objetto.data.DictData._clear
   .. automethod:: objetto.data.DictData._set
   .. automethod:: objetto.data.DictData._discard
   .. automethod:: objetto.data.DictData._remove
   .. automethod:: objetto.data.DictData._update
   .. automethod:: objetto.data.DictData.deserialize
   .. automethod:: objetto.data.DictData.serialize

.. autoclass:: objetto.data.InteractiveDictData
.. autoclass:: objetto.data.ListData
.. autoclass:: objetto.data.InteractiveListData
.. autoclass:: objetto.data.SetData
.. autoclass:: objetto.data.InteractiveSetData

Attribute Descriptor Class
--------------------------
.. autoclass:: objetto.data.DataAttribute
   :members: relationship

Relationship Classes
--------------------
.. autoclass:: objetto.data.DataRelationship
   :members: compared

   .. automethod:: objetto.data.DataRelationship.to_dict

.. autoclass:: objetto.data.KeyRelationship
   :members:
     types,
     subtypes,
     checked,
     module,
     factory,
     passthrough,

   .. automethod:: objetto.data.KeyRelationship.__hash__
   .. automethod:: objetto.data.KeyRelationship.__eq__
   .. automethod:: objetto.data.KeyRelationship.__repr__
   .. automethod:: objetto.data.KeyRelationship.to_dict
   .. automethod:: objetto.data.KeyRelationship.fabricate_key
