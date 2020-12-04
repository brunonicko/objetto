History
=======

.. automodule:: objetto.history

   .. autoclass:: objetto.history.HistoryObject

      .. autoattribute:: objetto.history.HistoryObject.size
         :annotation: :  Attribute
      .. autoattribute:: objetto.history.HistoryObject.executing
         :annotation: :  Attribute
      .. autoattribute:: objetto.history.HistoryObject.undoing
         :annotation: :  Attribute
      .. autoattribute:: objetto.history.HistoryObject.redoing
         :annotation: :  Attribute
      .. autoattribute:: objetto.history.HistoryObject.index
         :annotation: :  Attribute
      .. autoattribute:: objetto.history.HistoryObject.changes
         :annotation: :  Attribute
      .. autoattribute:: objetto.history.HistoryObject.current_batches
         :annotation: :  Attribute

      .. automethod:: objetto.history.HistoryObject.set_index
      .. automethod:: objetto.history.HistoryObject.undo_all
      .. automethod:: objetto.history.HistoryObject.redo_all
      .. automethod:: objetto.history.HistoryObject.redo
      .. automethod:: objetto.history.HistoryObject.undo
      .. automethod:: objetto.history.HistoryObject.flush
      .. automethod:: objetto.history.HistoryObject.flush_redo
      .. automethod:: objetto.history.HistoryObject.in_batch
      .. automethod:: objetto.history.HistoryObject.format_changes

   .. autoclass:: objetto.history.BatchChanges

      .. autoattribute:: objetto.history.BatchChanges.change
         :annotation: :  Attribute
      .. autoattribute:: objetto.history.BatchChanges.name
         :annotation: :  Attribute
      .. autoattribute:: objetto.history.BatchChanges.changes
         :annotation: :  Attribute
      .. autoattribute:: objetto.history.BatchChanges.closed
         :annotation: :  Attribute

      .. automethod:: objetto.history.BatchChanges.format_changes
