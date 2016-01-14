from setuptools import setup, find_packages

config = {
    'name': 'productstatus-client',
    'description': 'Productstatus REST API client',
    'author': 'MET Norway',
    'url': 'https://github.com/metno/python-productstatus-client',
    'download_url': 'https://github.com/metno/python-productstatus-client',
    'version': '3.1.1',
    'install_requires': ['nose', 'requests', 'python-dateutil', 'httmock', 'pyzmq'],
    'packages': find_packages(),
    'scripts': [],
}

setup(**config)
