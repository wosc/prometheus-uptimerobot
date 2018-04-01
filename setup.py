"""Export uptimerobot.com monitor results as prometheus.io metrics
"""
from setuptools import setup, find_packages
import glob


setup(
    name='ws.prometheus_uptimerobot',
    version='1.0.0',

    install_requires=[
        'prometheus_client',
        'requests',
        'setuptools',
    ],

    entry_points={
        'console_scripts': [
            'uptimerobot_exporter_cgi = ws.prometheus_uptimerobot.web:cgi',
            'uptimerobot_exporter = ws.prometheus_uptimerobot.web:serve',
        ],
    },

    author='Wolfgang Schnerring <wosc@wosc.de>',
    author_email='wosc@wosc.de',
    license='ZPL 2.1',
    url='https://github.com/wosc/prometheus-uptimerobot',

    description=__doc__.strip(),
    long_description='\n\n'.join(open(name).read() for name in (
        'README.rst',
        'CHANGES.txt',
    )),

    classifiers="""\
License :: OSI Approved :: Zope Public License
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Programming Language :: Python :: Implementation :: CPython
"""[:-1].split('\n'),

    namespace_packages=['ws'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    data_files=[('', glob.glob('*.txt'))],
    zip_safe=False,
)
