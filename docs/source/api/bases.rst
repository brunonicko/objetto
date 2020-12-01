Bases
=====

Objects
-------
.. autoclass:: objetto.bases.BaseObject
   :members: _parent, data

Changes
-------
.. autoclass:: objetto.bases.BaseChange
   :members: name, obj

.. autoclass:: objetto.bases.BaseAtomicChange
   :members:
     old_state,
     new_state,
     old_children,
     new_children,
     history_adopters,
     history,
