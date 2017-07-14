from setuptools import setup, find_packages
from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt', session=False)

version = '0.1.0'

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
    install_requires=[str(ir.req) for ir in install_reqs],
    include_package_data=True,
    zip_safe=False,
)
