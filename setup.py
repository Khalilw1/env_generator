from setuptools import setup

setup(
    name='generator',
    packages=['generator'],
    include_package_data=True,
    install_requires=[
        'flask',
        'SQLAlchemy',
        'Flask-SQLAlchemy'
    ],
)
