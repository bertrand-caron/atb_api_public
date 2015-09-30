# Automated Topology Builder (ATB) API Version 0.1

Author: Bertrand Caron

## Installation

```
git clone http://scmb-gitlab.biosci.uq.edu.au/ATB/atb_api_public.git
cd atb_api_public
make install-user # Try running 'python setup.py install' if it fails
```

## Example use

```
from atb_api import API
api = API(api_token='<your_api_token_here>') # Send an email to the ATB administrators to request an API token
molecules = api.Molecules.search(any='ethanol')

for molecule in molecules:
    print(molecule.inchi)
    pdb_path = '{molid}.pdb'.format(molid=molecule.molid)
    molecule.download_file(fnme=pdb_path, format='pdb')

    with open(pdb_path) as fh:
        print(fh.read())
```
		
