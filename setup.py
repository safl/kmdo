"""
    Definition of KMDO distribution package
"""
import codecs
import glob
import os
from setuptools import setup

def read(*parts):
    """Read parts to use a e.g. long_description"""

    here = os.path.abspath(os.path.dirname(__file__))

    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with codecs.open(os.path.join(here, *parts), 'r') as pfp:
        return pfp.read()

setup(
    name="kmdo",
    version="1.0.2",
    description="Command-line tool for auto generating command output",
    long_description=read('README.rst'),
    author="Simon A. F. Lund",
    author_email="os@safl.dk",
    url="https://github.com/safl/kmdo",
    license="Apache License 2.0",
    install_requires=[],
    zip_safe=False,
    data_files=[
        ("bin", glob.glob("bin/*")),
    ],
    options={"bdist_wheel":{"universal":True}},
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Text Processing",
        "Topic :: Utilities"
    ],
)
