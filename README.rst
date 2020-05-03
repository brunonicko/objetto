Objetto
#######

`Objetto` is a framework for building data-centric Applications/APIs which can be easily
observed/interacted with through a graphical or non-graphical user interface.

.. note::
    `Objetto` is currently in alpha. Use it at your own risk!

.. note::
    `Objetto` is compatible with Python 2.7 and higher (including Python 3).
    Even though Python 2.7 is now deprecated, it is still widely in use by Visual
    Effects pipelines, which can benefit from `Objetto`.
    Therefore, support for it will be maintained until a full transition takes place.

Take a look at the `Examples`_ to see it in practice.

`Objetto` takes some inspiration from projects like:
  - `attrs <https://www.attrs.org/>`_
  - `Python 3 Data Classes <https://docs.python.org/3/library/dataclasses.html>`_
  - `pyrsistent <https://github.com/tobgu/pyrsistent/>`_
  - `PySignal <https://github.com/dgovil/PySignal>`_
  - `React <https://reactjs.org/>`_
  - `Flux <https://facebook.github.io/flux/>`_

Overview
********
`Objetto` provides an easy way to define a high-level mutable data structure referred to
as `Object`_, which offers features related to data access, consistency, validation, and
monitoring.

Hierarchy and Ownership
=======================
An object can be 'owned' by another object in a parent-children tree hierarchy.
This can help preventing them from being mistakenly re-used as data in an object other
than its owner (if that behavior is desired).

The parent-children hierarchy also provides a good way to structure your data, prevents
cycles, and eases processes like serialization and application-wide validation.

An object's hierarchy can be accessed through its `.hierarchy` property.

Schema & Validation
===================
Objects provide a variety of mechanisms to define schema and to validate your data.
The mantra here is that the client code using a well-written Application/API created
with `Objetto` should not be concerned about leaving it in a bad state.

One way to implement validation is to make use of the `value_type` and/or
`value_factory` parameters when defining `Attributes`_.

Event Emission
==============
Every time an object gets mutated, it will automatically emit events that describe its
mutation. Listeners can hook up to objects so they react when they receive those events.

This is useful for triggering reactive behaviors that are internal to the
Application/API, but also for external systems that interact with the objects, such as
graphical user interfaces, controllers, or even other external objects.

Each object type has a standardized set of event types that it emits, making it easy
to build generic listeners that react to different objects with similar interfaces.

An object's event emitter can be accessed through its `.events` property.
Event types can be imported from the `objetto.events` module.

Undo/Redo History
=================
Objetto has built-in support for a undo/redo command history. It takes care of managing
its validity for internal data changes by flushing itself automatically when necessary,
and it is extremely easy to implement.

A history can be added to an object by adding a `history_attribute` to its definition.
Accessing that attribute from an object's instance will give you the `History` itself.

Object
======
Objects are the building blocks of any `Objetto` Application/API.

`objetto.Object` is the most important class, and the one you will probably be dealing
with the most. Its internal state is curated by `Attributes`_ defined in sub-classes.

.. note::
    There are other object types that are used internally by attribute factories, known
    as containers, such as: `ListObject`, `DictObject`, and `SetObject`.
    These classes can be imported from the `objetto.objects` module if you want to
    create advanced custom attribute factories or define custom behaviors.

Attributes
==========
Attributes define the schema of an object class. Some of them can be delegated, meaning
that they can behave as properties.
Here are some of the attribute factories that `Objetto` offers:

  - attribute
  - history_attribute
  - constant_attribute
  - permanent_attribute
  - protected_attribute_pair
  - list_attribute
  - protected_list_attribute_pair
  - dict_attribute
  - protected_dict_attribute_pair
  - set_attribute
  - protected_set_attribute_pair
  - dependencies (decorator to define dependencies for an attribute's delegate)

Value Factories
===============
Value factories can be used for conforming/validating an input value when setting an
attribute. They can be imported from `objetto.factories`.
Here are some of the value factories that `Objetto` offers:

  - integer
  - floating_point
  - regex_match
  - regex_sub
  - curated

Reactions
=========
Reactions are pre-defined recipes that listen to events from container objects, reacting
to them in a certain way.
Here are some of the reactions that `Objetto` offers:

  - unique_attributes
  - limit


Examples
========
Here's how to define a simple `Person` object class with two string attributes.
Notice how we are using the `value_type` parameter to implement type checking.

.. code:: python

    >>> from objetto import Object, attribute
    >>>
    >>> class Person(Object):
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

    >>> from objetto import dependencies
    >>> from objetto.factories import regex_match
    >>>
    >>> NAME_REGEX = r"^[A-Z][a-zA-Z]*$"
    >>>
    >>> class Person(Object):
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

Now, let's start creating a hierarchy of objects by creating the class `Father`,
which extends `Person` by defining children in a `list_attribute`.
Not how we used a `unique_attributes` reaction in order to enforce a validation that
prevents siblings from having the same full name.

.. code:: python

    >>> from objetto import list_attribute
    >>> from objetto.reactions import unique_attributes
    >>>
    >>> class Father(Person):
    ...     children = list_attribute(
    ...         value_type=Person,
    ...         reaction=unique_attributes("full_name"),
    ...         parent=True
    ...     )
    ...
    >>> elizabeth = Person("Elizabeth Leigh")
    >>> ada = Person("Ada Byron")
    >>> clara = Person("Clara Byron")
    >>>
    >>> george = Father("George Byron")
    >>> george.children.append(elizabeth, ada, clara)
    >>>
    >>> george_children = george.children
    >>> print(elizabeth.hierarchy.parent is george.children)
    True
    >>> print(george.children.hierarchy.parent is george)
    True

Let's define an object that will represent the top of the hierarchy and implement a
history so we can utilize undo/redo capabilities for all of its members.

.. code:: python

    >>> from objetto import history_attribute
    >>>
    >>> class Family(Object):
    ...     history = history_attribute()
    ...     father = attribute(value_type=Father, parent=True)
    ...
    ...     def __init__(self, father):
    ...         self.father = father
    ...
    >>> family = Family(Father("George Byron"))
    >>>
    >>> elizabeth = Person("Elizabeth Leigh")
    >>> ada = Person("Ada Byron")
    >>> clara = Person("Clara Byron")
    >>>
    >>> family.father.children.append(elizabeth)
    >>> family.father.children.append(ada)
    >>> family.father.children.append(clara)
    >>> print(len(family.father.children))
    3
    >>> family.history.undo()
    >>> print(len(family.father.children))
    2
    >>> family.history.undo()
    >>> print(len(family.father.children))
    1
    >>> family.history.undo()
    >>> print(len(family.father.children))
    0
