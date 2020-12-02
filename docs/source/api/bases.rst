Bases
=====

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

Base Decorators
---------------
.. autofunction:: objetto.bases.final
.. autofunction:: objetto.bases.init

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

Base Data Class
---------------
.. autoclass:: objetto.bases.BaseData

Base Object Class
-----------------
.. autoclass:: objetto.bases.BaseObject

Base Change Classes
--------------------
.. autoclass:: objetto.bases.BaseChange
   :members:
     name,
     obj,

.. autoclass:: objetto.bases.BaseAtomicChange
   :members:
     old_state,
     new_state,
     old_children,
     new_children,
     history_adopters,
     history,
