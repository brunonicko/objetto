Factories (objetto.factories)
=============================

.. automodule:: objetto.factories

   .. autoclass:: objetto.factories.MultiFactory
      :members: factories

      .. automethod:: objetto.factories.MultiFactory.__call__
      .. automethod:: objetto.factories.MultiFactory.__add__

   .. autoclass:: objetto.factories.Integer
      :members:
        minimum,
        maximum,
        clamp_minimum,
        clamp_maximum,
        accepts_none,

      .. automethod:: objetto.factories.Integer.__call__

   .. autoclass:: objetto.factories.FloatingPoint
      :members:
        minimum,
        maximum,
        clamp_minimum,
        clamp_maximum,
        accepts_none,

      .. automethod:: objetto.factories.FloatingPoint.__call__

   .. autoclass:: objetto.factories.String
      :members: accepts_none

      .. automethod:: objetto.factories.String.__call__

   .. autoclass:: objetto.factories.RegexMatch
      :members: pattern, compiled_pattern

      .. automethod:: objetto.factories.RegexMatch.__call__

   .. autoclass:: objetto.factories.RegexSub
      :members: pattern, compiled_pattern, repl

      .. automethod:: objetto.factories.RegexSub.__call__

   .. autoclass:: objetto.factories.Curated
      :members: values

      .. automethod:: objetto.factories.Curated.__call__

   .. autoclass:: objetto.factories.Boolean

      .. automethod:: objetto.factories.Boolean.__call__