Modelo
######

.. warning::
    `Modelo` is currently in alpha phase. Use it at your own risk!
    Expect to see more updates in this documentation and more tests soon.

`Modelo` is a framework for building data-centric Applications/APIs which can be easily
interacted with through a graphical or non-graphical user interface.

`Modelo` is compatible with Python 2.7 and higher (including Python 3).
Even though Python 2.7 is now deprecated, it is still widely in use by Visual Effects
pipelines, which can benefit from APIs/tools written with `Modelo` and
`PyQt <https://riverbankcomputing.com/software/pyqt/intro>`_/
`PySide <https://www.qt.io/qt-for-python>`_, for example. Therefore, support for it will
be maintained until a full transition takes place.

Take a look at the `Examples`_ to see it in practice.

`Modelo` takes some inspiration from projects like:
  - `attrs <https://www.attrs.org/>`_
  - `Python 3 Data Classes <https://docs.python.org/3/library/dataclasses.html>`_
  - `pyrsistent <https://github.com/tobgu/pyrsistent/>`_
  - `PySignal <https://github.com/dgovil/PySignal>`_
  - `React <https://reactjs.org/>`_
  - `Flux <https://facebook.github.io/flux/>`_

Overview
********
`Modelo` provides an easy way to define mutable data structures known as `Models`_,
which offer features to control data access, consistency, validation, and monitoring.

Hierarchy and Ownership
=======================
A model can be 'owned' by another model in a parent-children hierarchical relationship.
This can help preventing them from being mistakenly re-used as data in more than one
model, since they are mutable objects.

The parent-children hierarchy also provides a good way to structure your data, prevents
cycles, and eases processes like serialization and application-wide validation.

Schema & Validation
===================
Models provide a variety of mechanisms to define schema and to validate your data.
The mantra here is that the client code using an Application/API created with `Modelo`
should not be concerned about leaving it in a bad state.

Event Emission
==============
Every time a model gets mutated, it will automatically emit events that describe its
mutation. Listeners can hook up to models so they react when they receive those events.

This is useful for triggering reactive behaviors that are internal to the
Application/API, but also for external systems that interact with the models, such as
graphical user interfaces, controllers, or even other external models.

Each model type has a standardized set of event types that it emits, making it easy
to build generic listeners that react to different models with similar interfaces.

Undo/Redo History
=================
Modelo has built-in support for a undo/redo command history. It takes care of managing
its validity for internal data changes by flushing itself automatically when necessary,
so it is ridiculously easy to implement.

Models
======
Models are the building blocks of any `Modelo` Application/API. Simply put, they all
share the features described above, but each model type has a different interface for
holding and providing access to its state/data. You will notice that those different
interfaces resemble generic Python interfaces like objects, lists, dictionaries and
sets. The idea is that, although they have all those features under the hood, client
code interaction with them should feel very familiar and pythonic.

Models can be imported from the `modelo.models` module.

Abstract Model
--------------

modelo.models.Model
^^^^^^^^^^^^^^^^^^^
Abstract base class from which all other model types inherit from.
This cannot be instantiated, but provides the basic interface for accessing the
`hierarchy` property, `events` property, and `_batch context` context manager
(for undo/redo operations).

Container Models
----------------
modelo.models.sequence.SequenceModel
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

modelo.models.sequence.MutableSequenceModel
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

modelo.models.sequence.SequenceProxyModel
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

modelo.models.mapping.MappingModel
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

modelo.models.mapping.MutableMappingModel
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

modelo.models.mapping.MappingProxyModel
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

modelo.models.set.SetModel
^^^^^^^^^^^^^^^^^^^^^^^^^^

modelo.models.set.MutableSetModel
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

modelo.models.set.SetProxyModel
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Object Model
------------

modelo.models.ObjectModel
^^^^^^^^^^^^^^^^^^^^^^^^^

Attributes
==========


Examples
========
Here's how to define a simple `Person` object model class with two string attributes.
Notice how we are using the `value_type` parameter to implement type checking.

.. code:: python

    >>> from modelo.models import ObjectModel
    >>> from modelo.attributes import attribute
    >>>
    >>> class Person(ObjectModel):
    ...     first_name = attribute(value_type=str)
    ...     last_name = attribute(value_type=str)
    ...
    ...     def __init__(self, first_name, last_name):
    ...         self.first_name = first_name
    ...         self.last_name = last_name
    ...
    >>> person = Person("George", "Byron")
    >>> print(person)
    <Person first_name='George', last_name='Byron'>

Let's make it a little bit more complex by adding a `full_name` delegated attribute and
a regex validation `value_factory` for `first_name` and `last_name` attributes.

.. code:: python

    >>> from modelo.models import ObjectModel
    >>> from modelo.attributes import attribute, constant_attribute, dependencies
    >>> from modelo.factories import regex_match
    >>>
    >>> NAME_REGEX = r"^[A-Z][a-zA-Z]*$"
    >>>
    >>> class Person(ObjectModel):
    ...     first_name = attribute(value_factory=regex_match(NAME_REGEX))
    ...     last_name = attribute(value_factory=regex_match(NAME_REGEX))
    ...     full_name = attribute(value_type=str, delegated=True)
    ...
    ...     @full_name.getter
    ...     @dependencies(gets=(first_name, last_name))
    ...     def full_name(self):
    ...         return " ".join((self.first_name, self.last_name))
    ...
    ...     @full_name.setter
    ...     @dependencies(sets=(first_name, last_name))
    ...     def full_name(self, full_name):
    ...         self.first_name, self.last_name = full_name.split()
    ...
    ...     def __init__(self, full_name):
    ...         self.full_name = full_name
    ...
    >>> person = Person("George Byron")
    >>> print(person)
    <Person first_name='George', full_name='George Byron', last_name='Byron'>
    >>>
    >>> person.first_name = "Ada"
    >>> print(person)
    <Person first_name='Ada', full_name='Ada Byron', last_name='Byron'>
    >>>
    >>> person.full_name = "Ada Lovelace"
    >>> print(person)
    <Person first_name='Ada', full_name='Ada Lovelace', last_name='Lovelace'>

Now, let's start creating a hierarchy of models by creating the class `FamilyMember`,
which extends `Person` by defining children in a `sequence_attribute`.

.. code:: python

    >>> from modelo.attributes import sequence_attribute
    >>> from modelo.reactions import unique_attributes
    >>>
    >>> class FamilyMember(Person):
    ...     children = sequence_attribute(
    ...         value_type=Person,
    ...         reaction=unique_attributes("full_name"),
    ...         parent=True
    ...     )
    ...
    >>> elizabeth = Person("Elizabeth Leigh")
    >>> ada = Person("Ada Byron")
    >>> clara = Person("Clara Byron")
    >>>
    >>> george = Person("George Byron")
    >>> george.children.append(elizabeth, ada, clara)
    >>>
    >>> print(elizabeth.hierarchy.parent)
    <Person first_name='George', full_name='George Byron', last_name='Byron'>
