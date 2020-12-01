Bases
=====

Base Classes
------------
.. autoclass:: objetto.bases.Base
   :special-members:
     '__copy__',
     '__repr__',
     '__ne__',
     '__dir__',
   :members:
     _initializing,
.. autoclass:: objetto.bases.BaseHashable
   :members:
.. autoclass:: objetto.bases.BaseSized
   :members:
.. autoclass:: objetto.bases.BaseIterable
   :members:
.. autoclass:: objetto.bases.BaseContainer
   :members:

Base Decorators
---------------
.. autofunction:: objetto.bases.abstract_member
.. autofunction:: objetto.bases.final

Base Collection Classes
-----------------------
.. autoclass:: objetto.bases.BaseCollection
   :members:
.. autoclass:: objetto.bases.BaseProtectedCollection
   :members:
.. autoclass:: objetto.bases.BaseInteractiveCollection
   :members:
.. autoclass:: objetto.bases.BaseMutableCollection
   :members:
.. autoclass:: objetto.bases.BaseDict
   :members:
.. autoclass:: objetto.bases.BaseProtectedDict
   :members:
.. autoclass:: objetto.bases.BaseInteractiveDict
   :members:
.. autoclass:: objetto.bases.BaseMutableDict
   :members:
.. autoclass:: objetto.bases.BaseList
   :members:
.. autoclass:: objetto.bases.BaseProtectedList
   :members:
.. autoclass:: objetto.bases.BaseInteractiveList
   :members:
.. autoclass:: objetto.bases.BaseMutableList
   :members:
.. autoclass:: objetto.bases.BaseSet
   :members:
.. autoclass:: objetto.bases.BaseProtectedSet
   :members:
.. autoclass:: objetto.bases.BaseInteractiveSet
   :members:
.. autoclass:: objetto.bases.BaseMutableSet
   :members:

Base Object Class
-----------------
.. autoclass:: objetto.bases.BaseObject
   :members: _parent, data

Base Change Classes
--------------------
.. autoclass:: objetto.bases.BaseChange
   :members: name, obj
.. autoclass:: objetto.bases.BaseAtomicChange
   :members:
     name,
     obj,
     old_state,
     new_state,
     old_children,
     new_children,
     history_adopters,
     history,
