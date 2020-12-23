Constants (objetto.constants)
=============================

.. automodule:: objetto.constants

Action Execution Phases
-----------------------
.. autodata:: objetto.constants.PRE
.. autodata:: objetto.constants.POST

Special Values
--------------
.. autodata:: objetto.constants.DELETED
   :annotation: :  Special Value

   Special marker that represents a deleted value.
   Can be used when updating :class:`objetto.objects.Object` attributes or
   :class:`objetto.objects.DictObject` values.

Regular Expressions
-------------------

Lazy Import Paths Validation
****************************

.. autodata:: PRE_IMPORT_PATH_VALIDATION_REGEX

   Pre import path regex validation regex.

.. autodata:: objetto.constants.PARTIAL_IMPORT_PATH_REGEX

   Partial lazy import path regex.

.. autodata:: objetto.constants.RELATIVE_IMPORT_PATH_REGEX

   Relative lazy import path regex.

.. autodata:: objetto.constants.IMPORT_PATH_REGEX

   Full lazy import path regex.
