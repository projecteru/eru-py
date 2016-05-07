from setuptools import setup, find_packages

setup(
    name='eru-py',
    version='0.0.27',
    author='tonic',
    zip_safe=False,
    author_email='tonic@wolege.ca',
    description='ERU client for python',
    py_modules=['eruhttp'],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests>=2.7.0',
        'websocket-client>=0.30.0',
    ],
)
