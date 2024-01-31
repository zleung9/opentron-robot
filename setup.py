from setuptools import setup, find_packages

setup(
    name='auto',
    version='1.2.2',
    description="A platform for controling all the robots in Automat's lat ",
    license='See license',
    packages=find_packages(),
    python_requires=">=3.8",
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
        'console_scripts': [],
    },
)