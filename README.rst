.. logo_start
.. raw:: html

   <p align="center">
     <a href="https://github.com/brunonicko/objetto">
         <picture>
            <object data="./_static/objetto.svg" type="image/png">
                <source srcset="./docs/source/_static/objetto_white.svg" media="(prefers-color-scheme: dark)">
                <img src="./docs/source/_static/objetto.svg" width="60%" alt="objetto" />
            </object>
         </picture>
     </a>
   </p>
.. logo_end

.. image:: https://github.com/brunonicko/objetto/workflows/MyPy/badge.svg
   :target: https://github.com/brunonicko/objetto/actions?query=workflow%3AMyPy

.. image:: https://github.com/brunonicko/objetto/workflows/Lint/badge.svg
   :target: https://github.com/brunonicko/objetto/actions?query=workflow%3ALint

.. image:: https://github.com/brunonicko/objetto/workflows/Tests/badge.svg
   :target: https://github.com/brunonicko/objetto/actions?query=workflow%3ATests

.. image:: https://readthedocs.org/projects/objetto/badge/?version=stable
   :target: https://objetto.readthedocs.io/en/stable/

.. image:: https://img.shields.io/github/license/brunonicko/objetto?color=light-green
   :target: https://github.com/brunonicko/objetto/blob/main/LICENSE

.. image:: https://static.pepy.tech/personalized-badge/objetto?period=total&units=international_system&left_color=grey&right_color=brightgreen&left_text=Downloads
   :target: https://pepy.tech/project/objetto

.. image:: https://img.shields.io/pypi/pyversions/objetto?color=light-green&style=flat
   :target: https://pypi.org/project/objetto/

Overview
--------
`Objetto`.

Example
-------

.. code:: python

    >>> from objetto import Object, attribute
    >>> class Point(Object):
    ...     x = attribute(types=int)
    ...     y = attribute(types=int)
    ...
    >>> point = Point(3, 4)
