from setuptools import setup, find_packages

setup(
    name='auto',
    version='0.1.0',
    description="A platform for controling all the robots in Automat's lat ",
    license='See license',
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "paramiko==2.8.1", # higher version yields misleading exception about RSA keys.
        "scp",
        "notebook",
    ],
    entry_points={ # create scripts and add to sys.PATH
        'console_scripts': [
            "run_sdwf = scripts.run_sdwf:main",
        ],
    },
)