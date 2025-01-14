from setuptools import setup, find_packages

setup(
    name='auto',
    version='1.3.2',
    description="A platform for controling all the robots in Automat's lat ",
    license='See license',
    packages=find_packages(),
    install_requires=[
        "paramiko==2.8.1", # higher version yields misleading exception about RSA keys.
        "scp",
        "notebook",
        "sqlalchemy",
        "mysql-connector-python",
        "pandas",
        "numpy",
    ],
    entry_points={ # create scripts and add to sys.PATH
        'console_scripts': [
            'sdwf = scripts.sdwf_master:main',
        ],
    },
)