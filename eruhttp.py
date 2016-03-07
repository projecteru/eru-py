import json
import socket
import urllib
import urlparse
from urlparse import urljoin

import requests
import websocket


class EruException(Exception):

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return '<EruException code:%s message:%s>' % (self.code, self.message)

    __repr__ = __str__
    __unicode__ = __str__


class EruClient(object):

    def __init__(self, url, timeout=5, username='', password=''):
        self.url = url
        self.timeout = timeout
        self.username = username
        self.password = password
        self.session = requests.Session()

    def request(self, url, method='GET', params=None, data=None, json=None, expected_code=200):
        if params is None:
            params = {}
        if data is None:
            data = {}

        params.setdefault('start', 0)
        params.setdefault('limit', 20)
        target_url = urljoin(self.url, url)
        try:
            resp = self.session.request(method=method,
                                        url=target_url,
                                        params=params,
                                        data=data,
                                        json=json,
                                        timeout=self.timeout)
            r = resp.json()
            if resp.status_code != expected_code:
                raise EruException(resp.status_code, r.get('error', 'Unknown error'))
            return r
        except requests.exceptions.ReadTimeout:
            raise EruException(0, 'Read timeout')
        except requests.exceptions.ConnectionError:
            raise EruException(0, 'Connection refused')
        except Exception as e:
            raise EruException(0, e.message)

    def request_websocket(self, url, as_json=True, params=None):
        # .......
        ws_url = urljoin(self.url, url).replace(
            'http://', 'ws://').replace('https://', 'wss://')
        if params is None:
            params = {}
        query = urllib.urlencode(params)
        ws_url = urlparse.urlparse(ws_url)._replace(query=query).geturl()
        ws = websocket.create_connection(ws_url)
        while True:
            try:
                line = ws.recv()
                if not line:
                    continue
                if as_json:
                    line = json.loads(line)
                yield line
            except (websocket.WebSocketException, socket.error):
                break

    def post(self, url, **kwargs):
        return self.request(url, 'POST', **kwargs)

    def put(self, url, **kwargs):
        return self.request(url, 'PUT', **kwargs)

    def get(self, url, **kwargs):
        return self.request(url, 'GET', **kwargs)

    def delete(self, url, **kwargs):
        return self.request(url, 'DELETE', **kwargs)

    def register_app_version(self, version, git, token, appyaml, raw=False):
        """Register an app into ERU.

        :param name: the name of app.
        :param version: specific version of app, from git revision.
        :param git: git endpoint, used to clone code.
        :param token: git token, if repository is not public, need this to clone code.
        :param appyaml: file content of app.yaml, in dictionary.
        :type appyaml: ``dict``
        """
        url = '/api/app/register/'
        payload = {
            'version': version,
            'git': git,
            'token': token,
            'appyaml': appyaml,
        }
        if raw:
            payload['raw'] = True

        return self.post(url, json=payload, expected_code=201)

    def set_app_env(self, name, env, **kwargs):
        """Set environment key-value pair to app.

        e.g.::

            >>> eru_client.set_app_env('appname', 'prod', MYSQL_HOST='localhost', MYSQL_USER='user')
            {'r': 0, 'msg': 'ok'}

        :param name: the name of app.
        :param env: the name of environment, like `prod` or `test`.
        :param kwargs: the key-value pairs, like MYSQL_HOST=localhost, MYSQL_USER=user.
        """
        url = '/api/app/{0}/env/'.format(name)
        payload = {'env': env}
        payload.update(kwargs)
        return self.put(url, json=payload)

    def delete_app_env(self, name, env):
        url = '/api/app/{0}/env/'.format(name)
        payload = {'env': env}
        return self.delete(url, json=payload)

    def list_app_env_content(self, name, env):
        """List all key-value pairs from app with specific environment.
        e.g.::

            >>> eru_client.list_app_env_content('appname', 'prod')
            {'MYSQL_HOST': 'localhost', 'MYSQL_USER': 'user'}

        :param name: the name of app.
        :param env: the name of environment.
        """
        url = '/api/app/{0}/env/'.format(name)
        params = {'env': env}
        return self.get(url, params=params)

    def list_app_env_names(self, name):
        """List all available environments for app.

        e.g.::

            >>> eru_client.list_app_env_names('appname')
            {'r': 0, 'msg': 'ok', 'data': ['prod', 'test']}

        :param name: the name of app.
        """
        url = '/api/app/{0}/listenv/'.format(name)
        return self.get(url)

    def get_app(self, name):
        """Get app from name.

        :param name: the name of app.
        """
        url = '/api/app/{0}/'.format(name)
        return self.get(url)

    def list_apps(self, start=0, limit=20):
        url = '/api/app/'
        params = {'start': start, 'limit': limit}
        return self.get(url, params=params)

    def get_version(self, name, version):
        """Get version by name and version.

        :param name: the name of app.
        :param version: specific version of app, from git revision.
        """
        url = '/api/app/{0}/{1}/'.format(name, version)
        return self.get(url)

    def list_app_containers(self, name, start=0, limit=20):
        """List all containers of this app.

        :param name: the name of app.
        """
        url = '/api/app/{0}/containers/'.format(name)
        params = {'start': start, 'limit': limit}
        return self.get(url, params=params)

    def list_app_tasks(self, name, start=0, limit=20):
        """List all containers of this app.

        :param name: the name of app.
        """
        url = '/api/app/{0}/tasks/'.format(name)
        params = {'start': start, 'limit': limit}
        return self.get(url, params=params)

    def list_app_images(self, name, start=0, limit=20):
        """List all containers of this app.

        :param name: the name of app.
        """
        url = '/api/app/{0}/images/'.format(name)
        params = {'start': start, 'limit': limit}
        return self.get(url, params=params)

    def list_version_tasks(self, name, version, start=0, limit=20):
        """List all containers of this app.

        :param name: the name of app.
        """
        url = '/api/app/{0}/{1}/tasks/'.format(name, version)
        params = {'start': start, 'limit': limit}
        return self.get(url, params=params)

    def list_version_containers(self, name, version, start=0, limit=20):
        """List all containers of this app.

        :param name: the name of app.
        """
        url = '/api/app/{0}/{1}/containers/'.format(name, version)
        params = {'start': start, 'limit': limit}
        return self.get(url, params=params)

    def deploy_private(self, pod_name, app_name, ncore,
            ncontainer, version, entrypoint, env, network_ids, ports=None,
            host_name=None, raw=False, image='', spec_ips=None, args=None,
            callback_url=''):
        """Deploy app on pod, using cores that are private.

        e.g.::

            >>> eru_client.deploy_private('pod', 'appname', 1.4, \
            ...     10, '3def4a6', 'web', 'prod', [1, 2])
            {'r': '0', 'msg': 'ok'}

        :param pod_name: target pod name which containers will be deployed.
        :param app_name: the name of app.
        :param ncore: how many cores one containers requires, like 1, 2, 1.4.
        :type ncore: ``float``
        :param ncontainer: how many containers to deploy.
        :param version: specific version of app, from git revision.
        :param entrypoint: which entrypoint to run this container.
        :param env: which env to set to container, once set, all key-value pairs under `env` will be passed to container.
        :param network_ids: ids of network to bind to container.
        :type network_ids: ``list``
        :param ports: ports for container.
        :type ports: ``list``
        :param host_name: if specified, containers will be only deployed to this host.
        """
        if raw and not image:
            raise EruException('raw and image must be set together.')

        if ports is None:
            ports = []
        if args is None:
            args = []

        url = '/api/deploy/private/'
        payload = {
            'podname': pod_name,
            'appname': app_name,
            'ncore': ncore,
            'ncontainer': ncontainer,
            'version': version,
            'entrypoint': entrypoint,
            'env': env,
            'networks': network_ids,
            'ports': ports,
            'args': args,
            'callback_url': callback_url,
        }
        if raw and image:
            payload['raw'] = True
            payload['image'] = image

        if host_name:
            payload['hostname'] = host_name

        if spec_ips:
            payload['spec_ips'] = spec_ips

        return self.post(url, json=payload)

    def deploy_public(self, pod_name, app_name, ncontainer,
            version, entrypoint, env, network_ids, ports=None,
            raw=False, image='', spec_ips=None, args=None, callback_url=''):
        """Deploy app on pod, can't bind any cores to container."""
        if raw and not image:
            raise EruException('raw and image must be set together.')

        if ports is None:
            ports = []
        if args is None:
            args = []

        url = '/api/deploy/public/'
        payload = {
            'podname': pod_name,
            'appname': app_name,
            'ncontainer': ncontainer,
            'version': version,
            'entrypoint': entrypoint,
            'env': env,
            'networks': network_ids,
            'ports': ports,
            'args': args,
            'callback_url': callback_url,
        }
        if raw and image:
            payload['raw'] = True
            payload['image'] = image

        if spec_ips:
            payload['spec_ips'] = spec_ips

        return self.post(url, json=payload)

    def build_image(self, pod_name, app_name, base, version):
        """Build docker image for app.

        e.g.::

            >>> eru_client.build_image('pod', 'appname', \
            ...     'docker-registry.intra.hunantv.com/nbeimage/ubuntu:python-2015.05.12', '3d4fe6a')
            {'r': 0, 'msg': 'ok', 'task': 10001, 'watch_key': 'eru:task:result:10001'}

        :param pod_name: target pod name which containers will be deployed.
        :param app_name: the name of app.
        :param base: which image to use as base, will be like `FROM base` in dockerfile.
        :param version: specific version of app.
        """
        url = '/api/deploy/build/'
        payload = {
            'podname': pod_name,
            'appname': app_name,
            'base': base,
            'version': version,
        }
        return self.post(url, json=payload)

    def build_log(self, task_id):
        """Get build log for task_id. returns a generator"""
        url = '/websockets/tasklog/{0}/'.format(task_id)
        return self.request_websocket(url)

    def container_log(self, container_id, stdout=0, stderr=0, tail=0):
        """Get container log. returns a generator.

        :param container_id: container_id of container.
        :param stdout: if set, will get stdout logs.
        :param stderr: if set, will get stderr logs.
        :param tail: if set, `tail` lines will be shown, just like tail -n.
        """
        url = '/websockets/containerlog/{0}/'.format(container_id)
        params = {
            'stdout': stdout,
            'stderr': stderr,
            'tail': tail,
        }
        return self.request_websocket(url, as_json=False, params=params)

    def offline_version(self, pod_name, app_name, version):
        """Offline specific version of app."""
        url = '/api/deploy/rmversion/'
        payload = {
            'podname': pod_name,
            'appname': app_name,
            'version': version,
        }
        return self.post(url, json=payload)

    def remove_containers(self, container_ids):
        """Remove all containers in `container_ids`"""
        url = '/api/deploy/rmcontainers/'
        payload = {'cids': container_ids}
        return self.post(url, json=payload)

    def version(self):
        url = '/'
        return self.get(url, as_json=False)

    def kill_container(self, container_id):
        """Kill a container, it will be shown as dead in ERU."""
        url = '/api/container/{0}/kill/'.format(container_id)
        return self.put(url)

    def cure_container(self, container_id):
        """Cure a container, it will be shown as alive in ERU."""
        url = '/api/container/{0}/cure/'.format(container_id)
        return self.put(url)

    def start_container(self, container_id):
        """Start a container."""
        url = '/api/container/{0}/start/'.format(container_id)
        return self.put(url)

    def stop_container(self, container_id):
        """Stop a container."""
        url = '/api/container/{0}/stop/'.format(container_id)
        return self.put(url)

    def poll_container(self, container_id):
        """Poll container status.
        status 1 means alive, otherwise dead.

        e.g.::

            >>> eru_client.poll_container('b84fb25bd99b')
            {'r': 0, 'container': 'b84fb25bd99b752351faa52502f20ecc3de6e53a877704761de3a79efe21b2e2', 'status': 1}
        """
        url = '/api/container/{0}/poll/'.format(container_id)
        return self.get(url)

    def create_pod(self, name, description):
        """Create pod"""
        url = '/api/pod/create/'
        payload = {
            'name': name,
            'description': description,
        }
        return self.post(url, json=payload, expected_code=201)

    def create_host(self, addr, pod_name):
        """Create host.
        host name and basic information will be got from docker info.

        e.g.::

            >>> eru_client.create_host('10.1.201.91:2376', 'pod')
            {'r': 0, 'msg': 'ok'}

        """
        url = '/api/host/create/'
        data = {
            'addr': addr,
            'podname': pod_name,
        }
        return self.post(url, data=data, expected_code=201)

    def create_network(self, name, netspace):
        """Create macvlan network, netspace is like `10.200.0.0/16`"""
        url = '/api/network/create/'
        payload = {
            'name': name,
            'netspace': netspace,
        }
        return self.post(url, json=payload, expected_code=201)

    def list_network(self, start=0, limit=20):
        """List all available networks"""
        url = '/api/network/list/'
        return self.get(url)

    def bind_container_network(self, appname, container_id, network_names):
        url = '/api/container/%s/bind_network' % container_id
        payload = {
            'appname': appname,
            'networks': network_names,
        }
        return self.put(url, json=payload)

    def get_network(self, id_or_name):
        url = '/api/network/{0}/'.format(id_or_name)
        return self.get(url)

    def list_app_versions(self, app, start=0, limit=20):
        params = {'start': start, 'limit': limit}
        return self.get('/api/app/%s/versions/' % app, params=params)

    def list_pods(self, start=0, limit=20):
        params = {'start': start, 'limit': limit}
        return self.get('/api/pod/list/', params=params)

    def list_pod_hosts(self, pod_name_or_id, start=0, limit=20, show_all=False):
        params = {'start': start, 'limit': limit}
        if show_all:
            params['all'] = 1
        return self.get('/api/pod/{0}/hosts/'.format(pod_name_or_id), params=params)

    def get_pod(self, id_or_name):
        return self.get('/api/pod/{0}/'.format(id_or_name))

    def get_container(self, id_or_sha256):
        return self.get('/api/container/{0}/'.format(id_or_sha256))

    def get_host(self, host_name):
        """Get host info"""
        return self.get('/api/host/{0}/'.format(host_name))

    def kill_host(self, host_name):
        """Kill a host, will be shown as down in Eru
        and containers on this host will be shown as dead."""
        return self.put('/api/host/{0}/down/'.format(host_name))

    def cure_host(self, host_name):
        """Cure a host, will be shown as up in Eru
        and containers on this host will be shown as alive."""
        return self.put('/api/host/{0}/cure/'.format(host_name))

    def list_host_containers(self, host_name, start=0, limit=20):
        params = {'start': start, 'limit': limit}
        return self.get('/api/host/{0}/containers/'.format(host_name), params=params)

    def get_task(self, task_id):
        return self.get('/api/task/{0}/'.format(task_id))

    def get_task_log(self, task_id):
        return self.get('/api/task/{0}/log/'.format(task_id))

    def add_eip(self, *eips):
        payload = list(eips)
        return self.post('/api/network/add_eip/', json=payload, expected_code=201)

    def delete_eip(self, *eips):
        payload = list(eips)
        return self.post('/api/network/delete_eip/', json=payload)

    def bind_host_eip(self, hostname):
        url = '/api/host/{0}/eip/'.format(hostname)
        return self.post(url)

    def release_host_eip(self, hostname):
        url = '/api/host/{0}/eip/'.format(hostname)
        return self.delete(url)

    def get_host_eip(self, hostname):
        url = '/api/host/{0}/eip/'.format(hostname)
        return self.get(url)

    def bind_container_eip(self, container_id, eip):
        url = '/api/container/{0}/bind_eip/'.format(container_id)
        payload = {'eip': eip}
        return self.put(url, json=payload)

    def release_container_eip(self, container_id, eip):
        url = '/api/container/{0}/release_eip/'.format(container_id)
        return self.put(url)
