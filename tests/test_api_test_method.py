import jsonrpcclient

from jsonrpcclient.http_client import HTTPClient

def test_healthcheck():
    client = HTTPClient('http://localhost:8080')
    print(client.request('yo.api_test_method'))

if __name__=='__main__':
   test_healthcheck()
