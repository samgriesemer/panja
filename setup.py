import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="panja",
    version="0.0.1",
    author="Sam Griesemer",
    author_email="samgriesemer@gmail.com",
    description="pipeline building utilities with Jinja and Pandoc",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/samgriesemer/panja",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)%
