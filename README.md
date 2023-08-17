<!--
Copyright (c) 2022-2023 Geosiris.
SPDX-License-Identifier: Apache-2.0
-->
# Etpclient

## Installation : 

Poetry is required to use the client. [Poetry documentation](https://python-poetry.org/docs/)

```bash
poetry update
poetry install
```

## Sample commands :

```bash
poetry run python client --host RDDMS_HOST --port 9002 -t MY_TOKEN

poetry run python client --host MY_HOST --port 80 --sub-path etp -t MY_TOKEN

poetry run python client --host 127.0.0.1 --port 17000 --sub-path etp --username login --password passwordTest

poetry run python client --host 127.0.0.1 --port 5432 --username testerlogin --password passwordtester
```


## ETP supported commands : 

When the client is connected you can send your request.

This is the help menu :
```bash
[XXX] : replace XXX with your value
[XXX=Y] : replace XXX with your value, default is Y
[[XXX]] : optional parameter

Help : show this menu

Quit : hard quit (no CloseSession sent)
CloseSession : close this session

GetDataArrayMetadata  [URI] [PATH_IN_RESOURCE]
GetDataArray          [URI] [PATH_IN_RESOURCE]
GetDataSubArray       [URI] [PATH_IN_RESOURCE] [START] [COUNT]
PutDataArray          [[UUIDS]]* [DATASPACE_NAME] [EPC_FILE_PATH] [H5_FILE_PATH]

GetDataObject         [URI_1] [...] [URI_N]
PutDataObject         [FILE_PATH] [[DATASPACE_NAME]]
GetResources          [[uri=eml:/// or notUri=DataspaceName]] [[depth=1]] [[SCOPE]]

GetDataspaces
PutDataspace          [NAME]
DeleteDataspace       [NAME]
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