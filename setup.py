from setuptools import setup, find_packages

config = {
    'name': 'productstatus-client',
    'description': 'Productstatus REST API client',
    'author': 'MET Norway',
    'url': 'https://github.com/metno/python-productstatus-client',
    'download_url': 'https://github.com/metno/python-productstatus-client',
    'version': '7.0.0',
    'python_requires': '>=3.6',
    'install_requires': [
        'nose==1.3.7',
        'requests==2.20.0',
        'python-dateutil==2.7.5',
        'httmock==1.2.6',
        'kafka-python==1.4.3',
        'mock==2.0.0',
    ],
    'packages': find_packages(),
    'scripts': [],
}

setup(**config)
