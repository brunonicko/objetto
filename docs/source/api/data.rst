Data
====

Data Classes
------------
.. autoclass:: objetto.data.Data
   :members: _state

   .. automethod:: objetto.data.Data._get_relationship
   .. automethod:: objetto.data.Data._get_attribute
   .. automethod:: objetto.data.Data._hash
   .. automethod:: objetto.data.Data._eq
   .. automethod:: objetto.data.Data._clear
   .. automethod:: objetto.data.Data._set
   .. automethod:: objetto.data.Data._delete
   .. automethod:: objetto.data.Data._update
   .. automethod:: objetto.data.Data.deserialize
   .. automethod:: objetto.data.Data.serialize

.. autoclass:: objetto.data.InteractiveData

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

Dictionary Classes
******************
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

List Classes
************
.. autoclass:: objetto.data.ListData
   :members: _state

   .. automethod:: objetto.data.ListData.__getitem__
   .. automethod:: objetto.data.ListData._clear
   .. automethod:: objetto.data.ListData._insert
   .. automethod:: objetto.data.ListData._append
   .. automethod:: objetto.data.ListData._extend
   .. automethod:: objetto.data.ListData._remove
   .. automethod:: objetto.data.ListData._reverse
   .. automethod:: objetto.data.ListData._move
   .. automethod:: objetto.data.ListData._delete
   .. automethod:: objetto.data.ListData._update
   .. automethod:: objetto.data.ListData.deserialize
   .. automethod:: objetto.data.ListData.serialize

.. autoclass:: objetto.data.InteractiveListData

Set Classes
************
.. autoclass:: objetto.data.SetData
   :members: _state

   .. automethod:: objetto.data.SetData._from_iterable
   .. automethod:: objetto.data.SetData._clear
   .. automethod:: objetto.data.SetData._add
   .. automethod:: objetto.data.SetData._discard
   .. automethod:: objetto.data.SetData._remove
   .. automethod:: objetto.data.SetData._replace
   .. automethod:: objetto.data.SetData._update
   .. automethod:: objetto.data.SetData.deserialize
   .. automethod:: objetto.data.SetData.serialize

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

Unique Descriptor Class
-----------------------
.. autoclass:: objetto.data.UniqueDescriptor
   :members: relationship

   .. automethod:: objetto.data.UniqueDescriptor.__get__
