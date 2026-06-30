"""GAIA OS setup — installs the `gaia` CLI entry point."""
from setuptools import setup, find_packages

setup(
    name="gaia-os",
    version="0.1.0",
    description="GAIA — The Global Autonomous Intelligence Architecture",
    packages=find_packages(),
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "gaia=cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
