Reactions (objetto.reactions)
=============================

.. automodule:: objetto.reactions

   .. autodecorator:: objetto.reactions.reaction

   .. autoclass:: objetto.reactions.CustomReaction
      :members: func

      .. automethod:: objetto.reactions.CustomReaction.__call__
      .. automethod:: objetto.reactions.CustomReaction.to_dict

   .. autoclass:: objetto.reactions.UniqueAttributes
      :members: names, incrementers

      .. automethod:: objetto.reactions.UniqueAttributes.__call__
      .. automethod:: objetto.reactions.UniqueAttributes.to_dict

   .. autoclass:: objetto.reactions.LimitChildren
      :members: minimum, maximum

      .. automethod:: objetto.reactions.LimitChildren.__call__
      .. automethod:: objetto.reactions.LimitChildren.to_dict

   .. autoclass:: objetto.reactions.Limit
      :members: minimum, maximum

      .. automethod:: objetto.reactions.Limit.__call__
      .. automethod:: objetto.reactions.Limit.to_dict
