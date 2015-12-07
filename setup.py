from setuptools import setup, find_packages

config = {
    'name': 'modelstatus-client',
    'description': 'Modelstatus REST API client',
    'author': 'MET Norway',
    'url': 'https://github.com/metno/python-modelstatus-client',
    'download_url': 'https://github.com/metno/python-modelstatus-client',
    'version': '2.0.0',
    'install_requires': ['nose', 'requests', 'python-dateutil', 'httmock', 'pyzmq'],
    'packages': find_packages(),
    'scripts': [],
}

setup(**config)
