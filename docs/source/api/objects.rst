Objects (objetto.objects)
=========================

.. automodule:: objetto.objects

Object Class
------------
.. autoclass:: objetto.objects.Object
   :members: _state, data

   .. automethod:: objetto.objects.Object._get_relationship
   .. automethod:: objetto.objects.Object._get_attribute
   .. automethod:: objetto.objects.Object._clear
   .. automethod:: objetto.objects.Object._update
   .. automethod:: objetto.objects.Object._set
   .. automethod:: objetto.objects.Object._delete
   .. automethod:: objetto.objects.Object._locate
   .. automethod:: objetto.objects.Object._locate_data
   .. automethod:: objetto.objects.Object.deserialize
   .. automethod:: objetto.objects.Object.serialize

Attributes
----------
.. autofunction:: objetto.objects.attribute
.. autofunction:: objetto.objects.constant_attribute

Auxiliary Attributes
********************
.. autofunction:: objetto.objects.protected_attribute_pair
.. autofunction:: objetto.objects.dict_attribute
.. autofunction:: objetto.objects.protected_dict_attribute_pair
.. autofunction:: objetto.objects.list_attribute
.. autofunction:: objetto.objects.protected_list_attribute_pair
.. autofunction:: objetto.objects.set_attribute
.. autofunction:: objetto.objects.protected_set_attribute_pair

Auxiliary Class Factories
-------------------------
.. autofunction:: objetto.objects.dict_cls
.. autofunction:: objetto.objects.list_cls
.. autofunction:: objetto.objects.set_cls

Data Method Decorator
---------------------
.. autodecorator:: objetto.objects.data_method

Unique Descriptor
-----------------
.. autofunction:: objetto.objects.unique_descriptor

History Descriptor
------------------
.. autofunction:: objetto.objects.history_descriptor

Auxiliary Classes
-----------------

These are special types of objects that are used internally by :ref:`Auxiliary
Attributes` to contain multiple values in different ways.

.. note::
    Prefer using :ref:`Auxiliary Attributes` or :ref:`Auxiliary Class Factories`
    over :ref:`Auxiliary Classes` directly.

The mutable versions of :ref:`Auxiliary Classes` expose the mutable methods as
public, whereas the internally-mutable ones have them as protected (mutable method
names start with an underscore).

When subclassing :ref:`Auxiliary Classes`, the schema is defined by a
:class:`objetto.objects.Relationship` assigned to the class attribute
:attr:`objetto.bases.BaseAuxiliaryStructure._relationship`.

Dictionary Classes
******************

When subclassing a :class:`objetto.objects.DictObject`, the schema is defined by a
:class:`objetto.objects.Relationship` assigned to the class attribute
:attr:`objetto.bases.BaseDictStructure._key_relationship`.

.. autoclass:: objetto.objects.DictObject
   :members: _state, data

   .. automethod:: objetto.objects.DictObject._clear
   .. automethod:: objetto.objects.DictObject._update
   .. automethod:: objetto.objects.DictObject._set
   .. automethod:: objetto.objects.DictObject._discard
   .. automethod:: objetto.objects.DictObject._remove
   .. automethod:: objetto.objects.DictObject._locate
   .. automethod:: objetto.objects.DictObject._locate_data
   .. automethod:: objetto.objects.DictObject.deserialize
   .. automethod:: objetto.objects.DictObject.serialize

.. autoclass:: objetto.objects.MutableDictObject

   .. automethod:: objetto.objects.MutableDictObject.pop
   .. automethod:: objetto.objects.MutableDictObject.popitem
   .. automethod:: objetto.objects.MutableDictObject.setdefault

List Classes
************
.. autoclass:: objetto.objects.ListObject
   :members: _state, data

   .. automethod:: objetto.objects.ListObject.__getitem__
   .. automethod:: objetto.objects.ListObject._clear
   .. automethod:: objetto.objects.ListObject._insert
   .. automethod:: objetto.objects.ListObject._append
   .. automethod:: objetto.objects.ListObject._extend
   .. automethod:: objetto.objects.ListObject._remove
   .. automethod:: objetto.objects.ListObject._reverse
   .. automethod:: objetto.objects.ListObject._move
   .. automethod:: objetto.objects.ListObject._delete
   .. automethod:: objetto.objects.ListObject._update
   .. automethod:: objetto.objects.ListObject._locate
   .. automethod:: objetto.objects.ListObject._locate_data
   .. automethod:: objetto.objects.ListObject.deserialize
   .. automethod:: objetto.objects.ListObject.serialize

.. autoclass:: objetto.objects.MutableListObject

   .. automethod:: objetto.objects.MutableListObject.__getitem__
   .. automethod:: objetto.objects.MutableListObject.__setitem__
   .. automethod:: objetto.objects.MutableListObject.__delitem__
   .. automethod:: objetto.objects.MutableListObject.pop

Set Classes
***********
.. autoclass:: objetto.objects.SetObject
   :members: _state, data

   .. automethod:: objetto.objects.SetObject._from_iterable
   .. automethod:: objetto.objects.SetObject._clear
   .. automethod:: objetto.objects.SetObject._add
   .. automethod:: objetto.objects.SetObject._discard
   .. automethod:: objetto.objects.SetObject._remove
   .. automethod:: objetto.objects.SetObject._replace
   .. automethod:: objetto.objects.SetObject._update
   .. automethod:: objetto.objects.SetObject._locate
   .. automethod:: objetto.objects.SetObject._locate_data
   .. automethod:: objetto.objects.SetObject.deserialize
   .. automethod:: objetto.objects.SetObject.serialize

.. autoclass:: objetto.objects.MutableSetObject

   .. automethod:: objetto.objects.MutableSetObject.pop
   .. automethod:: objetto.objects.MutableSetObject.intersection_update
   .. automethod:: objetto.objects.MutableSetObject.symmetric_difference_update
   .. automethod:: objetto.objects.MutableSetObject.difference_update

Proxy Classes
-------------

Proxy Dictionary Class
**********************
.. autoclass:: objetto.objects.ProxyDictObject
   :members: _obj, _state, data

   .. automethod:: objetto.objects.ProxyDictObject.__reversed__
   .. automethod:: objetto.objects.ProxyDictObject.__getitem__
   .. automethod:: objetto.objects.ProxyDictObject._update
   .. automethod:: objetto.objects.ProxyDictObject._set
   .. automethod:: objetto.objects.ProxyDictObject._discard
   .. automethod:: objetto.objects.ProxyDictObject._remove
   .. automethod:: objetto.objects.ProxyDictObject.get
   .. automethod:: objetto.objects.ProxyDictObject.iteritems
   .. automethod:: objetto.objects.ProxyDictObject.iterkeys
   .. automethod:: objetto.objects.ProxyDictObject.itervalues
   .. automethod:: objetto.objects.ProxyDictObject.pop
   .. automethod:: objetto.objects.ProxyDictObject.popitem
   .. automethod:: objetto.objects.ProxyDictObject.setdefault

Proxy List Class
****************
.. autoclass:: objetto.objects.ProxyListObject
   :members: _obj, _state, data

   .. automethod:: objetto.objects.ProxyListObject.__setitem__
   .. automethod:: objetto.objects.ProxyListObject.__delitem__
   .. automethod:: objetto.objects.ProxyListObject.__reversed__
   .. automethod:: objetto.objects.ProxyListObject.__getitem__
   .. automethod:: objetto.objects.ProxyListObject._insert
   .. automethod:: objetto.objects.ProxyListObject._append
   .. automethod:: objetto.objects.ProxyListObject._extend
   .. automethod:: objetto.objects.ProxyListObject._remove
   .. automethod:: objetto.objects.ProxyListObject._reverse
   .. automethod:: objetto.objects.ProxyListObject._move
   .. automethod:: objetto.objects.ProxyListObject._delete
   .. automethod:: objetto.objects.ProxyListObject._update
   .. automethod:: objetto.objects.ProxyListObject.pop
   .. automethod:: objetto.objects.ProxyListObject.count
   .. automethod:: objetto.objects.ProxyListObject.index
   .. automethod:: objetto.objects.ProxyListObject.resolve_index
   .. automethod:: objetto.objects.ProxyListObject.resolve_continuous_slice

Proxy Set Class
***************
.. autoclass:: objetto.objects.ProxySetObject
   :members: _obj, _state, data

   .. automethod:: objetto.objects.ProxySetObject.pop
   .. automethod:: objetto.objects.ProxySetObject.intersection_update
   .. automethod:: objetto.objects.ProxySetObject.symmetric_difference_update
   .. automethod:: objetto.objects.ProxySetObject.difference_update
   .. automethod:: objetto.objects.ProxySetObject._from_iterable
   .. automethod:: objetto.objects.ProxySetObject._hash
   .. automethod:: objetto.objects.ProxySetObject._add
   .. automethod:: objetto.objects.ProxySetObject._discard
   .. automethod:: objetto.objects.ProxySetObject._remove
   .. automethod:: objetto.objects.ProxySetObject._replace
   .. automethod:: objetto.objects.ProxySetObject._update
   .. automethod:: objetto.objects.ProxySetObject.isdisjoint
   .. automethod:: objetto.objects.ProxySetObject.issubset
   .. automethod:: objetto.objects.ProxySetObject.issuperset
   .. automethod:: objetto.objects.ProxySetObject.intersection
   .. automethod:: objetto.objects.ProxySetObject.difference
   .. automethod:: objetto.objects.ProxySetObject.inverse_difference
   .. automethod:: objetto.objects.ProxySetObject.symmetric_difference
   .. automethod:: objetto.objects.ProxySetObject.union


Attribute Descriptor Class
--------------------------
.. autoclass:: objetto.objects.Attribute
   :members:
     relationship,
     delegated,
     dependencies,
     deserialize_to,
     fget,
     fset,
     fdel,
     constant,
     data_attribute,

   .. automethod:: objetto.objects.Attribute.__set__
   .. automethod:: objetto.objects.Attribute.__delete__
   .. automethod:: objetto.objects.Attribute.to_dict
   .. automethod:: objetto.objects.Attribute.set_value
   .. automethod:: objetto.objects.Attribute.delete_value
   .. automethod:: objetto.objects.Attribute.getter
   .. automethod:: objetto.objects.Attribute.setter
   .. automethod:: objetto.objects.Attribute.deleter

Relationship Classes
--------------------
.. autoclass:: objetto.objects.Relationship
   :members:
     child,
     history,
     data,
     data_relationship,

   .. automethod:: objetto.objects.Relationship.to_dict

.. autoclass:: objetto.objects.KeyRelationship
   :members:
     types,
     subtypes,
     checked,
     module,
     factory,
     passthrough,

   .. automethod:: objetto.objects.KeyRelationship.__hash__
   .. automethod:: objetto.objects.KeyRelationship.__eq__
   .. automethod:: objetto.objects.KeyRelationship.__repr__
   .. automethod:: objetto.objects.KeyRelationship.to_dict
   .. automethod:: objetto.objects.KeyRelationship.fabricate_key

Unique Descriptor Class
-----------------------
.. autoclass:: objetto.objects.UniqueDescriptor

   .. automethod:: objetto.objects.UniqueDescriptor.__get__

Action Class
------------
.. autoclass:: objetto.objects.Action

   .. autoattribute:: objetto.objects.Action.sender
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.objects.Action.receiver
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.objects.Action.locations
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.objects.Action.change
      :annotation: :  Data Attribute
