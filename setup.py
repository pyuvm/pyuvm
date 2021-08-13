import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyuvm",
    version="2.0a8",
    author="Ray Salemi",
    author_email="ray@raysalemi.com",
    description="A Python implementation of the UVM using cocotb",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pyuvm/pyuvm",
    project_urls={
        "Bug Tracker": "https://github.com/pyuvm/pyuvm/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    install_requires="cocotb>=1.5.2",
)
