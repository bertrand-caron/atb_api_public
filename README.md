# Automated Topology Builder (ATB) API Version 0.1

Author: Bertrand Caron

## Installation

```
git clone git@github.com:bertrand-caron/atb_api_public.git
cd atb_api_public
make install-user # Try running 'python setup.py install' if it fails
```

## Example use

```
from atb_api import API
# Send an email to the ATB administrators to request an API token
api = API(api_token='<your_api_token_here>')
molecules = api.Molecules.search(any='ethanol', match_partial=False)

for molecule in molecules:
    print(molecule.inchi)
    pdb_path = '{molid}.pdb'.format(molid=molecule.molid)
    molecule.download_file(fnme=pdb_path, atb_format='pdb_aa') # Get All-Atom (aa) PDB

    with open(pdb_path) as fh:
        print(fh.read())
```
		
A longer and more detailed example file is provided in `test_atb_api.py`.
