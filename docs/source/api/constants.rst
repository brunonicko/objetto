Constants
=========

Action Execution Phases
-----------------------
.. autodata:: objetto.constants.PRE
.. autodata:: objetto.constants.POST

Special Values
--------------
.. autoattribute:: objetto.constants.DELETED

   Special marker that represents a deleted value.
   Can be used when updating :class:`objetto.objects.Object` attributes or
   :class:`objetto.objects.DictObject` values.

Regular Expressions
-------------------

Lazy Import Paths Validation
****************************
.. autoattribute:: objetto.constants.PARTIAL_IMPORT_PATH_REGEX

   Partial lazy import path regex.

.. autoattribute:: objetto.constants.RELATIVE_IMPORT_PATH_REGEX

   Relative lazy import path regex.

.. autoattribute:: objetto.constants.IMPORT_PATH_REGEX

   Full lazy import path regex.
