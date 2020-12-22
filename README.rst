Objetto
=======
.. image:: https://github.com/brunonicko/objetto/workflows/MyPy/badge.svg
   :target: https://github.com/brunonicko/objetto/actions?query=workflow%3AMyPy

.. image:: https://github.com/brunonicko/objetto/workflows/Lint/badge.svg
   :target: https://github.com/brunonicko/objetto/actions?query=workflow%3ALint

.. image:: https://github.com/brunonicko/objetto/workflows/Tests/badge.svg
   :target: https://github.com/brunonicko/objetto/actions?query=workflow%3ATests

.. image:: https://readthedocs.org/projects/objetto/badge/?version=stable
   :target: https://objetto.readthedocs.io/en/stable/

.. image:: https://img.shields.io/github/license/brunonicko/objetto?color=light-green
   :target: https://github.com/brunonicko/objetto/blob/master/LICENSE

.. image:: https://static.pepy.tech/personalized-badge/objetto?period=total&units=international_system&left_color=grey&right_color=brightgreen&left_text=Downloads
   :target: https://pepy.tech/project/objetto

.. image:: https://img.shields.io/pypi/pyversions/objetto?color=light-green&style=flat
   :target: https://pypi.org/project/objetto/

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
  - `Objects <Object_>`_ encase an immutable subset version of themselves referred to
    as `Data`_.
  - `Objects <Object_>`_ will send an `Action`_ to themselves, their parent, and
    grandparents everytime a `Change`_ happens.
  - `Objects <Object_>`_ can perform `Reactions <Reaction>`_ in response to `Actions
    <Action>`_ received from themselves, their children, and grandchildren.
  - `Objects <Object_>`_ can be observed by external `Observers <Action Observer>`_ such
    as GUI widgets.
  - `Objects <Object_>`_ feature built-in human-readable `Serialization`_ and
    `Deserialization`_ capabilities.
  - `Objects <Object_>`_ can be automatically tracked by a
    `History <Undo/Redo History>`_, which allows for easy and selective undo/redo
    functionality.

How to install
--------------
You can install `Objetto` by using `pip <https://pypi.org/>`_:

``pip install objetto``

Application
-----------
An `Application`_ oversees all `Objects <Object_>`_ that are meant to work together. It
provides different contexts for managing and keeping track of their `Changes <Change>`_.

`Objects <Object_>`_ that are part of different `Applications <Application>`_ see each
other as regular values and can never be part of the same `Hierarchy`_.

An `Application`_ can have `Root Objects <Roots>`_, which are `Objects <Object_>`_ that
are always available at the top of the hierarchy, and cannot be parented under other
`Objects <Object_>`_.

**Example**: Instantiate a new `Application`_.

.. code:: python

    >>> from objetto import Application

    >>> app = Application()  # instantiate a new application

Read Context
************
While in a `Read Context`_, all `Objects <Object>`_ in the `Application`_ are guaranteed
not to be modified.

**Example**: Enter a `Read Context`_.

.. code:: python

    >>> from objetto import Application

    >>> app = Application()
    >>> with app.read_context():
    ...     pass  # read access only, no changes allowed
    ...

Write Context
*************
While in a `Write Context`_, `Actions <Action>`_ are only sent internally until the
outermost `Write Context`_ exits without errors, after which external `Observers
<Action Observer>`_ will then receive them.

If an unhandled exception gets raised, all changes are reverted to the moment the
context was entered, and external `Observers <Action Observer>`_ will not receive any
`Actions <Action>`_. This behavior is similar to `transactions` in a database.

.. note::
    You cannot enter a `Write Context`_ while in a `Read Context`_.

**Example**: Enter a `Write Context`_.

.. code:: python

    >>> from objetto import Application

    >>> app = Application()
    >>> with app.write_context():
    ...     pass  # send actions to external observers only at the end, revert if errors
    ...

Roots
*****
Root `Objects <Object_>`_ can be declared when creating a subclass of an `Application`_
by using a root descriptor and specifying the `Object`_ type and initialization
arguments.

**Example**: Define `Root Objects <Roots>`_ when subclassing `Application`_.

.. code:: python

    >>> from objetto import Application, Object, attribute, root

    >>> class Document(Object):
    ...     title = attribute(str)
    ...
    >>> class CustomApplication(Application):  # inherit from Application
    ...     document = root(Document, title="untitled")  # specify object type and args
    ...
    >>> app = CustomApplication()
    >>> type(app.document).__name__
    'Document'

Object
------
`Objects <Object_>`_ are the building blocks of an `Application`_. An `Object`_ is
mutable, has state, and can be a parent/child of another `Object`_.

To define our own `Object`_, we have to inherit from `objetto.Object` and use
`Attributes <Attribute>`_ to define its schema. You need to instantiate it by passing an
`Application`_, which can later be accessed through the `.app` property:

**Example**: Make our own `Object`_ subclass and instantiate it.

.. code:: python

    >>> from objetto import Application, Object, attribute

    >>> class Hobby(Object):  # inherit from Object
    ...     description = attribute(str)  # example attribute called 'description'
    ...
    >>> app = Application()  # we need an application
    >>> hobby = Hobby(app, description="biking")  # instantiate our object
    >>> hobby.app is app
    True

Attribute
---------
`Attributes <Attribute>`_ describe the schema of an `Object`_. When defining one, we can
specify relationship parameters between the `Object`_ that owns it and the value being
stored, such as a `Value Type`_, `Hierarchy`_ settings, `History <Undo/Redo History>`_
propagation, `Serialization`_ and `Deserialization`_ options, etc.

**Example**: Define custom `Objects <Object_>`_ with multiple `Attributes <Attribute>`_.

.. code:: python

    >>> from objetto import Application, Object, attribute

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
    >>> person.name
    'Phil'
    >>> person.name = "Gaimon"
    >>> person.name
    'Gaimon'

Value Type
**********
When defining an `Attribute`_, we can specify its `Value Type`_. This is leveraged by
the runtime type checking and by static ones such as `mypy <http://mypy-lang.org/>`_.

Defining types is also helpful to inform `Objetto` about the schema of our
`Objects <Object>`_, which is needed for proper `Serialization`_ and `Deserialization`_.

Import strings are also valid (using the syntax `module.submodule|Class.NestedClass`),
and they will be imported lazily during runtime. It's also possible to use multiple
`Types <Value Type>`_ by specifying them in a tuple.

.. note::
    Static type checkers such as `mypy <http://mypy-lang.org/>`_ might not understand
    types correctly when multiple/lazy types are declared. In that case, you can help
    the type checker by adding a type hint/comment using the `Attribute`_ base like so:

    **Example**: Helping static type checkers with a type hint for the attribute.

    .. code:: python

        >>> from typing import Union
        >>> from objetto.objects import Attribute  # use 'Attribute' base for type hint
        >>> from objetto import Object, attribute

        >>> class Example(Object):
        ...     foo = attribute(
        ...         (str, int, "__main__|Example")
        ...     )  # type: Attribute[Union[str, int, Example]]
        ...

The types are interpreted 'exactly' by default. This means they are checked and compared
by identity, so instances of subclasses are not accepted. However that behavior can be
changed by specifying `subtypes=True` when defining an `Attribute`_.

If `None` is also accepted as a value, we can specify `None` as a valid type.

**Example**: Define the `Value Types <Value Type>`_ of `Attributes <Attribute>`_.

.. code:: python

    >>> from objetto import Object, attribute

    >>> class Person(Object):
    ...     name = attribute(str)  # single exact value type
    ...     friend = attribute(("__main__|Person", None))  # import path, accepts None
    ...     hobby = attribute("module.hobby|Hobby") # import path with module path
    ...     points = attribute((int, float))  # multiple basic types
    ...     _status = attribute(serialized=False)  # no value type, not serialized
    ...     _pet = attribute(
    ...         "pets|AbstractPet", subtypes=True
    ...     )  # accepts instances of 'AbstractPet' subclasses

Value Factory
*************
An `Attribute`_ can conform and/or verify new values by using a `Value Factory`_, which
is simply a function or callable that takes the newly input value, does something to it,
and then return the actual value that gets stored in the `Object`_.

.. note::
    There's a very important thing to note when it comes to defining your own
    `<Value Factory>`_, which is that any value returned by the factory should always
    produce itself in case it's fed again through the same factory. Also, the
    `<Value Factory>`_ needs to be deterministic.

You can use simple functions or callable types as `Value Factories <Value Factory>`_,
but `Objetto` offers some very useful pre-defined ones that can be easily configured
with parameters.

Here are some of those built-in `Value Factories <Value Factory>`_, which can be
imported from `objetto.factories`:

  - `Integer`
  - `FloatingPoint`
  - `RegexMatch`
  - `RegexSub`
  - `String`
  - `Curated`
  - `Boolean`

**Example**: Use `Value Factories <Value Factory>`_ to conform/verify attribute values.

.. code:: python

    >>> from objetto import Object, attribute
    >>> from objetto.factories import RegexMatch, Integer, Curated, String, Boolean

    >>> class Person(Object):
    ...     name = attribute(str, factory=RegexMatch(r"^[a-z ,.'-]+$"))  # regex match
    ...     age = attribute(int, factory=Integer(minimum=1))  # minimum integer
    ...     pet = attribute(str, factory=Curated(("cat", "dog"))) # curated values
    ...     job = attribute(str, factory=String())  # force string
    ...     happy = attribute(bool, factory=Boolean(), default=True)  # force boolean

Auxiliary Attribute
*******************
These are special `Attributes <Attribute>`_ that will hold multiple values instead of
just one.

The most basic `Auxiliary Attributes <Auxiliary Attribute>`_ are:

  - `list_attribute`
  - `dict_attribute`
  - `set_attribute`

**Example**: Use `Auxiliary Attributes <Auxiliary Attribute>`_ to hold values.

.. code:: python

    >>> from objetto import Application, Object, attribute, list_attribute

    >>> class Hobby(Object):
    ...     description = attribute(str)
    ...
    >>> class Person(Object):
    ...     hobbies = list_attribute(Hobby)  # holds multiple 'hobbies'
    ...
    >>> app = Application()
    >>> hobby_a = Hobby(app, description="biking")
    >>> hobby_b = Hobby(app, description="gaming")
    >>> person = Person(app, hobbies=(hobby_a, hobby_b))  # initialize with iterable
    >>> person.hobbies[0] is hobby_a
    True

Delegated Attribute
*******************
`Attributes <Attribute>`_ can have delegate methods that will get, set and/or delete
the values of other `Attributes <Attribute>`_ in the same `Object`_.

When defining delegates, you have to specify which `Attributes <Attribute>`_ they will
read from as `dependencies`.

.. note::
    The results of delegate methods are cached, and because of that they should never
    rely on mutable external objects. Think of delegates as 'pure functions' in the
    context of the `Object`_ they belong to.

    If an `Attribute`_ value needs to change according to external factors,
    `Reactions <Reaction>`_ or regular methods are encouraged to be used instead of
    delegates.

**Example**: Define a `Delegated Attribute`_ with a `getter` and a `setter`.

.. code:: python

    >>> from objetto import Application, Object, attribute

    >>> class Person(Object):
    ...     first_name = attribute(str)
    ...     last_name = attribute(str)
    ...     name = attribute(
    ...         str, delegated=True, dependencies=(first_name, last_name)
    ...     )  # delegated attribute with read dependencies
    ...
    ...     @name.getter  # define a getter delegate
    ...     def name(self):
    ...         return self.first_name + " " + self.last_name
    ...
    ...     @name.setter  # define a setter delegate
    ...     def name(self, value):
    ...         self.first_name, self.last_name = value.split()
    ...
    >>> app = Application()
    >>> person = Person(app, first_name="Katherine", last_name="Johnson")
    >>> person.name
    'Katherine Johnson'
    >>> person.name = "Grace Hopper"
    >>> person.name
    'Grace Hopper'
    >>> person.first_name
    'Grace'
    >>> person.last_name
    'Hopper'

Attribute Helper
****************
There are patterns that come up very often when defining `Attributes <Attribute>`_.
Instead of re-writing those patterns everytime, it's possible to use helper functions
known as `Attribute Helpers <Attribute Helper>`_ to get the same effect.

Here are some examples of `Attribute Helpers <Attribute Helper>`_:

  - `constant_attribute`
  - `protected_attribute_pair`
  - `protected_list_attribute_pair`
  - `protected_dict_attribute_pair`
  - `protected_set_attribute_pair`

**Example**: Define a simple `Attribute Helper`_.

.. code:: python

    >>> from objetto import Application, Object, protected_attribute_pair

    >>> class Person(Object):
    ...     _name, name = protected_attribute_pair(str, default="King")  # helper
    ...
    ...     def set_name(self, name):
    ...         self._name = name.upper()  # set the changeable private attribute
    ...
    >>> app = Application()
    >>> person = Person(app)
    >>> person.name
    'King'
    >>> person.name = "bb king"  # can't set non-changeable public attribute
    Traceback (most recent call last):
    AttributeError: attribute 'name' is read-only
    >>> person.set_name("bb king")  # we have to use the method instead
    >>> person.name
    'BB KING'

Hierarchy
---------
An `Object`_ can have one parent and/or multiple children.

The parent-children hierarchy is central to the way `Objetto` works, as it provides an
elegant way to structure our `Application`_. It's essential for features like:

  - Preventing cyclic references: `Objects <Object_>`_ can only have one parent
  - Immutable `Data`_ 'mirroring': The `Data`_ structure will replace child `Objects
    <Object_>`_ with their `Data`_ according to the hierarchy
  - Human-readable `Serialization`_: The `.serialize()` and `.deserialize()` methods
    utilize the hierarchy to format their input/output
  - `Action`_ sending and subsequent `Reaction`_\ response: `Actions <Action>`_ will
    propagate from where the `Change`_ happened all the way up the hierarchy to the
    topmost grandparent, triggering `Reactions <Reaction>`_ along the way
  - Automatic `History <Undo/Redo History>`_ propagation: Children can automatically be
    assigned to the same `History <Undo/Redo History>`_ of the parent if desired.

.. note::
    The hierarchical relationship can be turned off selectively at the expense of those
    features by specifying `child=False` when we define an `Attribute`_.

    Also note that the hierarchical relationship will only work between
    `Objects <Object_>`_ within the same `Application`_.

**Example**: Access `._parent` and `._children` properties.

.. code:: python

    >>> from objetto import Application, Object, attribute

    >>> class Hobby(Object):
    ...     description = attribute(str)
    ...
    >>> class Person(Object):
    ...     name = attribute(str)
    ...     hobby = attribute(Hobby)  # child=True is the default behavior
    ...
    >>> app = Application()
    >>> hobby = Hobby(app, description="animation")
    >>> person = Person(app, name="Hayao Miyazaki", hobby=hobby)
    >>> hobby._parent is person  # 'person' is the parent of 'hobby'
    True
    >>> hobby in person._children  # 'hobby' is a child of 'person'
    True

Undo/Redo History
-----------------
Objetto has built-in support for a undo/redo `History <Undo/Redo History>`_. It takes
care of managing its validity for internal changes by flushing itself automatically when
necessary, and it is extremely easy to implement.

A history can be associated with an `Object`_ by adding a `history_descriptor` to the
class definition. Accessing that attribute from an `Object`_'s instance will give us the
history itself.

A history will be propagated to children/grandchildren of the `Object`_ which defines
it, however it's possible to prevent that behavior by specifying `history=False` when we
define an `Attribute`_.

Undo/redo can be triggered by running the history's methods `.undo()` and `.redo()`.

Histories are `Objects <Object_>`_ too, so they do send `Actions <Action>`_ that can be
observed by `Observers <Action Observer>`_.

**Example**: Associate a `History <Undo/Redo History>`_ with an `Object`_.

.. code:: python

    >>> from objetto import Application, Object, history_descriptor, attribute

    >>> class Person(Object):
    ...     history = history_descriptor()  # specify a history
    ...     name = attribute(str)
    ...
    >>> app = Application()
    >>> person = Person(app, name="Dave")
    >>> person.name
    'Dave'
    >>> person.name = "Dave Grohl"
    >>> person.name
    'Dave Grohl'
    >>> person.history.undo()  # undo the name change
    >>> person.name
    'Dave'

Batch Context
*************
An `Object`_ can enter a `Batch Context`_, which will group multiple `Changes <Change>`_
happening to itself and/or to other `Objects <Object>`_ into one single entry in the
associated `History <Undo/Redo History>`_.

A special `Action`_ carrying the the name and the metadata of the batch context will be
sent when entering (`PRE` `Phase`_) and when exiting the context (`POST` `Phase`_).

**Example**: Enter a `Batch Context`_.

.. code:: python

    >>> from objetto import Application, Object, history_descriptor, attribute

    >>> class Hobby(Object):
    ...     description = attribute(str)
    ...
    >>> class Person(Object):
    ...     history = history_descriptor()  # specify a history
    ...     name = attribute(str)
    ...     hobby = attribute(Hobby)  # history will propagate by default
    ...
    ...     def set_info(self, name, hobby_description):
    ...         with self._batch_context("Set Person Info"):  # enter batch
    ...             self.name = name  # single change
    ...             self.hobby.description = hobby_description  # single change
    ...
    >>> app = Application()
    >>> hobby = Hobby(app, description="sailing")
    >>> person = Person(app, name="Albert", hobby=hobby)
    >>> person.name, person.hobby.description
    ('Albert', 'sailing')
    >>> person.set_info("Einstein", "physics")  # batch change
    >>> person.name, person.hobby.description
    ('Einstein', 'physics')
    >>> person.history.undo()  # single undo will revert both changes
    >>> person.name, person.hobby.description
    ('Albert', 'sailing')

Data
----
`Data`_ are analog structures to `Objects <Object_>`_, but they are immutable.

Everytime an `Object`_ changes, their internal `Data`_ and all of its parent's and
grandparents' `Data`_ get replaced with a new one that reflects those changes.

By default, every `Object`_ class/subclass with automatically generate it's `Data`_
class based on its attributes and schema. You can access the data type of an `Object`_
through its `.Data` class property.

The `Data`_ instance for an `Object`_ can be accessed through its `.data` property.

**Example**: Access internal `Data`_ of an `Object`_.

.. code:: python

    >>> from objetto import Application, Object, attribute

    >>> class Hobby(Object):
    ...     description = attribute(str)
    ...
    >>> class Person(Object):
    ...     hobby = attribute(Hobby)
    ...
    >>> Person.Data.__fullname__  # access to automatically generated 'Data' class
    'Person.Data'
    >>> app = Application()
    >>> hobby = Hobby(app, description="biking")
    >>> person = Person(app, hobby=hobby)
    >>> hobby_data = person.data.hobby  # access 'hobby' data through 'person' data
    >>> hobby_data is hobby.data
    True
    >>> hobby_data.description
    'biking'

If you want to bind methods from the `Object`_ to the `Data`_ as well, you can use the
`data_method` decorator.

**Example**: Using the `data_method` decorator.

.. code:: python

    >>> from objetto import Application, Object, attribute, data_method

    >>> class Hobby(Object):
    ...     description = attribute(str)
    ...
    ...     @data_method
    ...     def get_description(self):
    ...         return "Description: {}".format(self.description)
    ...
    >>> app = Application()
    >>> hobby = Hobby(app, description="biking")
    >>> hobby.get_description()
    'Description: biking'
    >>> hobby.data.get_description()  # 'hobby' data also has the method
    'Description: biking'

And finally, if you want more control, you can define a custom `Data`_ class for an
`Object`_, but this only recommended for advanced behavior. Keep in mind that the class
must match the schema of the `Object <Object>`_'s `Attributes <Attribute>`_.

**Example**: Defining a custom `Data`_ class for an `Object <Object>`_.

.. code:: python

    >>> from objetto import Application, Object, Data, attribute, data_attribute

    >>> class Hobby(Object):
    ...     description = attribute(str)
    ...
    ...     class Data(Data):
    ...         description = data_attribute(str, factory=lambda v, **_: v.upper())
    ...
    >>> app = Application()
    >>> hobby = Hobby(app, description="biking")
    >>> hobby.description
    'biking'
    >>> hobby.data.description  # data attribute has a custom factory
    'BIKING'

It's also possible to use `Data`_ on its own, without an encasing `Object`_. Remember
that `Data`_ instances are immutable, so the only way to produce changes is by calling
methods that return a new version of the data when subclassing from an *interactive*
`Data`_ class.

**Example**: Using an interactive `Data`_ on its own.

.. code:: python

    >>> from objetto import InteractiveData, data_attribute

    >>> class HobbyData(InteractiveData):  # inherit from InteractiveData
    ...     description = data_attribute(str)  # use data attributes
    ...
    >>> class PersonData(InteractiveData):
    ...     hobby = data_attribute((HobbyData, None))  # specify data types
    ...
    >>> hobby_data = HobbyData(description="biking")
    >>> new_hobby_data = hobby_data.set("description", "programming")  # make new
    >>> person_data = PersonData(hobby=hobby_data)
    >>> person_data.hobby = None  # data is immutable
    Traceback (most recent call last):
    AttributeError: 'PersonData' object attribute 'hobby' is read-only

Action
------
Every time an `Object`_ changes, it will automatically send an `Action`_ up the
`Hierarchy`_ to its parent and grandparents.

The `Action`_ carries information such as:

  - The description of the `Change`_ (`change`)
  - A reference to the `Object`_ receiving the `Action`_ (`receiver`)
  - A reference to the `Object`_ where the change originated from (`sender`)
  - A list of relative indexes/keys from the `receiver` to the `sender` (`locations`)

Phase
*****
A constant value that tells whether the change in the state is about to happen (`PRE`)
or if the change already happened (`POST`).

Change
******
A `Change`_ describes what exactly changed in the state of an `Object`_.

Here are some of the `Changes <Change>`_ provided by `Objects <Object>`_:

  - `Batch`
  - `Update`
  - `DictUpdate`
  - `ListInsert`
  - `ListDelete`
  - `ListUpdate`
  - `ListMove`
  - `SetUpdate`
  - `SetRemove`

Reaction
********

`Objects <Object_>`_ can define `Reactions <Reaction>`_ that will get triggered once
`Actions <Action>`_ are received.
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

    >>> from objetto import Application, Object, attribute, reaction, POST

    >>> class MyObject(Object):
    ...     value = attribute(int, default=0)
    ...
    ...     @reaction
    ...     def __on_received(self, action, phase):
    ...         if not self._initializing and phase is POST:
    ...             print(("LAST -", action.change.name, phase))
    ...
    ...     @reaction(priority=1)
    ...     def __on_received_first(self, action, phase):
    ...         if not self._initializing and phase is POST:
    ...             print(("FIRST -", action.change.name, phase))
    ...
    >>> app = Application()
    >>> my_obj = MyObject(app)
    >>> my_obj.value = 42
    ('FIRST -', 'Update Attributes', <Phase.POST: 'POST'>)
    ('LAST -', 'Update Attributes', <Phase.POST: 'POST'>)

Action Observer
***************

After all internal `Reactions <Reaction>`_ within an `Write Context`_ run without any
errors, the `Actions <Action>`_ are then finally sent to external
`Action Observers <Action Observer>`_ so they have a chance to synchronize.

Graphical user interface widgets are a good example of
`Action Observers <Action Observer>`_.

**Example**: Register an external `Action Observer`_.

.. code:: python

    >>> from objetto import Application, Object, ActionObserver, attribute

    >>> class Person(Object):
    ...     name = attribute(str, default="Nina")
    ...
    >>> class PersonObserver(ActionObserver):
    ...
    ...     def __observe__(self, action, phase):
    ...         print((action.change.name, phase.value))
    ...
    >>> app = Application()
    >>> person = Person(app)
    >>> observer = PersonObserver()
    >>> token = observer.start_observing(person)
    >>> person.name = "Simone"
    ('Update Attributes', 'PRE')
    ('Update Attributes', 'POST')

Auxiliary Attribute Reaction
****************************
It is possible to specify `Reactions <Reaction>`_ methods/callables when defining
`Auxiliary Attributes <Auxiliary Attribute>`_. `Objetto` offers configurable reactions
that can be used for that purpose.

Here are some of them:

  - `UniqueAttributes`
  - `LimitChildren`
  - `Limit`

**Example**: Ensure unique names.

.. code:: python

    >>> from objetto import Application, Object, attribute, list_attribute
    >>> from objetto.reactions import UniqueAttributes

    >>> class Person(Object):
    ...     name = attribute(str)
    ...
    >>> class Band(Object):
    ...     musicians = list_attribute(Person, reactions=UniqueAttributes("name"))
    ...
    >>> app = Application()
    >>> person_a = Person(app, name="Paul")
    >>> person_b = Person(app, name="John")
    >>> band = Band(app, musicians=(person_a, person_b))
    >>> person_c = Person(app, name="Paul")
    >>> band.musicians.append(person_c)
    Traceback (most recent call last):
    ValueError: another object already has 'name' set to 'Paul'

Serialization
-------------
`Objects <Object>`_ support human-readable serialization out of the box.

**Example**: Serialize an `Object`_.

.. code:: python

    >>> from objetto import Application, Object, attribute, list_attribute

    >>> class Person(Object):
    ...     name = attribute(str)
    ...
    >>> class Band(Object):
    ...     musicians = list_attribute(Person)
    ...
    >>> app = Application()
    >>> person_a = Person(app, name="Oscar")
    >>> person_b = Person(app, name="Ray")
    >>> band = Band(app, musicians=(person_a, person_b))
    >>> band.serialize()
    {'musicians': [{'name': 'Oscar'}, {'name': 'Ray'}]}

Deserialization
***************
`Objects <Object>`_ support human-readable deserialization out of the box.

**Example**: Deserialize an `Object`_.

.. code:: python

    >>> from objetto import Application, Object, attribute, list_attribute

    >>> class Person(Object):
    ...     name = attribute(str)
    ...
    >>> class Band(Object):
    ...     musicians = list_attribute(Person)
    ...
    >>> app = Application()
    >>> Band.deserialize({"musicians": [{"name": "Oscar"}, {"name": "Ray"}]}, app=app)
    Band(musicians=[<Person at ...>, <Person at ...>])

Custom Serializer/Deserializer
******************************
You can specify custom serializer/deserializer functions for attributes.

**Example**: Serialize an `Enum` using lambdas.

.. code:: python

    >>> from enum import Enum
    >>> from objetto import Application, Object, attribute

    >>> class Hobby(Enum):
    ...     GUITAR = 1
    ...     BIKING = 2
    ...
    >>> class Person(Object):
    ...     hobby = attribute(
    ...         Hobby,
    ...         serializer=lambda value, **_: value.name.lower(),
    ...         deserializer=lambda value, **_: Hobby[value.upper()],
    ...     )
    ...
    >>> app = Application()
    >>> person = Person(app, hobby=Hobby.GUITAR)
    >>> person.serialize()
    {'hobby': 'guitar'}
    >>> Person.deserialize({"hobby": "biking"}, app=app)
    Person(hobby=<Hobby.BIKING: 2>)

**Example**: Serialize an `Enum` using provided serializer/deserializer.

.. code:: python

    >>> from enum import Enum
    >>> from objetto import Application, Object, attribute
    >>> from objetto.serializers import EnumSerializer
    >>> from objetto.deserializers import EnumDeserializer

    >>> class Hobby(Enum):
    ...     GUITAR = 1
    ...     BIKING = 2
    ...
    >>> class Job(Enum):
    ...     PROGRAMMER = 1
    ...     TEACHER = 2
    ...
    >>> class Person(Object):
    ...     hobby = attribute(
    ...         Hobby,
    ...         serializer=EnumSerializer(),
    ...         deserializer=EnumDeserializer(Hobby),
    ...     )
    ...     job = attribute(
    ...         Job,
    ...         serializer=EnumSerializer(by_name=True),
    ...         deserializer=EnumDeserializer(Job, by_name=True),
    ...     )
    ...
    >>> app = Application()
    >>> person = Person(app, hobby=Hobby.GUITAR, job=Job.PROGRAMMER)
    >>> serialized = person.serialize()
    >>> serialized["hobby"]
    1
    >>> serialized["job"]
    'PROGRAMMER'
    >>> Person.deserialize({"hobby": 2, "job": "TEACHER"}, app=app)
    Person(hobby=<Hobby.BIKING: 2>, job=<Job.TEACHER: 2>)

... And More!
*************
Take a look at the API documentation to learn more about `Objetto`.
