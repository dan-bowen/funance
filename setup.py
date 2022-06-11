from setuptools import setup, find_packages

"""
https://click.palletsprojects.com/en/7.x/setuptools/#setuptools-integration
"""

setup(
    name='funance',
    version='0.1',
    packages=find_packages(where='src'),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        'selenium>=3,<4',
        'click>=8,<9',
        'marshmallow>=3,<4',
        'dash',
        'plotly',
        'pandas',
        'numpy',
        'requests',
        'attrs',
        'python-dateutil',
        'PyYAML'
    ],
    extras_require={
        'dev': [
            'nose2',
            'parameterized',
            'coverage'
        ]
    },
    entry_points='''
        [console_scripts]
        funance=funance.cli.__main__:cli
    ''',
)
