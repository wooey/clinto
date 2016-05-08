import os
from setuptools import setup, find_packages

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='clinto',
    version='0.1.3',
    packages=find_packages(),
    scripts=[],
    install_requires = ['six',],
    include_package_data=True,
    description='Clinto',
    url='http://www.github.com/wooey/clinto',
    author='Chris Mitchell',
    author_email='chris.mit7@gmail.com',
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)

