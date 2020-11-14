Objetto
=======
.. image:: https://github.com/brunonicko/objetto/workflows/MyPy/badge.svg
    :target: https://github.com/brunonicko/objetto/actions?query=workflow%3AMyPy

.. image:: https://github.com/brunonicko/objetto/workflows/Lint/badge.svg
    :target: https://github.com/brunonicko/objetto/actions?query=workflow%3ALint

.. image:: https://github.com/brunonicko/objetto/workflows/Tests/badge.svg
    :target: https://github.com/brunonicko/objetto/actions?query=workflow%3ATests

.. image:: https://badge.fury.io/py/objetto.svg
    :target: https://pypi.org/project/objetto/

`Objetto` is an object-oriented framework for building smart applications and APIs.

Overview
--------
`Objetto` allows for the creation of an `Application`_ that consists of high-level
mutable structures referred to as `Objects <Object_>`_.

  - `Objects <Object_>`_ are associated with an `Application`_ when initialized.
  - `Objects <Object_>`_ are part of a parent-children `Hierarchy`_ tree.
  - `Objects <Object_>`_ have their schema defined by `Attributes <Attribute>`_.
  - `Objects <Object_>`_ encase an immutable 'mirror' version of themselves referred to
    as `Data`_.
  - `Objects <Object_>`_ will send an `Action`_ for every `Change`_ that happens in
    their state to themselves, their parent, and grandparents.
  - `Objects <Object_>`_ can perform `Reactions <Reaction>`_ in response to `Actions
    <Action>`_ received from themselves, their children, and grandchildren.
  - `Objects <Object_>`_ can be observed by external `Observers <Observer>`_ such as GUI
    widgets or even other `Objects <Object_>`_ in a different `Application`_.
  - `Objects <Object_>`_ feature built-in human-readable `Serialization`_ and
    `Deserialization`_ capabilities.
  - `Objects <Object_>`_ can be automatically tracked by a `History`_, which allows for
    easy and selective undo/redo functionality.

Application
-----------
An `Application`_ oversees all `Objects <Object_>`_ that are meant to work together. It
provides different contexts for managing and keeping track of their `Changes <Change>`_.

`Objects <Object_>`_ that are part of different `Applications <Application>`_ see each
other as regular values and can never be part of the same `Hierarchy`_.

**Example**: Instantiate a new `Application`_.

.. code:: python

    >>> from objetto.applications import Application

    >>> app = Application()  # instantiate a new application

Read Context
************
While in a `Read Context`_, all `Objects <Object>`_ in the `Application`_ are guaranteed
not to be modified.

**Example**: Enter a `Read Context`_.

.. code:: python

    >>> from objetto.applications import Application

    >>> app = Application()
    >>> with app.read_context():
    >>>     pass  # read access only, no changes allowed

Write Context
*************
While in a `Write Context`_, `Actions <Action>`_ are only sent internally until the
outermost `Write Context`_ exits without errors, after which external `Observers
<Observer>`_ will then receive them.

If an unhandled exception gets raised, all changes are reverted to the moment the
context was entered, and external `Observers <Observer>`_ will not receive `Actions
<Action>`_. This behavior is similar to `transactions` in a database.

.. note::
    You cannot enter a `Write Context`_ while in a `Read Context`_.

**Example**: Enter a `Write Context`_.

.. code:: python

    >>> from objetto.applications import Application

    >>> app = Application()
    >>> with app.write_context():
    >>>     pass  # send actions to external observers only at the end, revert if errors

Object
------
`Objects <Object_>`_ are the building blocks of an `Application`_. An `Object`_ is
mutable, has state, and can be a parent and/or a child of another `Object`_.

The class `objetto.objects.Object` is the most important `Object`_ class, and the one
we will probably be dealing with the most. It is curated by `Attributes <Attribute>`_
defined in subclasses.

To define our own `Object`_, we have to inherit from `objetto.objects.Object` and use
`Attributes <Attribute>`_ to define its schema. You need to instantiate it with an
`Application`_, which can later be accessed through the `.app` property:

**Example**: Make our own `Object`_ subclass and instantiate it.

.. code:: python

    >>> from objetto.applications import Application
    >>> from objetto.objects import Object
    >>> from objetto.attributes import attribute

    >>> class Hobby(Object):  # inherit from objetto.objects.Object
    ...     description = attribute(str)  # example attribute called 'description'
    ...
    >>> app = Application()
    >>> hobby = Hobby(app, description="biking")  # instantiate our object
    >>> hobby.app is app
    True

Auxiliary Object
****************
Usually we don't have to deal with `Auxiliary Objects <Auxiliary Object>`_ since we
will probably be using `Auxiliary Attributes <Auxiliary Attribute>`_ instead, but they
can be used if advanced behavior is desired.

These are special types of `Objects <Object>`_ that are used internally by `Auxiliary
Attributes <Auxiliary Attribute>`_ to contain multiple values in different ways:

  - `ListObject`
  - `DictObject`
  - `SetObject`
  - `InteractiveListObject`
  - `InteractiveDictObject`
  - `InteractiveSetObject`

The interactive versions of `Auxiliary Objects <Auxiliary Object>`_ expose the mutable
methods as public, whereas the non-interactive ones have them as protected (their names
start with an underscore).

When subclassing, the `Auxiliary Object`_ schema is defined by a single `Relationship`
assigned to the class variable `_relationship`.

**Example**: Make a subclass of `InteractiveListObject` with a custom `Relationship`.

.. code:: python

    >>> from objetto.applications import Application
    >>> from objetto.objects import Object, InteractiveListObject, Relationship
    >>> from objetto.attributes import attribute

    >>> class Hobby(Object):
    ...     description = attribute(str)
    ...
    >>> class HobbiesList(InteractiveListObject):  # inherit from InteractiveListObject
    ...     _relationship = Relationship(Hobby)  # define relationship with value type
    ...
    >>> app = Application()
    >>> hobby_a = Hobby(app, description="biking")
    >>> hobby_b = Hobby(app, description="gaming")
    >>> hobbies = HobbiesList(app)  # make new instance
    >>> hobbies.extend((hobby_a, hobby_b))  # extend list object with 'hobby' objects

Batch Context
*************
An `Object`_ can enter a `Batch Context`_, which will group multiple `Changes <Change>`_
happening to itself and/or to other `Objects <Object>`_ into one single entry in the
associated `History`_.

A special `Action`_ carrying the provided `Batch Change`_ will be sent when entering
(`PRE` `Phase`_) and when exiting the context (`POST` `Phase`_).

**Example**: Enter a `Batch Context`_.

.. code:: python

    >>> from objetto.applications import Application
    >>> from objetto.objects import Object, history_descriptor
    >>> from objetto.attributes import attribute
    >>> from objetto.changes import BatchChange

    >>> class Hobby(Object):
    ...     description = attribute(str)
    ...
    >>> class Person(Object):
    ...     history = history_descriptor()  # specify a history
    ...     name = attribute(str)
    ...     hobby = attribute(Hobby)  # history will propagate by default
    ...
    ...     def set_info(self, name, hobby_description):
    ...         change = BatchChange(name="Set Person Info")  # custom 'change'
    ...         with self._batch_context(change):  # enter batch context, group changes
    ...             self.name = name  # single change
    ...             self.hobby.description = hobby_description  # single change
    ...
    >>> app = Application()
    >>> hobby = Hobby(app, description="sailing")
    >>> person = Person(app, name="Albert", hobby=hobby)
    >>> print(person.name, person.hobby.description)
    ('Albert', 'sailing')
    >>> person.set_info("Einstein", "physics")  # batch change
    >>> print(person.name, person.hobby.description)
    ('Einstein', 'physics')
    >>> person.history.undo()  # single undo
    >>> print(person.name, person.hobby.description)
    ('Albert', 'sailing')

Attribute
---------
`Attributes <Attribute>`_ describe the schema of an `Object`_. When defining one, we can
specify relationship parameters between the `Object`_ that owns it and the value being
stored, such as a `Value Type`_, `Hierarchy`_ settings, `History`_ propagation,
`Serialization`_ and `Deserialization`_ options, etc.

**Example**: Define custom `Objects <Object_>`_ with multiple `Attributes <Attribute>`_.

.. code:: python

    >>> from objetto.applications import Application
    >>> from objetto.objects import Object
    >>> from objetto.attributes import attribute

    >>> class Hobby(Object):
    ...     description = attribute(str)  # specify value type, only takes strings
    ...
    >>> class Person(Object):
    ...     name = attribute(str, default="Phil")  # specify a default value
    ...     hobby = attribute(Hobby)  # specify value type, only takes 'Hobby' objects
    ...     busy = attribute(bool, serialized=False, default=False)  # not serialized
    ...
    >>> app = Application()
    >>> hobby = Hobby(app, description="biking")
    >>> person = Person(app, hobby=hobby)
    >>> print(person.name)
    'Phil'
    >>> person.name = "Gaimon"
    >>> print(person.name)
    'Gaimon'

Value Type
**********
When defining an `Attribute`_, we can specify its `Value Type`_. This is useful for
runtime type checking, but also for informing `Objetto` about the schema of our
`Objects <Object>`_, which is needed for `Serialization`_ and `Deserialization`_.

Import path strings are also accepted, and they will be imported lazily during runtime.
It's possible to use multiple `Value Types <Value Type>`_ by specifying them in a tuple.

The types are interpreted 'exactly' by default. This means they are checked and compared
by identity, so instances of subclasses are not accepted. However that behavior can be
changed by specifying `exact=False` when we define an `Attribute`_.

If `None` is also accepted as a value, we can specify `optional=True`.

.. note::
    In order for `Serialization`_ and `Deserialization`_ to work properly, a single
    exact `Value Type`_ needs to be specified, otherwise custom `serializer` and
    `deserializer` functions are required. The exception to this rule is when we specify
    exact, but multiple basic types like `int`, `float`, `str`, and/or `bool`.

    Specifying `optional=True` does not affect the `Serialization`_ and
    `Deserialization`_.

**Example**: Define the `Value Types <Value Type>`_ of `Attributes <Attribute>`_.

.. code:: python

    >>> from objetto.objects import Object
    >>> from objetto.attributes import attribute

    >>> class Person(Object):
    ...     name = attribute(str)  # single exact value type
    ...     child = attribute("Person", optional=True)  # import path, also accepts None
    ...     job = attribute("jobs.Job") # import path string with module path
    ...     money = attribute((int, float))  # multiple basic types
    ...     _status = attribute(serialized=False)  # no value type, not serialized
    ...     _pet = attribute(
    ...         "pets.AbstractPet", exact=False, serialized=False
    ...     )  # accepts instances of 'AbstractPet' subclasses, not serialized

Value Factory
*************
An `Attribute`_ can conform and/or verify new values by using a `Value Factory`_, which
is simply a function or callable that takes the newly input value, does something to it,
and then return the actual value that gets stored in the `Object`_.

You can use simple functions or even basic types as `Value Factories <Value Factory>`_,
although `Objetto` offers some very useful functions that make advanced `Value Factories
<Value Factory>`_ on the fly according to configurable parameters.

Here are some of those useful functions, which can be imported from `objetto.factories`:

  - `integer`
  - `floating_point`
  - `regex_match`
  - `regex_sub`
  - `curated`

**Example**: Use `Value Factories <Value Factory>`_ to conform/verify attribute values.

.. code:: python

    >>> from objetto.objects import Object
    >>> from objetto.attributes import attribute
    >>> from objetto.factories import regex_match, integer, curated

    >>> class Person(Object):
    ...     name = attribute(str, factory=regex_match(r"^[a-z ,.'-]+$"))  # regex match
    ...     age = attribute(int, factory=integer(minimum=1))  # minimum integer
    ...     pet = attributes(str, factory=curated(("cat", "dog"))) # curated values
    ...     job = attribute(str, factory=str)  # force input to string

Auxiliary Attribute
*******************
These are special `Attributes <Attribute>`_ that will internally create an `Auxiliary
Object`_ to hold multiple values instead of just one.

The `Auxiliary Attributes <Auxiliary Attribute>`_ are:

  - `list_attribute`
  - `dict_attribute`
  - `set_attribute`

.. code:: python

    >>> from objetto.applications import Application
    >>> from objetto.objects import Object
    >>> from objetto.attributes import attribute

    >>> class Hobby(Object):
    ...     description = attribute(str)
    ...
    >>> class Person(Object):
    ...     hobbies = list_attribute(Hobby, child=True)  # holds multiple 'hobbies'
    ...
    >>> app = Application()
    >>> hobby_a = Hobby(app, description="biking")
    >>> hobby_b = Hobby(app, description="gaming")
    >>> person = Person(app, hobbies=(hobby_a, hobby_b))  # initialize with iterable
    >>> person.hobbies[0] is hobby_a
    True

Delegated Attribute
*******************
`Attributes <Attributes>`_ can have delegate methods that will get, set and/or delete
the values of other `Attributes <Attributes>`_ in the same `Object`_.

When defining delegates, you have to specify which `Attributes <Attributes>`_ they will
interact with as `dependencies`.

.. note::
    The results of delegate methods are cached, and because of that they should never
    rely on mutable external objects. Think of delegates as 'pure functions' in the
    context of the `Object`_ they belong to.

    If an `Attribute`_ value needs to change according to external factors,
    `Reactions <Reaction>`_ or regular methods could be used instead of delegates.

**Example**: Define a `Delegated Attribute`_ with a `getter` and a `setter`.

.. code:: python

    >>> from objetto.applications import Application
    >>> from objetto.objects import Object
    >>> from objetto.attributes import attribute

    >>> class Person(Object):
    ...     first_name = attribute(str)
    ...     last_name = attribute(str)
    ...     name = attribute(str, delegated=True)  # delegated attribute
    ...
    ...     @name.getter  # define a getter
    ...     @dependencies(gets=(first_name, last_name))  # specify dependencies
    ...     def name(self):
    ...         return self.first_name + " " + self.last_name
    ...
    ...     @name.setter  # define a setter
    ...     @dependencies(sets=(first_name, last_name))  # specify dependencies
    ...     def name(self, value):
    ...         self.first_name, self.last_name = value.split()
    ...
    >>> app = Application()
    >>> person = Person(app, first_name="Katherine", last_name="Johnson")
    >>> print(person.name)
    'Katherine Johnson'
    >>> person.name = "Grace Hopper"
    >>> print(person.name)
    'Grace Hopper'
    >>> print(person.first_name)
    'Grace'
    >>> print(person.last_name)
    'Hopper'

Attribute Helper
****************
There are patterns that come up very often when defining `Attributes <Attribute>`_.
Instead of re-writing those patterns everytime, it's possible to use helper functions
known as `Attribute Helpers <Attribute Helper>`_ to get the same effect.

Here are some examples of `Attribute Helpers <Attribute Helper>`_:

  - `constant_attribute`
  - `permanent_attribute`
  - `protected_attribute_pair`
  - `protected_list_attribute_pair`
  - `protected_dict_attribute_pair`
  - `protected_set_attribute_pair`

Hierarchy
---------
An `Object`_ can have one parent and/or multiple children.

The parent-children hierarchy is central to the way `Objetto` works, as it provides an
elegant way to structure our `Application`_. It's essential for features like:

  - Preventing cyclic references: `Objects <Object_>`_ can only have one parent
  - Immutable `Data`_ 'mirroring': The `Data`_ structure will replace child `Objects
    <Object_>`_ with their `Data`_ according to the hierarchy
  - Human-readable `Serialization`_: The `.serialize()` and `.deserialize(...)` methods
    utilize the hierarchy to find the correct classes
  - `Action`_ sending and subsequent `Reaction`_\ response: `Actions <Action>`_ will
    propagate from where the `Change`_ happened all the way up the hierarchy to the
    topmost grandparent, triggering `Reactions <Reaction>`_ along the way
  - Automatic `History`_ propagation: Children can automatically be assigned to the same
    `History`_ of the parent if desired.

.. note::
    The hierarchical relationship can be turned off selectively at the expense of those
    features by specifying `child=False` when we define an `Attribute`_.

    Also note that the hierarchical relationship will only work between
    `Objects <Object_>`_ sharing the same `Application`_.

**Example**: Access `._parent` and `._children` properties.

.. code:: python

    >>> from objetto.applications import Application
    >>> from objetto.objects import Object
    >>> from objetto.attributes import attribute

    >>> class Hobby(Object):
    ...     description = attribute(str)
    ...
    >>> class Person(Object):
    ...     name = attribute(str)
    ...     hobby = attribute(Hobby, child=True)
    ...
    >>> app = Application()
    >>> hobby = Hobby(app, description="animation")
    >>> person = Person(app, name="Hayao", hobby=hobby)
    >>> hobby._parent is person  # 'person' is the parent of 'hobby'
        True
    >>> hobby in person._children  # 'hobby' is a child of 'person'
        True

Data
----
`Data`_ are analog structures to `Objects <Object_>`_, but they are immutable.

Everytime an `Object`_ changes, their internal `Data`_ and all of its parent's and
grandparents' `Data`_ get replaced with a new one that reflects those changes.

The `Data`_ for an `Object`_ can be accessed through its `.data` property.

**Example**: Access internal `Data`_ of an `Object`_.

.. code:: python

    >>> from objetto.applications import Application
        >>> from objetto.objects import Object
        >>> from objetto.attributes import attribute
        >>> from objetto.data import Data

        >>> class Hobby(Object):
        ...     description = attribute(str)
        ...
        >>> class Person(Object):
        ...     hobby = attribute(Hobby)
        ...
        >>> app = Application()
        >>> hobby = Hobby(app, description="biking")
        >>> person = Person(app, hobby=hobby)
        >>> isinstance(person.data, Data)  # access a person's data
        True
        >>> isinstance(person._data.hobby, Data)  # hobby's data is in it
        True

    It's also possible to use
        >>> from objetto.objects import Object
        >>> from objetto.attributes import attribute
        >>> from objetto.data import Data

        >>> class Hobby(Object):
        ...     description = attribute(str)
        ...
        >>> class Person(Object):
        ...     hobby = attribute(Hobby)
        ...
        >>> app = Application()
        >>> hobby = Hobby(app, description="biking")
        >>> person = Person(app, hobby=hobby)
        >>> isinstance(person.data, Data)  # access a person's data
        True
        >>> isinstance(person._data.hobby, Data)  # hobby's data is in it
        True

    It's also possible to use
        >>> from objetto.objects import Object
        >>> from objetto.attributes import attribute
        >>> from objetto.data import Data

        >>> class Hobby(Object):
        ...     description = attribute(str)
        ...
        >>> class Person(Object):
        ...     hobby = attribute(Hobby)
        ...
        >>> app = Application()
        >>> hobby = Hobby(app, description="biking")
        >>> person = Person(app, hobby=hobby)
        >>> isinstance(person._data, Data)  # access a person's data
        True
        >>> isinstance(person.data.hobby, Data)  # hobby's data is in it
        True

    It's also possible to use
        >>> from objetto.objects import Object
        >>> from objetto.attributes import attribute
        >>> from objetto.data import Data

        >>> class Hobby(Object):
        ...     description = attribute(str)
        ...
        >>> class Person(Object):
        ...     hobby = attribute(Hobby)
        ...
        >>> app = Application()
        >>> hobby = Hobby(app, description="biking")
        >>> person = Person(app, hobby=hobby)
        >>> isinstance(person._data, Data)  # access a person's data
        True
        >>> isinstance(person.data.hobby, Data)  # hobby's data is in it
        True

    It's also possible to use
    >>> from objetto.objects import Object
    >>> from objetto.attributes import attribute
    >>> from objetto.data import Data

    >>> class Hobby(Object):
    ...     description = attribute(str)
    ...
    >>> class Person(Object):
    ...     hobby = attribute(Hobby)
    ...
    >>> app = Application()
    >>> hobby = Hobby(app, description="biking")
    >>> person = Person(app, hobby=hobby)
    >>> isinstance(person._data, Data)  # access a person's data
    True
    >>> isinstance(person._data.hobby, Data)  # hobby's data is in it
    True

It's also possible to use `Data`_ on its own, without an encasing `Object`_.

**Example**: Using `Data`_ on its own.

.. code:: python

    >>> from objetto.data import Data
    >>> from objetto.data_attributes import data_attribute

    >>> class HobbyData(Data):  # inherit from Data
    ...     description = data_attribute(str)  # use data attributes
    ...
    >>> class PersonData(Data):
    ...     hobby = data_attribute(HobbyData, optional=True)  # specify data types
    ...
    >>> hobby_data = HobbyData(description="biking")
    >>> person_data = PersonData(hobby=hobby_data)
    >>> person_data.hobby = None  # data is immutable
    Traceback (most recent call last):
    AttributeError: 'PersonData' object attribute 'hobby' is read-only

Action
------
Every time an `Object`_ changes, it will automatically send an `Action`_ up to the
parent and grandparents in the `Hierarchy`_.

The `Action`_ carries information such as:

    - The description of the `Change`_
    - A reference to the `Object`_ receiving the `Action`_ (`receiver`)
    - A reference to the `Object`_ where the change originated from (`sender`)
    - A list of relative indexes/keys from the `receiver` to the `sender`

`Objects <Object_>`_ can define `Reactions <Reaction>`_ that will get triggered once
`Actions <Action>`_ are received.

After all internal `Reactions <Reaction>`_ within an `Write Context`_ run without any
errors, the `Actions <Action>`_ are then sent to external `Observers <Observer>`_ so
they have a chance to synchronize.

Change
******
Describes a change in the state of an `Object`_.

Batch Change
************
Can be subclassed and its instance used when entering a `Batch Context`_ to describe
multiple `Changes <Change>`_.

Reaction
--------
`Reactions <Reaction>`_ are special methods of `Objects <Object_>`_ that respond to
`Actions <Action>`_ received from themselves, their children, and grandchildren.

.. note::
    While an `Object`_ can react to its own changes, its triggered `Reaction`_ cannot
    perform any further changes to the same `Object`_, only to its children and
    grandchildren.

    If an `Attribute`_ value needs to change when another `Attribute`_ in the same
    `Object`_ changes, `Delegated Attributes <Delegated Attribute>`_ should be used
    instead of `Reactions <Reaction>`_.

**Example**: Define `Reaction`_ methods.

.. code:: python

    >>> from objetto.applications import Application
    >>> from objetto.objects import Object
    >>> from objetto.attributes import attribute
    >>> from objetto.reactions import reaction

    >>> class Hobby(Object):
    ...     description = attribute(str)
    ...
    >>> class Person(Object):
    ...     name = attribute(str)
    ...     _possession, possession = protected_attribute_pair(str, default="unknown")
    ...     _hobby, hobby = protected_attribute_pair(Hobby, child=True)
    ...
    ...     @reaction(priority=1)  # decorate reaction method
    ...     def __on_hobby_description_change(self, action, phase):
    ...         if (
    ...             action.locations == ("hobby",) and  # only actions sent from 'hobby'
    ...             phase is Phase.POST and  # after the change happened
    ...             type(action.change) is AttributesChanged and  # attribute change
    ...             "description" in action.change.new_values # 'description' changed
    ...         ):
    ...             hobby_description = action.change.new_values["description"]
    ...             self.__update_possession(hobby_description)
    ...
    ...     def __update_possession(self, hobby_description):
    ...         if hobby_description == "biking":
    ...             self._possession = "bike"
    ...         elif hobby_description == "gaming":
    ...             self._possession = "computer"
    ...         else:
    ...             self._possession = "unknown"
    ...
    ...     # Override the setter to update 'possession' when first/new 'hobby' is set.
    ...     @hobby.setter
    ...     @dependencies(sets=(_hobby, _possession))
    ...     def hobby(self, value):
    ...         self._hobby = value
    ...         self.__update_possession(value.description)
    ...
    >>> app = Application()
    >>> hobby = Hobby(app, description="biking")
    >>> person = Person(app, name="Foo", hobby=hobby)
    >>> print(person.possession)
    'bike'
    >>> hobby.description = "gaming"
    >>> print(person.possession)
    'computer'
    >>> hobby.description = "biking"
    >>> print(person.possession)
    'bike'
    >>> hobby.description = "running"
    >>> print(person.possession)
    'unknown'

Auxiliary Attribute Reaction
****************************
It is possible to specify `Reactions <Reaction>`_ methods when defining `Auxiliary
Attributes <Auxiliary Attribute>`_.

Phase
-----
A constant value that tells whether the change in the state is about to happen (`PRE`)
or if the change already happened (`POST`).

Observer
--------
An external object that inherits from `objetto.observer.Observer` or
`objetto.observer.SlottedObserver` and thus can react to `Actions <Action>`_ sent from
`Objects <Object_>`_ to synchronize/reflect the changes in some way.

Graphical user interface widgets are a good example of `Observers <Observer>`_.

**Example**: Register an external `Observer`_.

Serialization
-------------

**Example**: Serialize an `Object`_.

Deserialization
***************

**Example**: Deserialize an `Object`_.

History
-------
Objetto has built-in support for a undo/redo `History`_. It takes care of managing
its validity for internal changes by flushing itself automatically when necessary,
and it is extremely easy to implement.

A history can be associated with an `Object`_ by adding a `history_attribute` to its
class definition. Accessing that attribute from an `Object`_'s instance will give us the
history itself.

A history will be propagated to children/grandchildren of the `Object`_ which defines
it, however it's possible to prevent that behavior by specifying `history=False` when we
define an `Attribute`_.

Undo/redo can be triggered by running the history's methods `.undo()` and `.redo()`.

Histories are `Objects <Object_>`_ too, so they do send `Actions <Action>`_ that can
trigger `Reactions <Reaction>`_ and/or be observed by `Observers <Observer>`_.

**Example**: Associate a `History`_ with an `Object`_.
