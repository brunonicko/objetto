import sys
import setuptools  # type: ignore

if sys.version_info[0] == 3 and sys.version_info[1] < 7:
    error = "python {} is not supported".format(".".join((sys.version_info[0:2])))
    raise RuntimeError(error)

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="objetto",
    version="2.0.0",
    author="Bruno Nicko",
    author_email="brunonicko@gmail.com",
    description="Object-oriented framework for building smart applications and APIs",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/brunonicko/objetto",
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    package_data={"objetto": ["py.typed"]},
    install_requires=[
        "enum34; python_version < '3.4'",
        "attrs",
        "jinja2",
        "decorator",
        "pyrsistent",
        "qualname",
        "six",
        "slotted",
        "typing; python_version < '3.5'",
    ],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    python_requires=">=2.7",
)
