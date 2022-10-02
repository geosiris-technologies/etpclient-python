etpclient
==========


[![License](https://img.shields.io/pypi/l/etpclient)](https://github.com/geosiris-technologies/etpclient-python/blob/main/LICENSE)
[![Documentation Status](https://readthedocs.org/projects/etpclient-python/badge/?version=latest)](https://etpclient-python.readthedocs.io/en/latest/?badge=latest)
[![Python CI](https://github.com/geosiris-technologies/etpclient-python/actions/workflows/ci-tests.yml/badge.svg)](https://github.com/geosiris-technologies/etpclient-python/actions/workflows/ci-tests.yml)
![Python version](https://img.shields.io/pypi/pyversions/etpclient)
[![PyPI](https://img.shields.io/pypi/v/etpclient)](https://badge.fury.io/py/etpclient)
![Status](https://img.shields.io/pypi/status/etpclient)
[![codecov](https://codecov.io/gh/geosiris-technologies/etpclient-python/branch/main/graph/badge.svg)](https://codecov.io/gh/geosiris-technologies/etpclient-python)



poetry run python .\src\etpclient\main.py --host MY_HOST --port 80 --sub-path etp  -t https://rddms.centralus.cloudapp.azure.com/rest/Reservoir/v1/auth/token

poetry run python .\src\etpclient\main.py --host 127.0.0.1 --port 17000 --sub-path etp --username login --password passwordTest

poetry run python .\src\etpclient\main.py --host 127.0.0.1 --port 5432 --username testerlogin --password passwordtester
