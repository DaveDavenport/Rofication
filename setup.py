import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def read_metadata():
    name = version = url = None
    with open('rofication/_metadata.py') as fp:
        for match in re.finditer(r"^(ROFICATION_\w+?)\s*=\s*['\"](.*?)['\"]$", fp.read(), re.MULTILINE):
            var, value = match.groups()
            if var == 'ROFICATION_NAME':
                name = value
            elif var == 'ROFICATION_VERSION':
                version = value
            elif var == 'ROFICATION_URL':
                url = value

    if name is None or version is None or url is None:
        raise RuntimeError('unable to read package metadata')

    return name, version, url


NAME, VERSION, URL = read_metadata()
DESCRIPTION = 'Notification system that provides a Rofi front-end'

REQUIRED_PYTHON_VERSION = '>=3.6.0'
LICENSE = 'MIT'
CLASSIFIERS = [
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: Implementation :: CPython'
]

REQUIRED = ['PyGObject>=3.26.1', 'dbus-python>=1.2.6']

PACKAGES = ['rofication', 'rofication.resources']
SCRIPTS = ['rofication-daemon', 'rofication-gui']

setup(
    name=NAME,
    description=DESCRIPTION,
    version=VERSION,
    python_requires=REQUIRED_PYTHON_VERSION,
    packages=PACKAGES,
    scripts=SCRIPTS,
    url=URL,
    install_requires=REQUIRED,
    license=LICENSE,
    classifiers=CLASSIFIERS,
)
