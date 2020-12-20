Bases (objetto.bases)
=====================

.. automodule:: objetto.bases

Base Classes
------------

.. autoclass:: objetto.bases.Base
   :members: _initializing

   .. automethod:: objetto.bases.Base.__copy__
   .. automethod:: objetto.bases.Base.__repr__
   .. automethod:: objetto.bases.Base.__ne__
   .. automethod:: objetto.bases.Base.__dir__

.. autoclass:: objetto.bases.BaseHashable

   .. automethod:: objetto.bases.BaseHashable.__hash__

.. autoclass:: objetto.bases.BaseSized

   .. automethod:: objetto.bases.BaseSized.__len__

.. autoclass:: objetto.bases.BaseIterable

   .. automethod:: objetto.bases.BaseIterable.__iter__

.. autoclass:: objetto.bases.BaseContainer

   .. automethod:: objetto.bases.BaseContainer.__contains__

Base Metaclasses
----------------

.. autoclass:: objetto.bases.BaseMeta
   :members: __fullname__

   .. automethod:: objetto.bases.BaseMeta.__repr__
   .. automethod:: objetto.bases.BaseMeta.__dir__
   .. automethod:: objetto.bases.BaseMeta.__setattr__
   .. automethod:: objetto.bases.BaseMeta.__delattr__

Base Decorators
---------------

.. autodecorator:: objetto.bases.final
.. autodecorator:: objetto.bases.init

Base Functions
--------------

.. autofunction:: objetto.bases.simplify_member_names
.. autofunction:: objetto.bases.make_base_cls

Base Context Managers
---------------------

.. autofunction:: objetto.bases.init_context

Base Abstract Member
--------------------

.. autofunction:: objetto.bases.abstract_member

Base Collection Classes
-----------------------

.. autoclass:: objetto.bases.BaseCollection

   .. automethod:: objetto.bases.BaseCollection.find_with_attributes

.. autoclass:: objetto.bases.BaseProtectedCollection

   .. automethod:: objetto.bases.BaseProtectedCollection._clear

.. autoclass:: objetto.bases.BaseInteractiveCollection

   .. automethod:: objetto.bases.BaseInteractiveCollection.clear

.. autoclass:: objetto.bases.BaseMutableCollection

   .. automethod:: objetto.bases.BaseMutableCollection.clear

Base Dictionary Classes
***********************

.. autoclass:: objetto.bases.BaseDict

   .. automethod:: objetto.bases.BaseDict.__eq__
   .. automethod:: objetto.bases.BaseDict.__reversed__
   .. automethod:: objetto.bases.BaseDict.__getitem__
   .. automethod:: objetto.bases.BaseDict.get
   .. automethod:: objetto.bases.BaseDict.iteritems
   .. automethod:: objetto.bases.BaseDict.iterkeys
   .. automethod:: objetto.bases.BaseDict.itervalues
   .. automethod:: objetto.bases.BaseDict.items
   .. automethod:: objetto.bases.BaseDict.keys
   .. automethod:: objetto.bases.BaseDict.values

.. autoclass:: objetto.bases.BaseProtectedDict

   .. automethod:: objetto.bases.BaseProtectedDict._discard
   .. automethod:: objetto.bases.BaseProtectedDict._remove
   .. automethod:: objetto.bases.BaseProtectedDict._set
   .. automethod:: objetto.bases.BaseProtectedDict._update

.. autoclass:: objetto.bases.BaseInteractiveDict

   .. automethod:: objetto.bases.BaseInteractiveDict.discard
   .. automethod:: objetto.bases.BaseInteractiveDict.remove
   .. automethod:: objetto.bases.BaseInteractiveDict.set
   .. automethod:: objetto.bases.BaseInteractiveDict.update

.. autoclass:: objetto.bases.BaseMutableDict

   .. automethod:: objetto.bases.BaseMutableDict.__setitem__
   .. automethod:: objetto.bases.BaseMutableDict.__delitem__
   .. automethod:: objetto.bases.BaseMutableDict.clear
   .. automethod:: objetto.bases.BaseMutableDict.pop
   .. automethod:: objetto.bases.BaseMutableDict.popitem
   .. automethod:: objetto.bases.BaseMutableDict.setdefault
   .. automethod:: objetto.bases.BaseMutableDict.discard
   .. automethod:: objetto.bases.BaseMutableDict.remove
   .. automethod:: objetto.bases.BaseMutableDict.set
   .. automethod:: objetto.bases.BaseMutableDict.update

Base List Classes
*****************

.. autoclass:: objetto.bases.BaseList

   .. automethod:: objetto.bases.BaseList.__eq__
   .. automethod:: objetto.bases.BaseList.__reversed__
   .. automethod:: objetto.bases.BaseList.__getitem__
   .. automethod:: objetto.bases.BaseList.count
   .. automethod:: objetto.bases.BaseList.index
   .. automethod:: objetto.bases.BaseList.resolve_index
   .. automethod:: objetto.bases.BaseList.resolve_continuous_slice

.. autoclass:: objetto.bases.BaseProtectedList

   .. automethod:: objetto.bases.BaseProtectedList._insert
   .. automethod:: objetto.bases.BaseProtectedList._append
   .. automethod:: objetto.bases.BaseProtectedList._extend
   .. automethod:: objetto.bases.BaseProtectedList._remove
   .. automethod:: objetto.bases.BaseProtectedList._reverse
   .. automethod:: objetto.bases.BaseProtectedList._move
   .. automethod:: objetto.bases.BaseProtectedList._delete
   .. automethod:: objetto.bases.BaseProtectedList._update

.. autoclass:: objetto.bases.BaseInteractiveList

   .. automethod:: objetto.bases.BaseInteractiveList.insert
   .. automethod:: objetto.bases.BaseInteractiveList.append
   .. automethod:: objetto.bases.BaseInteractiveList.extend
   .. automethod:: objetto.bases.BaseInteractiveList.remove
   .. automethod:: objetto.bases.BaseInteractiveList.reverse
   .. automethod:: objetto.bases.BaseInteractiveList.move
   .. automethod:: objetto.bases.BaseInteractiveList.delete
   .. automethod:: objetto.bases.BaseInteractiveList.update

.. autoclass:: objetto.bases.BaseMutableList

   .. automethod:: objetto.bases.BaseMutableList.__iadd__
   .. automethod:: objetto.bases.BaseMutableList.__getitem__
   .. automethod:: objetto.bases.BaseMutableList.__setitem__
   .. automethod:: objetto.bases.BaseMutableList.__delitem__
   .. automethod:: objetto.bases.BaseMutableList.pop
   .. automethod:: objetto.bases.BaseMutableList.clear
   .. automethod:: objetto.bases.BaseMutableList.insert
   .. automethod:: objetto.bases.BaseMutableList.append
   .. automethod:: objetto.bases.BaseMutableList.extend
   .. automethod:: objetto.bases.BaseMutableList.remove
   .. automethod:: objetto.bases.BaseMutableList.reverse
   .. automethod:: objetto.bases.BaseMutableList.move
   .. automethod:: objetto.bases.BaseMutableList.delete
   .. automethod:: objetto.bases.BaseMutableList.update

Base Set Classes
*****************

.. autoclass:: objetto.bases.BaseSet

   .. automethod:: objetto.bases.BaseSet.__le__
   .. automethod:: objetto.bases.BaseSet.__lt__
   .. automethod:: objetto.bases.BaseSet.__gt__
   .. automethod:: objetto.bases.BaseSet.__ge__
   .. automethod:: objetto.bases.BaseSet.__and__
   .. automethod:: objetto.bases.BaseSet.__rand__
   .. automethod:: objetto.bases.BaseSet.__sub__
   .. automethod:: objetto.bases.BaseSet.__rsub__
   .. automethod:: objetto.bases.BaseSet.__or__
   .. automethod:: objetto.bases.BaseSet.__ror__
   .. automethod:: objetto.bases.BaseSet.__xor__
   .. automethod:: objetto.bases.BaseSet.__rxor__
   .. automethod:: objetto.bases.BaseSet.__eq__
   .. automethod:: objetto.bases.BaseSet._from_iterable
   .. automethod:: objetto.bases.BaseSet._hash
   .. automethod:: objetto.bases.BaseSet.isdisjoint
   .. automethod:: objetto.bases.BaseSet.issubset
   .. automethod:: objetto.bases.BaseSet.issuperset
   .. automethod:: objetto.bases.BaseSet.intersection
   .. automethod:: objetto.bases.BaseSet.symmetric_difference
   .. automethod:: objetto.bases.BaseSet.union
   .. automethod:: objetto.bases.BaseSet.difference
   .. automethod:: objetto.bases.BaseSet.inverse_difference

.. autoclass:: objetto.bases.BaseProtectedSet

   .. automethod:: objetto.bases.BaseProtectedSet._add
   .. automethod:: objetto.bases.BaseProtectedSet._discard
   .. automethod:: objetto.bases.BaseProtectedSet._remove
   .. automethod:: objetto.bases.BaseProtectedSet._replace
   .. automethod:: objetto.bases.BaseProtectedSet._update

.. autoclass:: objetto.bases.BaseInteractiveSet

   .. automethod:: objetto.bases.BaseInteractiveSet.add
   .. automethod:: objetto.bases.BaseInteractiveSet.discard
   .. automethod:: objetto.bases.BaseInteractiveSet.remove
   .. automethod:: objetto.bases.BaseInteractiveSet.replace
   .. automethod:: objetto.bases.BaseInteractiveSet.update

.. autoclass:: objetto.bases.BaseMutableSet

   .. automethod:: objetto.bases.BaseMutableSet.__iand__
   .. automethod:: objetto.bases.BaseMutableSet.__isub__
   .. automethod:: objetto.bases.BaseMutableSet.__ior__
   .. automethod:: objetto.bases.BaseMutableSet.__ixor__
   .. automethod:: objetto.bases.BaseMutableSet.pop
   .. automethod:: objetto.bases.BaseMutableSet.intersection_update
   .. automethod:: objetto.bases.BaseMutableSet.symmetric_difference_update
   .. automethod:: objetto.bases.BaseMutableSet.difference_update
   .. automethod:: objetto.bases.BaseMutableSet.clear
   .. automethod:: objetto.bases.BaseMutableSet.add
   .. automethod:: objetto.bases.BaseMutableSet.discard
   .. automethod:: objetto.bases.BaseMutableSet.remove
   .. automethod:: objetto.bases.BaseMutableSet.replace
   .. automethod:: objetto.bases.BaseMutableSet.update

Base Exception Class
--------------------
.. autoclass:: objetto.bases.BaseObjettoException

Base State Class
----------------
.. autoclass:: objetto.bases.BaseState
   :members: _internal

   .. automethod:: objetto.bases.BaseState.__hash__
   .. automethod:: objetto.bases.BaseState.__eq__
   .. automethod:: objetto.bases.BaseState.__copy__
   .. automethod:: objetto.bases.BaseState.__repr__
   .. automethod:: objetto.bases.BaseState.__str__

Base Structure Classes
----------------------
.. autoclass:: objetto.bases.BaseStructure
   :members: _state

   .. automethod:: objetto.bases.BaseStructure.__hash__
   .. automethod:: objetto.bases.BaseStructure.__eq__
   .. automethod:: objetto.bases.BaseStructure._hash
   .. automethod:: objetto.bases.BaseStructure._eq
   .. automethod:: objetto.bases.BaseStructure._get_relationship
   .. automethod:: objetto.bases.BaseStructure.deserialize_value
   .. automethod:: objetto.bases.BaseStructure.serialize_value
   .. automethod:: objetto.bases.BaseStructure.deserialize
   .. automethod:: objetto.bases.BaseStructure.serialize

.. autoclass:: objetto.bases.BaseInteractiveStructure

.. autoclass:: objetto.bases.BaseMutableStructure

.. autoclass:: objetto.bases.BaseAuxiliaryStructure
   :members: _relationship

   .. automethod:: objetto.bases.BaseAuxiliaryStructure.find_with_attributes
   .. automethod:: objetto.bases.BaseAuxiliaryStructure._get_relationship

.. autoclass:: objetto.bases.BaseInteractiveAuxiliaryStructure

.. autoclass:: objetto.bases.BaseMutableAuxiliaryStructure

Base Dict Structure Classes
***************************

.. autoclass:: objetto.bases.BaseDictStructure
   :members: _key_relationship, _state

   .. automethod:: objetto.bases.BaseDictStructure.__repr__
   .. automethod:: objetto.bases.BaseDictStructure.__reversed__
   .. automethod:: objetto.bases.BaseDictStructure.__getitem__
   .. automethod:: objetto.bases.BaseDictStructure.__len__
   .. automethod:: objetto.bases.BaseDictStructure.__iter__
   .. automethod:: objetto.bases.BaseDictStructure.__contains__
   .. automethod:: objetto.bases.BaseDictStructure.get
   .. automethod:: objetto.bases.BaseDictStructure.iteritems
   .. automethod:: objetto.bases.BaseDictStructure.iterkeys
   .. automethod:: objetto.bases.BaseDictStructure.itervalues

.. autoclass:: objetto.bases.BaseInteractiveDictStructure

.. autoclass:: objetto.bases.BaseMutableDictStructure

Base List Structure Classes
***************************

.. autoclass:: objetto.bases.BaseListStructure
   :members: _state

   .. automethod:: objetto.bases.BaseListStructure.__repr__
   .. automethod:: objetto.bases.BaseListStructure.__reversed__
   .. automethod:: objetto.bases.BaseListStructure.__len__
   .. automethod:: objetto.bases.BaseListStructure.__iter__
   .. automethod:: objetto.bases.BaseListStructure.__contains__
   .. automethod:: objetto.bases.BaseListStructure.count
   .. automethod:: objetto.bases.BaseListStructure.index
   .. automethod:: objetto.bases.BaseListStructure.resolve_index
   .. automethod:: objetto.bases.BaseListStructure.resolve_continuous_slice

.. autoclass:: objetto.bases.BaseInteractiveListStructure
.. autoclass:: objetto.bases.BaseMutableListStructure

Base Set Structure Classes
**************************

.. autoclass:: objetto.bases.BaseSetStructure
   :members: _state

   .. automethod:: objetto.bases.BaseSetStructure.__repr__
   .. automethod:: objetto.bases.BaseSetStructure.__len__
   .. automethod:: objetto.bases.BaseSetStructure.__iter__
   .. automethod:: objetto.bases.BaseSetStructure.__contains__
   .. automethod:: objetto.bases.BaseSetStructure.isdisjoint
   .. automethod:: objetto.bases.BaseSetStructure.issubset
   .. automethod:: objetto.bases.BaseSetStructure.issuperset
   .. automethod:: objetto.bases.BaseSetStructure.intersection
   .. automethod:: objetto.bases.BaseSetStructure.difference
   .. automethod:: objetto.bases.BaseSetStructure.inverse_difference
   .. automethod:: objetto.bases.BaseSetStructure.symmetric_difference
   .. automethod:: objetto.bases.BaseSetStructure.union

.. autoclass:: objetto.bases.BaseInteractiveSetStructure
.. autoclass:: objetto.bases.BaseMutableSetStructure

Base Attribute Structure Classes
********************************

.. autoclass:: objetto.bases.BaseAttributeStructure
   :members: _state

   .. automethod:: objetto.bases.BaseAttributeStructure.__repr__
   .. automethod:: objetto.bases.BaseAttributeStructure.__reversed__
   .. automethod:: objetto.bases.BaseAttributeStructure.__getitem__
   .. automethod:: objetto.bases.BaseAttributeStructure.__len__
   .. automethod:: objetto.bases.BaseAttributeStructure.__iter__
   .. automethod:: objetto.bases.BaseAttributeStructure.__contains__
   .. automethod:: objetto.bases.BaseAttributeStructure._get_relationship
   .. automethod:: objetto.bases.BaseAttributeStructure._get_attribute
   .. automethod:: objetto.bases.BaseAttributeStructure._set
   .. automethod:: objetto.bases.BaseAttributeStructure._delete
   .. automethod:: objetto.bases.BaseAttributeStructure._update
   .. automethod:: objetto.bases.BaseAttributeStructure.keys
   .. automethod:: objetto.bases.BaseAttributeStructure.find_with_attributes

.. autoclass:: objetto.bases.BaseInteractiveAttributeStructure

   .. automethod:: objetto.bases.BaseInteractiveAttributeStructure.set
   .. automethod:: objetto.bases.BaseInteractiveAttributeStructure.delete
   .. automethod:: objetto.bases.BaseInteractiveAttributeStructure.update

.. autoclass:: objetto.bases.BaseMutableAttributeStructure

   .. automethod:: objetto.bases.BaseMutableAttributeStructure.__setitem__
   .. automethod:: objetto.bases.BaseMutableAttributeStructure.__delitem__
   .. automethod:: objetto.bases.BaseMutableAttributeStructure.delete
   .. automethod:: objetto.bases.BaseMutableAttributeStructure.set
   .. automethod:: objetto.bases.BaseMutableAttributeStructure.update

Base Relationship Class
-----------------------
.. autoclass:: objetto.bases.BaseRelationship
   :members:
     types,
     subtypes,
     checked,
     module,
     factory,
     serialized,
     serializer,
     deserializer,
     represented,
     passthrough,

   .. automethod:: objetto.bases.BaseRelationship.__hash__
   .. automethod:: objetto.bases.BaseRelationship.__eq__
   .. automethod:: objetto.bases.BaseRelationship.__repr__
   .. automethod:: objetto.bases.BaseRelationship.__str__
   .. automethod:: objetto.bases.BaseRelationship.to_dict
   .. automethod:: objetto.bases.BaseRelationship.get_single_exact_type
   .. automethod:: objetto.bases.BaseRelationship.fabricate_value

Base Attribute Class
--------------------
.. autoclass:: objetto.bases.BaseAttribute
   :members:
     relationship,
     default,
     default_factory,
     module,
     required,
     changeable,
     deletable,
     finalized,
     abstracted,
     has_default,
     constant,

   .. automethod:: objetto.bases.BaseAttribute.__get__
   .. automethod:: objetto.bases.BaseAttribute.__hash__
   .. automethod:: objetto.bases.BaseAttribute.__eq__
   .. automethod:: objetto.bases.BaseAttribute.__repr__
   .. automethod:: objetto.bases.BaseAttribute.to_dict
   .. automethod:: objetto.bases.BaseAttribute.get_name
   .. automethod:: objetto.bases.BaseAttribute.get_value
   .. automethod:: objetto.bases.BaseAttribute.fabricate_default_value

Base Data Classes
-----------------
.. autoclass:: objetto.bases.BaseData
   :members: _state

   .. automethod:: objetto.bases.BaseData.__copy__

.. autoclass:: objetto.bases.BaseInteractiveData

.. autoclass:: objetto.bases.BaseAuxiliaryData
   :members:
     _relationship

   .. automethod:: objetto.bases.BaseAuxiliaryData._hash
   .. automethod:: objetto.bases.BaseAuxiliaryData._eq
   .. automethod:: objetto.bases.BaseAuxiliaryData.find_with_attributes

.. autoclass:: objetto.bases.BaseInteractiveAuxiliaryData

Base Object Classes
-------------------
.. autoclass:: objetto.bases.BaseObject
   :members:
     _state,
     _parent,
     _is_root,
     _children,
     _history,
     app,
     data,

   .. automethod:: objetto.bases.BaseObject.__copy__
   .. automethod:: objetto.bases.BaseObject._hash
   .. automethod:: objetto.bases.BaseObject._eq
   .. automethod:: objetto.bases.BaseObject._locate
   .. automethod:: objetto.bases.BaseObject._locate_data
   .. automethod:: objetto.bases.BaseObject._in_same_application
   .. automethod:: objetto.bases.BaseObject._batch_context()
   .. automethod:: objetto.bases.BaseObject.deserialize

.. autoclass:: objetto.bases.BaseMutableObject

.. autoclass:: objetto.bases.BaseAuxiliaryObject
   :members: _relationship

   .. automethod:: objetto.bases.BaseAuxiliaryObject.find_with_attributes

.. autoclass:: objetto.bases.BaseMutableAuxiliaryObject

Base Proxy Object Class
-----------------------
.. autoclass:: objetto.bases.BaseProxyObject
   :members:
     _obj,
     _state,
     _parent,
     _is_root,
     _children,
     _history,
     app,
     data,

   .. automethod:: objetto.bases.BaseProxyObject.__repr__
   .. automethod:: objetto.bases.BaseProxyObject.__hash__
   .. automethod:: objetto.bases.BaseProxyObject.__eq__
   .. automethod:: objetto.bases.BaseProxyObject.__len__
   .. automethod:: objetto.bases.BaseProxyObject.__iter__
   .. automethod:: objetto.bases.BaseProxyObject.__contains__
   .. automethod:: objetto.bases.BaseProxyObject._clear
   .. automethod:: objetto.bases.BaseProxyObject.find_with_attributes

Base Reaction Class
-------------------
.. autoclass:: objetto.bases.BaseReaction
   :members: priority

   .. automethod:: objetto.bases.BaseReaction.__call__
   .. automethod:: objetto.bases.BaseReaction.__get__
   .. automethod:: objetto.bases.BaseReaction.__hash__
   .. automethod:: objetto.bases.BaseReaction.__eq__
   .. automethod:: objetto.bases.BaseReaction.__repr__
   .. automethod:: objetto.bases.BaseReaction.to_dict
   .. automethod:: objetto.bases.BaseReaction.set_priority

Base Factory Class
------------------
.. autoclass:: objetto.bases.BaseFactory

   .. automethod:: __call__
   .. automethod:: __add__

Base Change Classes
-------------------
.. autoclass:: objetto.bases.BaseChange

   .. autoattribute:: objetto.bases.BaseChange.name
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.bases.BaseChange.obj
      :annotation: :  Data Attribute

.. autoclass:: objetto.bases.BaseAtomicChange

   .. autoattribute:: objetto.bases.BaseAtomicChange.old_state
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.bases.BaseAtomicChange.new_state
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.bases.BaseAtomicChange.old_children
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.bases.BaseAtomicChange.new_children
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.bases.BaseAtomicChange.history_adopters
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.bases.BaseAtomicChange.history
      :annotation: :  Data Attribute

Base Phase Enum
---------------
.. autoclass:: objetto.bases.Phase
   :members: PRE, POST
