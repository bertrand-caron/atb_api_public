from sys import version_info
from distutils.core import setup

if version_info < (3,):
    package_dir = {'': 'src2'}
else:
    package_dir = {'': 'src3'}

setup(
    name='atb_api_public',
    version='0.1',
    description='An API (Application Programming Interface) to interact with the ATB (http://compbio.biosci.uq.edu.au/atb)',
    author='Bertrand Caron',
    author_email='b.caron@uq.edu.au',
    py_modules=['atb_api'],
)
