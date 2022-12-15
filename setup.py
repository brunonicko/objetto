import os

import setuptools  # type: ignore

with open("README.rst", "r") as fh:
    long_description_lines = fh.read().split("\n")

    line_nos = {}
    for i, line in enumerate(long_description_lines):
        if line == ".. logo_start":
            line_nos["logo_start"] = i
        elif line == ".. logo_end":
            line_nos["logo_end"] = i
            break

    assert line_nos["logo_start"] < line_nos["logo_end"]

    long_description = "Datta\n=====\n" + "\n".join(long_description_lines[line_nos["logo_end"] + 1 :])


with open("requirements.txt", "r") as fh:
    install_requires = [line.strip(os.linesep) for line in fh.readlines()]


setuptools.setup(
    name="objetto",
    version="2.0.0",
    author="Bruno Nicko",
    author_email="brunonicko@gmail.com",
    description="Objetto.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/brunonicko/objetto",
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    package_data={"objetto": ["py.typed"]},
    install_requires=install_requires,
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    python_requires=">= 2.7, != 3.0.*, != 3.1.*, != 3.2.*, != 3.3.*, != 3.4.*, != 3.5.*, != 3.6.*",
    tests_require=["pytest"],
)
