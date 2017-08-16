import requests

def test_yo_health_response(yo_http_server):
    """Test /health returns a valid response direct from yo"""
    url      = '%s/health' % yo_http_server
    response = requests.get(url)
    response.raise_for_status()

#def test_nginx_health_response(yo_nginx_server):
#    """Test /health returns a valid response from nginx"""
#    url      = '%s/health' % yo_nginx_server
#    response = requests.get(url)
#    response.raise_for_status()
