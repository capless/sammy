import pathlib
import pkg_resources
from setuptools import setup, find_packages

with pathlib.Path('requirements.txt').open() as requirements_txt:
    install_requires = [
        str(requirement)
        for requirement
        in pkg_resources.parse_requirements(requirements_txt)
    ]
version = '0.4.2'

setup(
    name='sammy',
    version=version,
    description="Python library for generating AWS SAM "
                "(Serverless Application Model) templates with validation.",
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Environment :: Web Environment",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3 :: Only"
    ],
    keywords='serverless, cloudformation, sam',
    author='Brian Jinwright',
    author_email='opensource@ipoots.com',
    maintainer='Brian Jinwright',
    packages=find_packages(),
    url='https://github.com/capless/sammy',
    license='GNU General Public License v3.0',
    install_requires=install_requires,
    include_package_data=True,
    zip_safe=False,
)
