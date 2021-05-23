import os
from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))

with open("README.rst", "r", encoding="utf-8") as f:
    long_description = f.read()

VERSION = '0.1.0b5'
DESCRIPTION = 'FastApi Gino ViewSets'
LONG_DESCRIPTION = 'A package that boosts API creation'

# Setting up
setup(
    name="fastapi-gino-viewsets",
    version=VERSION,
    author="Basalex (Alexander Baskakov)",
    author_email="<alexanderbaskakov@mail.ru>",
    description=DESCRIPTION,
    long_description=long_description,
    packages=find_packages(),
    install_requires=['fastapi', 'gino', 'ginodantic'],
    keywords=['python', 'fastapi', 'gino', 'viewsets', 'pydantic', 'models'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
    project_urls={
        "Source": "https://github.com/Basalex/fastapi-gino-viewsets",
    },
)
