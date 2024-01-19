from setuptools import setup, find_packages

def readme():
    with open("README.md") as f:
        return f.read()

setup(
    name = "timelength",
    version = "1.1.8",
    url = "https://github.com/EtorixDev/timelength",
    license = "MIT License",
    author = "Etorix",
    author_email = "admin@etorix.dev",
    description = "A Python package to parse human readable lengths of time.",
    long_description_content_type = "text/markdown",
    long_description = readme(),
    classifiers=["License :: OSI Approved :: MIT License",
                 "Programming Language :: Python :: 3",
                 "Programming Language :: Python :: 3.10"],

    packages = find_packages()
)