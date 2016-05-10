from setuptools import setup, find_packages

setup(
    name='eru-py',
    version='0.0.29',
    author='tonic',
    zip_safe=False,
    author_email='tonic@wolege.ca',
    description='ERU client for python',
    py_modules=['eruhttp'],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests >= 2.7.0',
        'netaddr == 0.7.18',
        'setuptools == 18.0.1',
        'six == 1.9.0',
        'websocket_client == 0.37.0',
    ],
)
