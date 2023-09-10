from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="graphy",
    version="0.1.0",
    author="Bart Ilg",
    description="Query MS Graph via HTTP",
    package_dir={"graphy": "graphy"},
    packages=find_packages(exclude=('tests')),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bartilg/graphy",   
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        'requests',
        'msal',
        'pandas'
    ]
)
