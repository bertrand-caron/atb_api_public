from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import urlencode
import yaml
import json
import pickle
from copy import deepcopy
from sys import stderr
import inspect
from sys import stderr
from requests import post
from tempfile import TemporaryFile
from typing import Any, List, Dict, Callable, Optional, Union, Tuple
from functools import reduce

MISSING_VALUE = Exception('Missing value')
INCORRECT_VALUE = Exception('Incorrect value')

ATB_MOLID = Union[str, int]

ATB_OUTPUT = str

API_RESPONSE = Dict[Any, Any]

def stderr_write(a_str) -> None:
    stderr.write('API Client Debug: ' + a_str + '\n')

def deserializer_fct_for(api_format: str) -> Callable[[str], API_RESPONSE]:
    if api_format == 'json':
        deserializer_fct = lambda x: json.loads(x)
    elif api_format == 'yaml':
        deserializer_fct = lambda x: yaml.load(x)
    elif api_format == 'pickle':
        deserializer_fct = lambda x: pickle.loads(x)
    else:
        raise Exception('Incorrect API serialization format.')
    return deserializer_fct

def truncate_str_if_necessary(a_str: str, max_length: int = 1000) -> str:
    if len(a_str) <= max_length:
        return a_str
    else:
        return a_str[:1000] + '...[truncated]'

def concat_dicts(*args: List[Dict[Any, Any]]) -> Dict[Any, Any]:
    return dict(
        reduce(
            lambda acc, e: acc + e,
            [
                list(a_dict.items())
                for a_dict in args
            ],
            [],
        ),
    )

class API(object):
    HOST = 'https://atb.uq.edu.au'
    TIMEOUT = 45
    API_FORMAT = 'yaml'
    ENCODING = 'utf-8'

    def encoded(self, something: Any) -> Union[Dict[bytes, Any], bytes, None]:
        if type(something) == dict:
            return {self.encoded(key): self.encoded(value) for (key, value) in something.items()}
        elif type(something) in (str, int):
            return something.encode(self.ENCODING)
        elif something == None:
            return something
        else:
            raise Exception(
                '''Can't uncode object of type {0}: {1}'''.format(
                    type(something),
                    something,
                )
            )

    def safe_urlopen(self, url: str, data: Union[Dict[str, Any], List[Tuple[str, Any]]] = {}, method: str = 'GET') -> str:
        if isinstance(data, dict):
            data_items = list(data.items())
        elif type(data) in (tuple, list):
            data_items = list(data)
        else:
            raise Exception('Unexpected type: {0}'.format(type(data)))

        data_items += [('api_token', self.api_token), ('api_format', self.api_format)]

        try:
            if method == 'GET':
                url = url + '?' + urlencode(data_items)
                data_items = None
            elif method == 'POST':
                url = url
            else:
                raise Exception('Unsupported HTTP method: {0}'.format(method))
            if self.debug:
                print('Querying: {url}'.format(url=url), file=stderr)

            if method == 'POST' and any([isinstance(value, bytes) or 'read' in dir(value) for (key, value) in data_items]):
                def file_for(content):
                    '''Cast a content object to a file for request.post'''
                    if 'read' in dir(content):
                        return content
                    else:
                        file_handler = TemporaryFile(mode='w+b')
                        file_handler.write(
                            content if isinstance(content, bytes) else str(content).encode(),
                        )
                        file_handler.seek(0) # Rewind the files to future .read()
                        return file_handler

                files=dict(
                    [
                        (key, file_for(value))
                        for (key, value) in data_items
                    ]
                )

                request = post(
                    url,
                    files=files,
                )
                response_content = request.text

                if self.debug:
                    print('INFO: Will send binary data.')
            else:
                response = urlopen(
                    Request(
                        url,
                        data=self.encoded(urlencode(data_items),) if data_items is not None else None,
                    ),
                    timeout=self.timeout,
                )
                if self.api_format == 'pickle':
                    response_content = response.read()
                else:
                    response_content = response.read().decode()
        except HTTPError as e:
            stderr_write('Failed opening url: "{0}{1}{2}". Response was: "{3}"'.format(
                url,
                '?' if data_items else '',
                truncate_str_if_necessary(urlencode(data_items) if data_items else ''),
                e.read(),
            ))
            raise e
        return response_content

    def __init__(self, host: str = HOST, api_token: Optional[str] = None, debug: bool = False, timeout: int = TIMEOUT, api_format: str = API_FORMAT) -> None:
        # Attributes
        self.host = host
        self.api_token = api_token
        self.api_format = api_format
        self.debug = debug
        self.timeout = timeout
        self.deserializer_fct = deserializer_fct_for(api_format)

        # API namespaces
        self.Molecules = Molecules(self)
        self.RMSD = RMSD(self)
        self.Jobs = Jobs(self)
# 

    def deserialize(self, an_object: Any) -> Any:
        try:
            return self.deserializer_fct(an_object)
        except:
            print(an_object)
            raise

class ATB_Mol(object):
    def __init__(self, api, molecule_dict: Dict[str, Any]) -> None:
        self.api = api
        self.molid = molecule_dict['molid']
        self.n_atoms = molecule_dict['atoms']
        self.has_TI = molecule_dict['has_TI']
        self.iupac = molecule_dict['iupac']
        self.common_name = molecule_dict['common_name']
        self.inchi = molecule_dict['inchi']
        self.inchi_key = molecule_dict['inchi_key']
        self.experimental_solvation_free_energy = molecule_dict['experimental_solvation_free_energy']
        self.curation_trust = molecule_dict['curation_trust']
        self.pdb_hetId = molecule_dict['pdb_hetId']
        self.netcharge = molecule_dict['netcharge']
        self.formula = molecule_dict['formula']
        self.is_finished = molecule_dict['is_finished']
        self.rnme = molecule_dict['rnme']
        self.moltype = molecule_dict['moltype']
# 

    def download_file(self, **kwargs) -> Union[None, ATB_OUTPUT]:
        if 'molid' in kwargs: del kwargs['molid']
        return self.api.Molecules.download_file(molid=self.molid, **kwargs)

    def generate_mol_data(self, **kwargs) -> bool:
        if 'molid' in kwargs: del kwargs['molid']
        return self.api.Molecules.generate_mol_data(molid=self.molid, **kwargs)

# 

    def __repr__(self) -> str:
        self_dict = deepcopy(self.__dict__)
        del self_dict['api']
        return yaml.dump(self_dict)

# 

# 


# 

class Jobs(API):
    def __init__(self, api: API) -> None:
        self.api = api

    def url(self, api_endpoint: str) -> str:
        return self.api.host + '/api/current/' + self.__class__.__name__.lower() + '/' + api_endpoint + '.py'

# 

    def get(self, **kwargs: Dict[str, Any]) -> API_RESPONSE:
        return self.api.deserialize(
            self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs),
        )['jobs']

    def new(self, **kwargs: Dict[str, Any]) -> API_RESPONSE:
        return self.api.deserialize(
            self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs),
        )['molids']

    def accept(self, **kwargs: Dict[str, Any]) -> API_RESPONSE:
        return self.api.deserialize(
            self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs),
        )['molids']

    def release(self, **kwargs: Dict[str, Any]) -> API_RESPONSE:
        return self.api.deserialize(
            self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs),
        )['molids']

    def finished(self, molids: List[int] = [], qm_logs: List[str] = [], current_qm_levels: List[int] = [], method: str = 'POST', **kwargs: Dict[str, Any]) -> API_RESPONSE:
        return self.api.deserialize(
            self.api.safe_urlopen(
                self.url(inspect.stack()[0][3]),
                data=(
                    list(kwargs.items())
                    +
                    [('molid', molid) for molid in molids]
                    +
                    [('qm_log', qm_log) for qm_log in qm_logs]
                    +
                    [('current_qm_level', current_qm_level) for current_qm_level in current_qm_levels]
                ),
                method=method,
            ),
        )['accepted_molids']

# 

# 

class RMSD(API):

    def __init__(self, api: API) -> None:
        self.api = api

    def url(self, api_endpoint: str) -> str:
        return self.api.host + '/api/current/' + self.__class__.__name__.lower() + '/' + api_endpoint + '.py'

    def align(self, **kwargs) -> API_RESPONSE:
        assert 'molids' in kwargs or ('reference_pdb' in kwargs and 'pdb_0' in kwargs), MISSING_VALUE
        if 'molids' in kwargs:
            if type(kwargs['molids']) in (list, tuple):
                kwargs['molids'] = ','.join(map(str, kwargs['molids']))
            else:
                assert ',' in kwargs['molids']
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='POST')
        return self.api.deserialize(response_content)

    def matrix(self, **kwargs) -> API_RESPONSE:
        assert 'molids' in kwargs or ('reference_pdb' in kwargs and 'pdb_0' in kwargs), MISSING_VALUE
        if 'molids' in kwargs:
            if type(kwargs['molids']) in (list, tuple):
                kwargs['molids'] = ','.join(map(str, kwargs['molids']))
            else:
                assert ',' in kwargs['molids']
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='POST')
        return self.api.deserialize(response_content)

# 

# 

class Molecules(API):

    def __init__(self, api: API) -> None:
        self.api = api
        self.download_urls = {
            'pdb_aa': ('download_file', dict(outputType='top', file='pdb_allatom_optimised', ffVersion="54A7"),),
            'pdb_allatom_unoptimised': ('download_file', dict(outputType='top', file='pdb_allatom_unoptimised', ffVersion="54A7"),),
            'pdb_ua': ('download_file', dict(outputType='top', file='pdb_uniatom_optimised', ffVersion="54A7"),),
            'yml': ('generate_mol_data', dict(),),
            'mtb_aa': ('download_file', dict(outputType='top', file='mtb_allatom', ffVersion="54A7"),),
            'mtb_ua': ('download_file', dict(outputType='top', file='mtb_uniatom', ffVersion="54A7"),),
            'itp_aa': ('download_file', dict(outputType='top', file='rtp_allatom', ffVersion="54A7"),),
            'itp_ua': ('download_file', dict(outputType='top', file='rtp_uniatom', ffVersion="54A7"),),
        }

    def url(self, api_endpoint: str) -> str:
        return self.api.host + '/api/current/' + self.__class__.__name__.lower() + '/' + api_endpoint + '.py'

    def search(self, **kwargs) -> Any:
        return_type = kwargs['return_type'] if 'return_type' in kwargs else 'molecules'
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='GET')
        data = self.api.deserialize(response_content)
        if return_type == 'molecules':
            return [ATB_Mol(self.api, m) for m in data[return_type]]
        elif return_type == 'molids':
            return data[return_type]
        else:
            raise Exception('Unknow return_type: {0}'.format(return_type))

    def download_file(self, **kwargs: Dict[str, Any]) -> Union[None, ATB_OUTPUT]:

        def write_to_file_or_return(response_content, deserializer_fct) -> Union[None, ATB_OUTPUT]:
            # Either write response to file 'fnme', or return its content
            if 'fnme' in kwargs:
                fnme = str(kwargs['fnme'])
                with open(fnme, 'w' + ('b' if isinstance(response_content, bytes) else 't')) as fh:
                    fh.write(response_content)
                return None
            else:
                return deserializer_fct(response_content)

        if all([key in kwargs for key in ('atb_format', 'molid')]):
            # Construct donwload.py request based on requested file format
            atb_format = str(kwargs['atb_format'])
            call_kwargs = dict([(key, value) for (key, value) in list(kwargs.items()) if key not in ('atb_format',)])
            api_endpoint, extra_parameters = self.download_urls[atb_format]
            url = self.url(api_endpoint)
            response_content = self.api.safe_urlopen(url, data=concat_dicts(extra_parameters, call_kwargs), method='GET')
            deserializer_fct = (self.api.deserializer_fct if atb_format == 'yml' else (lambda x: x))
        else:
            # Forward all the keyword arguments to download_file.py
            response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='GET')
            deserializer_fct = lambda x: x
        return write_to_file_or_return(response_content, deserializer_fct)

    def duplicated_inchis(self, **kwargs) -> API_RESPONSE:
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='GET')
        return self.api.deserialize(response_content)['inchi_key']

    def generate_mol_data(self, **kwargs) -> API_RESPONSE:
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='GET')
        return self.api.deserialize(response_content)

# 

    def molid(self, molid: ATB_MOLID = None) -> ATB_Mol:
        parameters = dict(molid=molid)
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=parameters, method='GET')
        data = self.api.deserialize(response_content)
        return ATB_Mol(self.api, data['molecule'])

    def structure_search(self, method: str = 'POST', **kwargs) -> API_RESPONSE:
        assert all([ arg in kwargs for arg in ('structure', 'netcharge', 'structure_format') ])
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method=method)
        return self.api.deserialize(response_content)

# 

    def submit(self, request='POST', **kwargs) -> API_RESPONSE:
        assert all([ arg in kwargs for arg in ('netcharge', 'pdb', 'public', 'moltype') ])
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method=request)
        return self.api.deserialize(response_content)

# 

def test_api_client():
    api = API(api_token='<put your token here>', debug=True, api_format='yaml', host='https://atb.uq.edu.au')

    TEST_RMSD = True
    ETHANOL_MOLIDS = [15608, 23009, 26394]

# 

    if TEST_RMSD:
        print(api.RMSD.matrix(molids=ETHANOL_MOLIDS))
        print(api.RMSD.align(molids=ETHANOL_MOLIDS[0:2]))
        print(
            api.RMSD.align(
                reference_pdb=api.Molecules.download_file(atb_format='pdb_aa', molid=ETHANOL_MOLIDS[0]),
                pdb_0=api.Molecules.download_file(atb_format='pdb_aa', molid=ETHANOL_MOLIDS[1]),
            ),
        )

    print(api.Molecules.search(any='cyclohexane', curation_trust=0))
    print(api.Molecules.search(any='cyclohexane', curation_trust='0,2', return_type='molids'))
    mols = api.Molecules.search(any='cyclohexane', curation_trust='0,2')
    print([mol.curation_trust for mol in mols])

    water_molecules = api.Molecules.search(formula='H2O')
    print(water_molecules)
    for mol in water_molecules:
        print(mol.iupac, mol.molid)
    #print(water_molecules[0].download_file(fnme='test.mtb', atb_format='mtb_aa'))
    print(api.Molecules.download_file(atb_format='yml', molid=21))
    print(api.Molecules.download_file(atb_format='mtb_aa', molid=21, refresh_cache=True))

    exit()

# 

if __name__ == '__main__':
    test_api_client()
