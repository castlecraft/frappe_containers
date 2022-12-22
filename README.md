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
buildah build -t worker:latest --target backend -f Containerfile .
```

Or with `docker`

```shell
docker build -t worker:latest --target backend -f Containerfile .
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
