import urllib2
from urllib import urlencode
import yaml
import json
import pickle
from copy import deepcopy
from sys import stderr
import inspect

MISSING_VALUE = Exception('Missing value')
INCORRECT_VALUE = Exception('Incorrect value')

def stderr_write(a_str):
    stderr.write('API Client Debug: ' + a_str + '\n')

def serializer(api_format):
    if api_format == 'json':
        serializer = json.loads
    elif api_format == 'yaml':
        serializer = yaml.load
    elif api_format == 'pickle':
        serializer = pickle.loads
    else:
        raise Exception('Incorrect API serialization format.')
    return serializer

class API(object):

    HOST = 'https://atb.uq.edu.au'
    TIMEOUT = 45
    API_FORMAT = 'yaml'

    def safe_urlopen(self, url, data={}, method='GET'):
        data['api_token'] = self.api_token
        data['api_format'] = self.api_format
        try:
            if method == 'GET':
                url = url + '?' + urlencode(data)
                data = None
            elif method == 'POST':
                url = url
                data = data
            else:
                raise Exception('Unsupported HTTP method: {0}'.format(method))
            if self.debug: print 'Querying: {url}'.format(url=url)
            response = urllib2.urlopen(url, timeout=self.timeout, data=urlencode(data) if data else None)
        except Exception, e:
            stderr_write("Failed opening url: {0}{1}{2}".format(
                url,
                '?' if data else '',
                urlencode(data) if data else '',
            ))
            if e and 'fp' in e.__dict__: stderr_write( "Response was: {0}".format(e.fp.read()) )
            raise e
        return response

    def __init__(self, host=HOST, api_token=None, debug=False, timeout=TIMEOUT, api_format=API_FORMAT):
        self.host = host
        self.api_token = api_token
        self.api_format = api_format
        self.debug = debug
        self.timeout = timeout
        self.Molecules = Molecules(self)
        self.serializer = serializer(api_format)
# 

# 

# 

# 

# 

class Molecules(API):

    def __init__(self, api):
        self.api = api
        self.download_urls = {
            'pdb': ( 'download_file', dict(outputType='top', file='pdb_allatom_optimised', ffVersion="54A7") ),
            'yml': ( 'generate_mol_data', dict() ),
            'mtb_aa': ( 'download_file', dict(outputType='top', file='mtb_allatom', ffVersion="54A7") ),
            'mtb_ua': ( 'download_file', dict(outputType='top', file='mtb_uniatom', ffVersion="54A7") ),
        }

    def url(self, api_endpoint):
        return self.api.host + '/api/current/' + self.__class__.__name__.lower() + '/' + api_endpoint + '.py'

    def search(self, **kwargs):
        response = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='GET')
        data = self.api.serializer(response.read())
        return map(lambda m: ATB_Mol(self.api, m), data['molecules'])

    def download_file(self, fnme=None, format=None, molid=None):
        if not (fnme and format): return
        parameters = dict(molid=molid)
        api_endpoint, extra_parameters = self.download_urls[format]
        url = self.url(api_endpoint)
        response = self.api.safe_urlopen(url, data=dict(parameters.items() + extra_parameters.items()), method='GET')
        with open(fnme, 'w') as fh:
            fh.write( response.read() )

# 

    def molid(self, molid=None):
        parameters = dict(molid=molid)
        response = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=parameters, method='GET')
        data = self.api.serializer(response.read())
        return ATB_Mol(self.api, data['molecule'])

# 

    def submit(self, **kwargs):
        assert all([ arg in kwargs for arg in ('netcharge', 'pdb', 'public', 'moltype') ])
        response = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs)
        return response.read()

    def submit_TI(self, **kwargs):
        assert all([ arg in kwargs for arg in ('fe_method', 'fe_solvent', 'unique_id', 'molid', 'target_uncertainty') ])
        response = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs)
        return response.read()

# 

class ATB_Mol(object):
    def __init__(self, api, molecule_dict):
        self.api = api
        self.molid = molecule_dict['molid']
        self.n_atoms = molecule_dict['atoms']
        self.has_TI = molecule_dict['has_TI']
        self.iupac = molecule_dict['iupac']
        self.common_name = molecule_dict['common_name']
        self.inchi = molecule_dict['InChI']
        self.experimental_solvation_free_energy = molecule_dict['experimental_solvation_free_energy']
        self.curation_trust = molecule_dict['curation_trust']

    def download_file(self, fnme=None, format=None):
        self.api.Molecules.download_file(fnme=fnme, format=format, molid=self.molid)

# 

    def __repr__(self):
        self_dict = deepcopy(self.__dict__)
        del self_dict['api']
        return yaml.dump(self_dict)

if __name__ == '__main__':
    api = API(api_token='<put your token here>', debug=True, api_format='pickle')

    print api.Molecules.search(any='cyclohexane', curation_trust=0)
    print api.Molecules.search(any='cyclohexane', curation_trust='0,2')
    mols = api.Molecules.search(any='cyclohexane', curation_trust='0,2')
    print [mol.curation_trust for mol in mols]

# 
