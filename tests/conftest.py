import pytest
import requests

from requests.exceptions import (
    ConnectionError,
)

def is_responsive(url):
    """Check if something responds to ``url``."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
    except ConnectionError:
        return False

@pytest.fixture(scope='session')
def yo_http_server(docker_ip, docker_services):
    """Ensure that yo itself is up and responsive."""
    url = 'http://%s:%s' % (docker_ip, docker_services.port_for('yo',9000))
    docker_services.wait_until_responsive(
       timeout=30.0, pause=0.1,
       check=lambda: is_responsive(url)
    )
    return url

@pytest.fixture(scope='session')
def yo_nginx_server(docker_ip, docker_services):
    """Ensure that the nginx reverse proxy inside the container is up."""
    url = 'http://%s:%s' % (docker_ip, docker_services.port_for('yo',8080))
    docker_services.wait_until_responsive(
       timeout=30.0, pause=0.1,
       check=lambda: is_responsive(url)
    )
    return url
