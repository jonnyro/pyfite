"""Builds a .whl for the pyfite package.
"""
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyfite",
    version="0.0.1",
    author="Ryan Hite",
    author_email="rhite@ara.com",
    description="Basic module containing FITE helper classes.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    install_requires=[
        "numpy>=1.17.3",
        "pymap3d>=2.1.0",
        "pyproj>=2.4.1"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
