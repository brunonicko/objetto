Observers
=========

.. automodule:: objetto.observers

Action Observer Class
---------------------
.. autoclass:: objetto.observers.ActionObserver

   .. automethod:: objetto.observers.ActionObserver.__observe__
   .. automethod:: objetto.observers.ActionObserver.start_observing
   .. automethod:: objetto.observers.ActionObserver.stop_observing

Action Observer Token Class
---------------------------
.. autoclass:: objetto.observers.ActionObserverToken
   :members: observer

   .. automethod:: objetto.observers.ActionObserverToken.wait

Action Observer Exception Data
------------------------------
.. autoclass:: objetto.observers.ActionObserverExceptionData

   .. autoattribute:: objetto.observers.ActionObserverExceptionData.observer
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.observers.ActionObserverExceptionData.action
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.observers.ActionObserverExceptionData.phase
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.observers.ActionObserverExceptionData.exception_type
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.observers.ActionObserverExceptionData.exception
      :annotation: :  Data Attribute

   .. autoattribute:: objetto.observers.ActionObserverExceptionData.traceback
      :annotation: :  Data Attribute
