### Clone repo and change working directory

```
git clone https://github.com/castlecraft/frappe_containers
cd frappe_containers
```

### Clone required apps

```shell
git clone https://github.com/frappe/payments -b develop --origin upstream --depth 1 repos/payments
git clone https://github.com/frappe/erpnext -b version-14 --origin upstream --depth 1 repos/erpnext
git clone https://github.com/resilient-tech/india-compliance -b version-14 --origin upstream --depth 1 repos/india_compliance
```

### Build image

With `buildah`

```shell
buildah build -t worker:latest --target backend -f Containerfile .
```

Or with `docker`

```shell
docker build -t worker:latest --target backend -f Containerfile .
```

### Start containers

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
