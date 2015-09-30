import urllib2
from urllib import urlencode
import yaml
from copy import deepcopy
from sys import stderr
import inspect

MISSING_VALUE = Exception('Missing value')
INCORRECT_VALUE = Exception('Incorrect value')

def stderr_write(a_str):
    stderr.write('API Client Debug: ' + a_str + '\n')

class API(object):

    HOST = 'http://compbio.biosci.uq.edu.au/atb'
    TIMEOUT = 45

    def safe_urlopen(self, url, data={}, method='GET'):
        data['api_token'] = self.api_token
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
            stderr_write("Failed opening url: {0}".format(url))
            if e and 'fp' in e.__dict__: stderr_write( "Response was: {0}".format(e.fp.read()) )
            raise e
        return response

    def __init__(self, host=HOST, api_token=None, debug=False, timeout=TIMEOUT):
        self.host = host
        self.api_token = api_token
        self.debug = debug
        self.timeout = timeout
        self.Molecules = Molecules(self)
# 

# 

# 

# 

# 

class Molecules(API):

    def __init__(self, api):
        self.api = api
        self.download_urls = {
            'pdb': ( self.api.host + '/download.py', dict(outputType='top', dbfile='pdb_allatom_optimised') ),
            'yml': ( self.api.host + '/api/current/molecules/generate_mol_data.py', dict() ),
            'mtb_ua': ( self.api.host + '/download.py', dict(outputType='top', file='mtb_uniatom', ffVersion="54A7") ),
        }

    def url(self, api_endpoint):
        return self.api.host + '/api/current/' + self.__class__.__name__.lower() + '/' + api_endpoint + '.py'

    def search(self, **kwargs):
        response = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='GET')
        data = yaml.load(response.read())
        return map(lambda m: ATB_Mol(self.api, m), data['molecules'])

    def download_file(self, fnme=None, format=None, molid=None):
        if not (fnme and format): return
        parameters = dict(molid=molid)
        url, extra_parameters = self.download_urls[format]
        response = self.api.safe_urlopen(url, data=dict(parameters.items() + extra_parameters.items()), method='GET')
        with open(fnme, 'w') as fh:
            fh.write( response.read() )

# 

    def molid(self, molid=None):
        parameters = dict(molid=molid)
        response = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=parameters, method='GET')
        data = yaml.load(response.read())
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
        self.exp_solv_free_energy = molecule_dict['exp_solv_free_energy']

    def download_file(self, fnme=None, format=None):
        self.api.Molecules.download_file(fnme=fnme, format=format, molid=self.molid)

# 

    def __repr__(self):
        self_dict = deepcopy(self.__dict__)
        del self_dict['api']
        return yaml.dump(self_dict)

if __name__ == '__main__':
    api = API(api_token='<put your token here>', debug=True)

    print api.Molecules.search(any='water', curation_trust=0)

# 
