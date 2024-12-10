<!--
Copyright (c) 2022-2023 Geosiris.
SPDX-License-Identifier: Apache-2.0
-->
# Etpclient
==========


[![License](https://img.shields.io/pypi/l/etpclient)](https://github.com/geosiris-technologies/etpclient-python/blob/main/LICENSE)
[![Documentation Status](https://readthedocs.org/projects/etpclient-python/badge/?version=latest)](https://etpclient-python.readthedocs.io/en/latest/?badge=latest)
[![Python CI](https://github.com/geosiris-technologies/etpclient-python/actions/workflows/ci-tests.yml/badge.svg)](https://github.com/geosiris-technologies/etpclient-python/actions/workflows/ci-tests.yml)
![Python version](https://img.shields.io/pypi/pyversions/etpclient)
[![PyPI](https://img.shields.io/pypi/v/etpclient)](https://badge.fury.io/py/etpclient)
![Status](https://img.shields.io/pypi/status/etpclient)
[![codecov](https://codecov.io/gh/geosiris-technologies/etpclient-python/branch/main/graph/badge.svg)](https://codecov.io/gh/geosiris-technologies/etpclient-python)


## Installation : 

Poetry is required to use the client. [Poetry documentation](https://python-poetry.org/docs/)

```bash
poetry update
poetry install
```

## Connection to a server : 

You must fill a configuration file (see. config/sample.yml):
```yaml
url: wss://XXX
port: 80
username: XXX
password: XXX
additional-headers:
  - data-partition-id: osdu

token-url: https://XXX
token-grant-type: client_credentials
token-scope: openid profile email
token-refresh_token: XXX
```

Then you must set an environment variable to refer it : **INI_FILE_PATH**.
Or you can fill a .env file : 
```dotenv
INI_FILE_PATH=config/sample.yml
CLIENT_ID=XXX
CLIENT_SECRET=XXX
```

## Sample commands :

### Interactive client : 

```bash
poetry run client
```


### Run a specific script (here *download_xmls* that downloads all xml from a server) : 
```bash
poetry run script download_xmls
```

### Run a pre-written script :
```bash
poetry run file_script .\script_sample.txt
```
Example of a script file : 
```bash
getresources eml:///

# a commented line, a line starting with a '#' will not be executed

getdataspaces

quit
```


## ETP supported commands : 

When the *interactive* client is connected you can send your request (this commands are the same for the *script files*).

This is the help menu :
```bash
[XXX] : replace XXX with your value
[XXX=Y] : replace XXX with your value, default is Y
[[XXX]] : optional parameter

[URI] for dataspaces can sometimes be set as "eml:///dataspace('DATASPACE_NAME')" but also with only the DATASPACE_NAME.

    Help : show this menu

    Quit : hard quit (no CloseSession sent)
    CloseSession : close this session

    Authorize             [ [TOKEN] | ( [USERNAME] [PASSWORD]) ]
    RequestSession

    GetDataArrayMetadata  [URI] [PATH_IN_RESOURCE]
    GetDataArray          [URI] [PATH_IN_RESOURCE]
    GetDataSubArray       [URI] [PATH_IN_RESOURCE] [START] [COUNT]
    PutDataArray          [DATASPACE_NAME] [EPC_FILE_PATH] [H5_FILE_PATH] [[UUIDS]]*
    PutDataArray_filter   [DATASPACE_NAME] [EPC_FILE_PATH] [H5_FILE_PATH] [[REGEX_TYPE_FILTER]]

    GetDataObject         [URI_1] [...] [URI_N]
    DeleteDataObjects     [URI_1] [...] [URI_N]
    PutDataObject         [FILE_PATH] [[DATASPACE_NAME]] [[UUIDS]]*

    GetResources          [[uri=eml:/// or notUri=DataspaceName]] [[depth=1]] [[SCOPE]]
    GetDeletedResources   [[uri=eml:/// or notUri=DataspaceName]] [[DELETE_TIME_FILTER]] [[DATA_OBJECT_TYPES]]*

    GetDataspaces
    PutDataspace          [NAME]
    DeleteDataspace       [NAME]*

    Download              [OUTPUT_FILE_PATH] [DATASPACE_NAME]
    DownloadObject        [OUTPUT_FOLDER_PATH] [URI]

    GetSupportedTypes     [URI] [[COUNT=True]] [[RETURN_EMPTY_TYPES=True]] [[SCOPE=Self]]
```

## Configuration

It is possible to change the "capabilities" of your client in the prefilled RequestSession object in [etpclient/etp/requester.py](https://github.com/geosiris-technologies/etpclient-python/blob/main/etpclient/etp/requester.py#L180)

To add/remove supported protocols and request, modify the file [etpclient/etp/serverprotocols.py](https://github.com/geosiris-technologies/etpclient-python/blob/main/etpclient/etp/serverprotocols.py#L166). Do not forget to decorate your protocols to allow the class ETPConnection to use your protocol.
Example : 
```python
@ETPConnection.on(CommunicationProtocol.CORE)
class myCoreProtocol(CoreHandler):
    ...
```