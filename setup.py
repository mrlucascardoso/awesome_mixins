import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='awesome-mixins',
    version='0.8',
    packages=find_packages(),
    install_requires=[
        'django-braces',
    ],
    include_package_data=True,
    license='MIT',
    description='Set of the mixins for class based view on django.',
    long_description=README,
    url='https://github.com/MrLucasCardoso/awesome_mixins',
    author='Lucas Cardoso',
    author_email='mr.lucascardoso@gmail.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.10',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
