from setuptools import setup, find_packages

setup(
    name='eru-py',
    version='0.0.2',
    author='tonic',
    zip_safe=False,
    author_email='tonic@wolege.ca',
    description='ERU client for python',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests>=2.7.0',
    ],
)
