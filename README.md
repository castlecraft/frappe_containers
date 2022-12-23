## Clone repo and change working directory

```
git clone https://github.com/castlecraft/frappe_containers
cd frappe_containers
```

## Clone required apps

```shell
git clone https://github.com/frappe/payments -b develop --origin upstream --depth 1 repos/payments
git clone https://github.com/frappe/erpnext -b version-14 --origin upstream --depth 1 repos/erpnext
git clone https://github.com/resilient-tech/india-compliance -b version-14 --origin upstream --depth 1 repos/india_compliance
```

## Build image

With `buildah`

```shell
buildah build -t worker:latest -f Containerfile .
```

Or with `docker`

```shell
docker build -t worker:latest -f Containerfile .
```

## Start containers

With `podman-compose`

```shell
podman-compose up -d
```

Or with `docker compose`

```shell
docker compose up -d
# or
docker-compose up -d
```

### Alternative mutable bench setup

WARNING: This goes against container best practices.

Use `compose/bench.compose.yml` to start containers with shared volumes for `apps`, `assets`, `env`, `logs` and `sites`.

```shell
docker compose -p bench -f compose/bench.compose.yml up -d
# or
podman-compose --project-name bench -f compose/bench.compose.yml up -d
```

Enter the backend container:

```shell
docker compose -p bench exec -w /home/frappe/frappe-bench backend bash
# or
podman-compose --project-name bench exec -w /home/frappe/frappe-bench backend bash
```

Now you can execute standard bench commands inside container. Example:

```shell
bench new-site site1.localhost --no-mariadb-socket --db-root-password=admin --admin-password=admin --install-app erpnext
bench update --no-backup --reset
bench build --production --hard-link
```

Notes:

- As the processes are controlled by container engine, `supervisor` is not installed in containers. Instead restart the containers to have the same effect.
- Volumes preserve the changes done to apps, assets, env and sites during bench commands like `bench update`, `bench setup env` or `build build --hard-link`.

## Environment Variables

No script except `nginx-entrypoint.sh` uses environment variables.

Variables used are as follows:

- `BACKEND`: Set to `{host}:{port}`, defaults to `0.0.0.0:8000`
- `SOCKETIO`: Set to `{host}:{port}`, defaults to `0.0.0.0:9000`
- `UPSTREAM_REAL_IP_ADDRESS`: Set Nginx config for [ngx_http_realip_module#set_real_ip_from](http://nginx.org/en/docs/http/ngx_http_realip_module.html#set_real_ip_from), defaults to `127.0.0.1`
- `UPSTREAM_REAL_IP_HEADER`: Set Nginx config for [ngx_http_realip_module#real_ip_header](http://nginx.org/en/docs/http/ngx_http_realip_module.html#real_ip_header), defaults to `X-Forwarded-For`
- `UPSTREAM_REAL_IP_RECURSIVE`: Set Nginx config for [ngx_http_realip_module#real_ip_recursive](http://nginx.org/en/docs/http/ngx_http_realip_module.html#real_ip_recursive) Set defaults to `off`
- `FRAPPE_SITE_NAME_HEADER`: Set proxy header `X-Frappe-Site-Name` and serve site named in the header, defaults to `$host`, i.e. find site name from host header.

To bypass `nginx-entrypoint.sh`, mount desired `/etc/nginx/conf.d/frappe.conf` and run `nginx -g 'daemon off;'` as container command.
