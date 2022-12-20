### Clone required apps

```shell
git clone https://github.com/frappe/payments -b develop --origin upstream --depth 1 repos/payments
git clone https://github.com/frappe/erpnext -b version-14 --origin upstream --depth 1 repos/erpnext
git clone https://github.com/resilient-tech/india-compliance -b version-14 --origin upstream --depth 1 repos/india_compliance
```

### Build image

```shell
buildah build -t worker:latest --target backend -f Containerfile
```

### Start containers

```shell
podman-compose up -d
```
