#-*- coding:utf-8 -*-

from setuptools import setup

setup(
    name='echidna-parade',
    version='0.1.1',
    description='Meta-tool to test a contract with various configs, using Echidna processes ("parade" is the proper name for a group of echidna)',
    long_description_content_type="text/markdown",    
    long_description=open('README.md').read(),
    packages=['echidna_parade',],
    license='MIT',
    entry_points="""
    [console_scripts]
    echidna-parade = echidna_parade.echidna_parade:main
    """,
    keywords='echidna smart-contracts testing fuzzing swarm test-diversity',
    test_suite='nose.collector',
    tests_require=['nose'],
    classifiers=[
      "Intended Audience :: Developers",
      "Development Status :: 4 - Beta",
      "Programming Language :: Python :: 2",
      "Programming Language :: Python :: 3",
      ],
    install_requires=[
      'pyyaml',
      'slither-analyzer',
      'crytic-compile'
    ],
    url='https://github.com/agroce/echidna-parade',
)
