import time
import hashlib
import docker


def gen_pw():
    """Hacky as hell but works"""
    fd = open('/dev/urandom', 'rb')
    data = fd.read(32)
    fd.close()
    return hashlib.sha256(data).hexdigest()


class MySQLServer:
    def __init__(self, db_name=None, db_user=None, db_pass=None):
        self.client = docker.from_env()
        self.cenv = {
            'MYSQL_USER': db_user,
            'MYSQL_PASSWORD': db_pass,
            'MYSQL_DATABASE': db_name,
            'MYSQL_ROOT_PASSWORD': gen_pw()
        }
        self.container = self.client.containers.run(
            'mysql',
            detach=True,
            environment=self.cenv,
            ports={'3306/tcp': ('127.0.0.1', 3306)},
            tmpfs={'/var/lib/mysql': ''},
            remove=True)

    def wait(self):
        while True:
            for l in self.container.logs(
                    stdout=True, stderr=True, stream=True):
                log_entry = l.decode('utf-8')
                if 'MySQL init process done' in log_entry:
                    time.sleep(1)
                    return

    def stop(self):
        self.container.stop()
