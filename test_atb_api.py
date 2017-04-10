from atb_api import API

api = API(api_token='<your_api_token_here>', api_format='yaml')
# Send an email to the ATB administrators to request an API token
molecules = api.Molecules.search(any='ethanol', match_partial=False)

for molecule in molecules:
    print(molecule.inchi)
    pdb_path = '{molid}.pdb'.format(molid=molecule.molid)
    molecule.download_file(fnme=pdb_path, atb_format='pdb_aa')

    with open(pdb_path) as fh:
        pdb_str = fh.read()
        print(pdb_str)

print(api.Molecules.structure_search(structure_format='pdb', structure=pdb_str, netcharge='*'))

print(api.Molecules.molid(molid=21))

# This will and should fail, as we are trying to resubmit a molecule already in the database.
try:
    print(api.Molecules.submit(pdb=pdb_str, netcharge=0, moltype='heteromolecule', public=True))
except Exception as e:
    print(e.read())
