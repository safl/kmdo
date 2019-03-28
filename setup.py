"""
    Definition of KMDO distribution package
"""
import glob
from setuptools import setup

setup(
    name="kmdo",
    version="0.0.1",
    description="Command-line tool for auto generating command output",
    author="Simon A. F. Lund",
    author_email="safl@safl.dk",
    url="https://github.com/safl/kmdo",
    license="Apache License 2.0",
    install_requires=[],
    zip_safe=False,
    data_files=[
        ("bin", glob.glob("bin/*")),
    ],
    options={"bdist_wheel":{"universal":True}},
    classifiers=[
        "Development Status :: 4 - Beta",
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
