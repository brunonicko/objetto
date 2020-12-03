Objects
=======

Object Class
------------
.. autoclass:: objetto.objects.Object
   :members: _parent

Auxiliary Object Classes
------------------------
.. autoclass:: objetto.objects.DictObject
   :members: _parent
.. autoclass:: objetto.objects.ListObject
   :members: _parent
.. autoclass:: objetto.objects.SetObject
   :members: _parent

Attribute Descriptors
---------------------
.. autofunction:: objetto.objects.attribute
.. autofunction:: objetto.objects.dict_attribute
.. autofunction:: objetto.objects.list_attribute
.. autofunction:: objetto.objects.set_attribute

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
