Objects
=======

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

Auxiliary and Proxy Classes
---------------------------

Dictionary Classes
******************
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

List Classes
************
.. autoclass:: objetto.objects.ListObject
.. autoclass:: objetto.objects.MutableListObject
.. autoclass:: objetto.objects.ProxyListObject

Set Classes
***********
.. autoclass:: objetto.objects.SetObject
.. autoclass:: objetto.objects.MutableSetObject
.. autoclass:: objetto.objects.ProxySetObject

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
