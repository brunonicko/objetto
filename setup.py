import setuptools  # type: ignore


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
    package_data={"objetto": ["py.typed", "*.pyi"]},
    install_requires=["tippo", "basicco", "registtro"],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    python_requires=">=3.7",
    tests_require=["pytest"],
)
