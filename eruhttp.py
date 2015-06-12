import json
import socket
import requests
import websocket
import urllib
import urlparse
from urlparse import urljoin

class EruException(Exception):
    pass

class EruClient(object):

    def __init__(self, url, timeout=5, username='', password=''):
        self.url = url
        self.timeout = timeout
        self.username = username
        self.password = password
        self.session = requests.Session()

    def request(self, url, method='GET', params=None, data=None, as_json=True):
        headers = {'content-type': 'application/json'}
        if params is None:
            params = {}
        if data is None:
            data = {}
        if 'start' not in params:
            params['start'] = 0
        if 'limit' not in params:
            params['limit'] = 20
        target_url = urljoin(self.url, url)
        try:
            resp = self.session.request(
                method=method, url=target_url, params=params,
                data=json.dumps(data), timeout=self.timeout, headers=headers)
            if as_json:
                return resp.json()
            return resp.content
        except requests.exceptions.ReadTimeout:
            if as_json:
                return {'r': 1, 'msg': 'Read timeout'}
            return 'Read timeout'
        except requests.exceptions.ConnectionError:
            if as_json:
                return {'r': 1, 'msg': 'Connection refused'}
            return 'Connection refused'

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

    def post(self, url, params=None, data=None, as_json=True):
        return self.request(url, 'POST', params=params, data=data, as_json=as_json)

    def put(self, url, params=None, data=None, as_json=True):
        return self.request(url, 'PUT', params=params, data=data, as_json=as_json)

    def get(self, url, params=None, data=None, as_json=True):
        return self.request(url, 'GET', params=params, data=data, as_json=as_json)

    def delete(self, url, params=None, data=None, as_json=True):
        return self.request(url, 'DELETE', params=params, data=data, as_json=as_json)

    def register_app_version(self, name, version, git, token, appyaml, raw=False):
        """Register an app into ERU.

        :param name: the name of app.
        :param version: specific version of app, from git revision.
        :param git: git endpoint, used to clone code.
        :param token: git token, if repository is not public, need this to clone code.
        :param appyaml: file content of app.yaml, in dictionary.
        :type appyaml: ``dict``
        """
        url = '/api/app/register/'
        data = {
            'name': name,
            'version': version,
            'git': git,
            'token': token,
            'appyaml': appyaml,
        }
        if raw:
            data['raw'] = True
        return self.post(url, data=data)

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
        data = {'env': env}
        data.update(kwargs)
        return self.put(url, data=data)

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
        url = '/api/app/{0}/listenv'.format(name)
        return self.get(url)

    def get_app(self, name):
        """Get app from name.
        
        :param name: the name of app.
        """
        url = '/api/app/{0}'.format(name)
        return self.get(url)

    def get_version(self, name, version):
        """Get version by name and version.
        
        :param name: the name of app.
        :param version: specific version of app, from git revision.
        """
        url = '/api/app/{0}/{1}'.format(name, version)
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

    def deploy_private(self, group_name, pod_name, app_name, ncore,
            ncontainer, version, entrypoint, env, network_ids, host_name=None,
            raw=False, image='', spec_ips=None):
        """Deploy app on pod, using cores that are private.
        
        e.g.::

            >>> eru_client.deploy_private('group', 'pod', 'appname', 1.4, \
            ...     10, '3def4a6', 'web', 'prod', [1, 2])
            {'r': '0', 'msg': 'ok'}

        :param group_name: group which current user belongs to.
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
        :param host_name: if specified, containers will be only deployed to this host.
        """
        if raw and not image:
            raise EruException('raw and image must be set together.')

        url = '/api/deploy/private/{0}/{1}/{2}'.format(group_name, pod_name, app_name)
        data = {
            'ncore': ncore,
            'ncontainer': ncontainer,
            'version': version,
            'entrypoint': entrypoint,
            'env': env,
            'networks': network_ids,
        }
        if raw and image:
            data['raw'] = True
            data['image'] = image
        if host_name:
            data['hostname'] = host_name
        if spec_ips:
            data['spec_ips'] = spec_ips
        return self.post(url, data=data)

    def deploy_public(self, group_name, pod_name, app_name, ncontainer,
            version, entrypoint, env, network_ids, raw=False, image='', spec_ips=None):
        """Deploy app on pod, can't bind any cores to container."""
        if raw and not image:
            raise EruException('raw and image must be set together.')

        url = '/api/deploy/public/{0}/{1}/{2}'.format(group_name, pod_name, app_name)
        data = {
            'ncontainer': ncontainer,
            'version': version,
            'entrypoint': entrypoint,
            'env': env,
            'networks': network_ids,
        }
        if raw and image:
            data['raw'] = True
            data['image'] = image
        if spec_ips:
            data['spec_ips'] = spec_ips
        return self.post(url, data=data)

    def build_image(self, group_name, pod_name, app_name, base, version):
        """Build docker image for app.

        e.g.::

            >>> eru_client.build_image('group', 'pod', 'appname', \
            ...     'docker-registry.intra.hunantv.com/nbeimage/ubuntu:python-2015.05.12', '3d4fe6a')
            {'r': 0, 'msg': 'ok', 'task': 10001, 'watch_key': 'eru:task:result:10001'}
        
        :param group_name: group which current user belongs to.
        :param pod_name: target pod name which containers will be deployed.
        :param app_name: the name of app.
        :param base: which image to use as base, will be like `FROM base` in dockerfile.
        :param version: specific version of app.
        """
        url = '/api/deploy/build/{0}/{1}/{2}'.format(group_name, pod_name, app_name)
        data = {
            'base': base,
            'version': version,
        }
        return self.post(url, data=data)

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

    def offline_version(self, group_name, pod_name, app_name, version):
        """Offline specific version of app."""
        url = '/api/deploy/rmversion/{0}/{1}/{2}'.format(group_name, pod_name, app_name)
        data = {'version': version}
        return self.post(url, data=data)

    def remove_containers(self, container_ids):
        """Remove all containers in `container_ids`"""
        url = '/api/deploy/rmcontainers/'
        data = {'cids': container_ids}
        return self.post(url, data=data)

    def version(self):
        url = '/'
        return self.get(url, as_json=False)

    def kill_container(self, container_id):
        """Kill a container, it will be shown as dead in ERU."""
        url = '/api/container/{0}/kill'.format(container_id)
        return self.put(url)

    def cure_container(self, container_id):
        """Cure a container, it will be shown as alive in ERU."""
        url = '/api/container/{0}/cure'.format(container_id)
        return self.put(url)

    def start_container(self, container_id):
        """Start a container."""
        url = '/api/container/{0}/start'.format(container_id)
        return self.put(url)

    def stop_container(self, container_id):
        """Stop a container."""
        url = '/api/container/{0}/stop'.format(container_id)
        return self.put(url)

    def poll_container(self, container_id):
        """Poll container status.
        status 1 means alive, otherwise dead.
        
        e.g.::

            >>> eru_client.poll_container('b84fb25bd99b')
            {'r': 0, 'container': 'b84fb25bd99b752351faa52502f20ecc3de6e53a877704761de3a79efe21b2e2', 'status': 1}
        """
        url = '/api/container/{0}/poll'.format(container_id)
        return self.get(url)

    def create_group(self, name, description):
        """Create group"""
        url = '/api/sys/group/create'
        data = {
            'name': name,
            'description': description,
        }
        return self.post(url, data=data)

    def create_pod(self, name, description):
        """Create pod"""
        url = '/api/sys/pod/create'
        data = {
            'name': name,
            'description': description,
        }
        return self.post(url, data=data)

    def assign_pod_to_group(self, pod_name, group_name):
        """Assign a pod to group, the user in group now has access right to pod"""
        url = '/api/sys/pod/{0}/assign'.format(pod_name)
        data = {'group_name': group_name}
        return self.post(url, data=data)

    def create_host(self, addr, pod_name):
        """Create host.
        host name and basic information will be got from docker info. 

        e.g.::

            >>> eru_client.create_host('10.1.201.91:2376', 'pod')
            {'r': 0, 'msg': 'ok'}
        
        """
        url = '/api/sys/host/create'
        data = {
            'addr': addr,
            'pod_name': pod_name,
        }
        return self.post(url, data=data)

    def assign_host_to_group(self, addr, group_name):
        """Assign host to group, host will be private,
        people not in group don't have access to host.
        Don't forget port in `addr`.
        
        e.g.::

            >>> eru_client.assign_host_to_group('10.1.201.92:2376', 'group')
            {'r': 0, 'msg': 'ok'}
        """
        url = '/api/sys/host/{0}/assign'.format(addr)
        data = {'group_name': group_name}
        return self.post(url, data=data)

    def get_group_max_priviate_containers(self, group_name, pod_name, ncore):
        """How many containers can be deployed on pod from group,
        if each container requires ncore cores, ncore can be like 1.5."""
        url = '/api/sys/group/{0}/available_container_count'.format(group_name)
        params = {'pod_name': pod_name, 'ncore': ncore}
        return self.get(url, params=params)

    def create_network(self, name, netspace):
        """Create macvlan network, netspace is like `10.200.0.0/16`"""
        url = '/api/network/create/'
        data = {
            'name': name,
            'netspace': netspace,
        }
        return self.post(url, data=data)

    def list_network(self, start=0, limit=20):
        """List all available networks"""
        url = '/api/network/list/'
        return self.get(url)

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
