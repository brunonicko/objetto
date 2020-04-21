import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="modelo",
    version="0.0.1",
    author="Bruno Nicko",
    author_email="brunonicko@gmail.com",
    description="Framework for building data-centric Applications/APIs",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/brunonicko/modelo",
    packages=setuptools.find_packages(),
    install_requires=["six", "slotted", "typing", "enum34"],
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=2.7",
)
