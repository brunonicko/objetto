Changes
=======

Batch Change
------------
.. autoclass:: objetto.changes.Batch

   .. autoattribute:: objetto.changes.Batch.name
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.Batch.metadata
      :annotation: :  Data Attribute

Attributes Change
-----------------
.. autoclass:: objetto.changes.Update

   .. autoattribute:: objetto.changes.Update.name
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.Update.old_values
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.Update.new_values
      :annotation: :  Data Attribute

Dictionary Changes
------------------
.. autoclass:: objetto.changes.DictUpdate

   .. autoattribute:: objetto.changes.DictUpdate.name
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.DictUpdate.old_values
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.DictUpdate.new_values
      :annotation: :  Data Attribute

List Changes
------------
.. autoclass:: objetto.changes.ListInsert

   .. autoattribute:: objetto.changes.ListInsert.name
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListInsert.index
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListInsert.last_index
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListInsert.stop
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListInsert.new_values
      :annotation: :  Data Attribute

.. autoclass:: objetto.changes.ListDelete

   .. autoattribute:: objetto.changes.ListDelete.name
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListDelete.index
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListDelete.last_index
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListDelete.stop
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListDelete.old_values
      :annotation: :  Data Attribute

.. autoclass:: objetto.changes.ListUpdate

   .. autoattribute:: objetto.changes.ListUpdate.name
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListUpdate.index
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListUpdate.last_index
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListUpdate.stop
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListUpdate.old_values
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListUpdate.new_values
      :annotation: :  Data Attribute

.. autoclass:: objetto.changes.ListMove

   .. autoattribute:: objetto.changes.ListMove.name
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListMove.index
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListMove.last_index
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListMove.stop
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListMove.target_index
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListMove.post_index
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListMove.post_last_index
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListMove.post_stop
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.ListMove.values
      :annotation: :  Data Attribute

Set Changes
-----------
.. autoclass:: objetto.changes.SetUpdate

   .. autoattribute:: objetto.changes.SetUpdate.name
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.SetUpdate.new_values
      :annotation: :  Data Attribute

.. autoclass:: objetto.changes.SetRemove

   .. autoattribute:: objetto.changes.SetRemove.name
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.changes.SetRemove.old_values
      :annotation: :  Data Attribute
