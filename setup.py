# flake8: noqa

from setuptools import setup, find_packages

reqs = [
    'eth-abi==1.3.0',
    'eth-keys==0.2.1',
    'eth-account==0.3.0',
    'pycryptodomex',
    'websockets'
]

setup(
    name='riemann-ether',
    version='4.1.1',
    description=('Transaction creation library for Ethereum'),
    url='https://github.com/summa-tx/riemann-ether',
    author='James Prestwich',
    author_email='james@summa.one',
    install_requires=reqs,
    packages=find_packages(),
    package_dir={'ether': 'ether'},
    package_data={'ether': ['py.typed']},
    keywords = 'ethereum cryptocurrency blockchain development',
    python_requires='>=3.6',
    classifiers=[
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)'
    ]
)
