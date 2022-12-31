from timelength import __title__, __version__, __url__, __author__, __author_email__
from setuptools import setup, find_packages

setup(
    name = __title__,
    version = __version__,

    url = __url__,
    author = __author__,
    author_email = __author_email__,

    packages = find_packages()
)