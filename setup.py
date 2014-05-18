import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES')).read()

requires = [
    'lxml',
]

setup(name='Veerok',
    version='1.0.0',
    description='Convert XML to python objects and vice versa',
    long_description=README + '\n\n' +  CHANGES,
    classifiers=[
        "Programming Language :: Python",
    ],
    author='Igor Stroh',
    author_email='igor.stroh@rulim.de',
    url='http://github.com/jenner/veerok',
    keywords='xml',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    tests_require=requires + ['nose'],
    test_suite="veerok"
)

