# configurator

## Overview

The [configurator.py](configuration.py) python script is used to configure Senzing.
The `senzing/configurator` docker image is a wrapper for use in docker formations (e.g. docker-compose, kubernetes).

To see all of the subcommands, run:

```console
$ ./configurator.py
usage: configurator.py [-h] {service,sleep,version,docker-acceptance-test} ...

Perform Senzing configuration. For more information, see
https://github.com/Senzing/configurator

positional arguments:
  {service,sleep,version,docker-acceptance-test}
                        Subcommands (SENZING_SUBCOMMAND):
    service             Receive HTTP requests.
    sleep               Do nothing but sleep. For Docker testing.
    version             Print version of configurator.py.
    docker-acceptance-test
                        For Docker acceptance testing.

optional arguments:
  -h, --help            show this help message and exit
```

To see the options for a subcommand, run commands like:

```console
./configurator.py service --help
```

### Related artifacts

1. [DockerHub](https://hub.docker.com/r/senzing/configurator)
1. [Helm Chart](https://github.com/Senzing/charts/tree/master/charts/senzing-configurator)

### Contents

1. [Expectations](#expectations)
    1. [Space](#space)
    1. [Time](#time)
    1. [Background knowledge](#background-knowledge)
1. [Demonstrate using Command Line](#demonstrate-using-command-line)
    1. [Install](#install)
    1. [Set environment variables](#set-environment-variables)
    1. [Run command](#run-command)
    1. [Test Command Line](#test-command-line)
1. [Demonstrate using Docker](#demonstrate-using-docker)
    1. [Initialize Senzing](#initialize-senzing)
    1. [Configuration](#configuration)
    1. [Volumes](#volumes)
    1. [Docker network](#docker-network)
    1. [Docker user](#docker-user)
    1. [Database support](#database-support)
    1. [Run docker container](#run-docker-container)
    1. [Test docker container](#test-docker-container)
1. [Demonstrate using docker-compose](#demonstrate-using-docker-compose)
    1. [Prerequisite docker-compose stack](#prerequisite-docker-compose-stack)
    1. [docker-compose database](#docker-compose-database)
    1. [docker-compose volumes](#docker-compose-volumes)
    1. [Bring up docker-compose stack](#bring-up-docker-compose-stack)
1. [Demonstrate using Helm](#demonstrate-using-helm)
    1. [Prerequisite software for Helm demonstration](#prerequisite-software-for-helm-demonstration)
    1. [Clone repository for Helm demonstration](#clone-repository-for-helm-demonstration)
    1. [Create custom helm values files](#create-custom-helm-values-files)
    1. [Create custom kubernetes configuration files](#create-custom-kubernetes-configuration-files)
    1. [Create namespace](#create-namespace)
    1. [Create persistent volume](#create-persistent-volume)
    1. [Add helm repositories](#add-helm-repositories)
    1. [Deploy Senzing](#deploy-senzing)
    1. [Deploy configurator](#deploy-configurator)
    1. [Install senzing-debug Helm chart](#install-senzing-debug-helm-chart)
    1. [Cleanup](#cleanup)
1. [Develop](#develop)
    1. [Prerequisite software](#prerequisite-software)
    1. [Clone repository](#clone-repository)
    1. [Build docker image for development](#build-docker-image-for-development)
1. [Examples](#examples)
1. [Errors](#errors)
1. [References](#references)

### Legend

1. :thinking: - A "thinker" icon means that a little extra thinking may be required.
   Perhaps you'll need to make some choices.
   Perhaps it's an optional step.
1. :pencil2: - A "pencil" icon means that the instructions may need modification before performing.
1. :warning: - A "warning" icon means that something tricky is happening, so pay attention.

## Expectations

### Space

This repository and demonstration require 6 GB free disk space.

### Time

Budget 40 minutes to get the demonstration up-and-running, depending on CPU and network speeds.

### Background knowledge

This repository assumes a working knowledge of:

1. [Docker](https://github.com/Senzing/knowledge-base/blob/master/WHATIS/docker.md)

## Demonstrate using Command Line

### Install

1. Install prerequisites:
    1. [Debian-based installation](docs/debian-based-installation.md) - For Ubuntu and [others](https://en.wikipedia.org/wiki/List_of_Linux_distributions#Debian-based)
    1. [RPM-based installation](docs/rpm-based-installation.md) - For Red Hat, CentOS, openSuse and [others](https://en.wikipedia.org/wiki/List_of_Linux_distributions#RPM-based).

### Set environment variables

1. :pencil2: Identify where
   [senzing/yum](https://github.com/Senzing/docker-yum)
   placed the Senzing directories.
   Example:

    ```console
    export SENZING_DATA_VERSION_DIR=/opt/senzing/data/2.0.0
    export SENZING_ETC_DIR=/etc/opt/senzing
    export SENZING_G2_DIR=/opt/senzing/g2
    export SENZING_VAR_DIR=/var/opt/senzing
    ```

1. :pencil2: Identify database.
   Example:

    ```console
    export SENZING_DATABASE_URL="sqlite3://na:na@${SENZING_VAR_DIR}/sqlite/G2C.db"
    ```

1. Set environment variables.
   Example:

    ```console
    export SENZING_CONFIG_PATH=${SENZING_ETC_DIR}
    export SENZING_SUPPORT_PATH=${SENZING_DATA_VERSION_DIR}
    export PYTHONPATH=${SENZING_G2_DIR}/python
    export LD_LIBRARY_PATH=${SENZING_G2_DIR}/lib:${SENZING_G2_DIR}/lib/debian
    ```

### Run command

1. Run command.
   Note: **GIT_REPOSITORY_DIR** needs to be set.
   Example:

    ```console
    cd ${GIT_REPOSITORY_DIR}
    ./configurator.py service
    ```

### Test Command Line

1. Get existing datasources.
   Example:

    ```console
    curl -X GET \
      --header 'Content-type: application/json;charset=utf-8' \
      http://localhost:8253/datasources
    ```

1. Add new datasources.
   Note that adding datasources that already exist does not create a second copy.
   This is a case where the POST method is idempotent.
   Example:

    ```console
    curl -X POST \
      --data '[ "SEARCH", "TEST", "TEST1", "TEST2"]' \
      --header 'Content-type: application/json;charset=utf-8' \
      http://localhost:8253/datasources
    ```

## Demonstrate using Docker

### Initialize Senzing

1. If Senzing has not been initialized, visit
   "[How to initialize Senzing with Docker](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/initialize-senzing-with-docker.md)".

### Configuration

Configuration values specified by environment variable or command line parameter.

- **[SENZING_DATA_VERSION_DIR](https://github.com/Senzing/knowledge-base/blob/master/lists/environment-variables.md#senzing_data_version_dir)**
- **[SENZING_DATABASE_URL](https://github.com/Senzing/knowledge-base/blob/master/lists/environment-variables.md#senzing_database_url)**
- **[SENZING_DEBUG](https://github.com/Senzing/knowledge-base/blob/master/lists/environment-variables.md#senzing_debug)**
- **[SENZING_ETC_DIR](https://github.com/Senzing/knowledge-base/blob/master/lists/environment-variables.md#senzing_etc_dir)**
- **[SENZING_G2_DIR](https://github.com/Senzing/knowledge-base/blob/master/lists/environment-variables.md#senzing_g2_dir)**
- **[SENZING_NETWORK](https://github.com/Senzing/knowledge-base/blob/master/lists/environment-variables.md#senzing_network)**
- **[SENZING_RUNAS_USER](https://github.com/Senzing/knowledge-base/blob/master/lists/environment-variables.md#senzing_runas_user)**
- **[SENZING_SUBCOMMAND](https://github.com/Senzing/knowledge-base/blob/master/lists/environment-variables.md#senzing_subcommand)**
- **[SENZING_VAR_DIR](https://github.com/Senzing/knowledge-base/blob/master/lists/environment-variables.md#senzing_var_dir)**

1. To determine which configuration parameters are used for each `subcommand`, run:

    ```console
    ./configurator.py <subcommand> --help
    ```

### Volumes

1. :pencil2: Specify the directory containing the Senzing installation.
   Use the same `SENZING_VOLUME` value used when performing
   "[How to initialize Senzing with Docker](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/initialize-senzing-with-docker.md)".
   Example:

    ```console
    export SENZING_VOLUME=~/my-senzing
    ```

    1. Here's a simple test to see if `SENZING_VOLUME` is correct.
       The following commands should return file contents.
       Example:

        ```console
        cat ${SENZING_VOLUME}/g2/g2BuildVersion.json
        cat ${SENZING_VOLUME}/data/2.0.0/libpostal/data_version
        ```

    1. :warning:
       **macOS** - [File sharing](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/share-directories-with-docker.md#macos)
       must be enabled for `SENZING_VOLUME`.
    1. :warning:
       **Windows** - [File sharing](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/share-directories-with-docker.md#windows)
       must be enabled for `SENZING_VOLUME`.

1. Identify the `data_version`, `etc`, `g2`, and `var` directories.
   Example:

    ```console
    export SENZING_DATA_VERSION_DIR=${SENZING_VOLUME}/data/2.0.0
    export SENZING_ETC_DIR=${SENZING_VOLUME}/etc
    export SENZING_G2_DIR=${SENZING_VOLUME}/g2
    export SENZING_VAR_DIR=${SENZING_VOLUME}/var
    ```

### Docker network

:thinking: **Optional:**  Use if docker container is part of a docker network.

1. List docker networks.
   Example:

    ```console
    sudo docker network ls
    ```

1. :pencil2: Specify docker network.
   Choose value from NAME column of `docker network ls`.
   Example:

    ```console
    export SENZING_NETWORK=*nameofthe_network*
    ```

1. Construct parameter for `docker run`.
   Example:

    ```console
    export SENZING_NETWORK_PARAMETER="--net ${SENZING_NETWORK}"
    ```

### Docker user

:thinking: **Optional:**  The docker container runs as "USER 1001".
Use if a different userid (UID) is required.

1. :pencil2: Manually identify user.
   User "0" is root.
   Example:

    ```console
    export SENZING_RUNAS_USER="0"
    ```

   Another option, use current user.
   Example:

    ```console
    export SENZING_RUNAS_USER=$(id -u)
    ```

1. Construct parameter for `docker run`.
   Example:

    ```console
    export SENZING_RUNAS_USER_PARAMETER="--user ${SENZING_RUNAS_USER}"
    ```

### Database support

:thinking: **Optional:**  Some database need additional support.
For other databases, these steps may be skipped.

1. **Db2:** See
   [Support Db2](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/support-db2.md)
   instructions to set `SENZING_OPT_IBM_DIR_PARAMETER`.
1. **MS SQL:** See
   [Support MS SQL](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/support-mssql.md)
   instructions to set `SENZING_OPT_MICROSOFT_DIR_PARAMETER`.

### Run docker container

1. Run docker container.
   Example:

    ```console
    sudo docker run \
      --interactive \
      --publish 8253:8253 \
      --rm \
      --tty \
      --volume ${SENZING_DATA_VERSION_DIR}:/opt/senzing/data \
      --volume ${SENZING_ETC_DIR}:/etc/opt/senzing \
      --volume ${SENZING_G2_DIR}:/opt/senzing/g2 \
      --volume ${SENZING_VAR_DIR}:/var/opt/senzing \
      ${SENZING_RUNAS_USER_PARAMETER} \
      ${SENZING_NETWORK_PARAMETER} \
      ${SENZING_OPT_IBM_DIR_PARAMETER} \
      ${SENZING_OPT_MICROSOFT_DIR_PARAMETER} \
      senzing/configurator
    ```

### Test docker container

1. Get existing datasources.
   Example:

    ```console
    curl -X GET \
      --header 'Content-type: application/json;charset=utf-8' \
      http://localhost:8253/datasources
    ```

1. Add new datasources.
   Note that adding datasources that already exist does not create a second copy.
   This is a case where the POST method is idempotent.
   Example:

    ```console
    curl -X POST \
      --data '[ "SEARCH", "TEST", "TEST1", "TEST2"]' \
      --header 'Content-type: application/json;charset=utf-8' \
      http://localhost:8253/datasources
    ```

## Demonstrate using docker-compose

### Prerequisite docker-compose stack

1. Bring up one of the Senzing docker-compose stacks seen in
   [docker-compose-demo](https://github.com/Senzing/docker-compose-demo).

### docker-compose database

1. Specify the database connection URL used in the Senzing docker-compose stack.
   *Note:*  The value will be the same as the `SENZING_DATABASE_URL` value used in the
   [docker-compose-demo](https://github.com/Senzing/docker-compose-demo) stack.
   Example:

    ```console
    export SENZING_DATABASE_URL=postgresql://postgres:postgres@senzing-postgres:5432/G2
    ```

### docker-compose volumes

1. :pencil2: Specify the directory containing the Senzing installation.
   *Note:*  The value will be the same as the `SENZING_VOLUME` value used in the
   [docker-compose-demo](https://github.com/Senzing/docker-compose-demo) stack.
   Example:

    ```console
    export SENZING_VOLUME=~/my-senzing
    ```

1. Identify the `data_version`, `etc`, `g2`, and `var` directories.
   Example:

    ```console
    export SENZING_DATA_VERSION_DIR=${SENZING_VOLUME}/data/2.0.0
    export SENZING_ETC_DIR=${SENZING_VOLUME}/etc
    export SENZING_G2_DIR=${SENZING_VOLUME}/g2
    export SENZING_VAR_DIR=${SENZING_VOLUME}/var
    ```

### Bring up docker-compose stack

1. Set these environment variable values:

    ```console
    export GIT_ACCOUNT=senzing
    export GIT_REPOSITORY=configurator
    export GIT_ACCOUNT_DIR=~/${GIT_ACCOUNT}.git
    export GIT_REPOSITORY_DIR="${GIT_ACCOUNT_DIR}/${GIT_REPOSITORY}"
    ```

1. Bring up `docker-compose.yaml`.
   Example:

    ```console
    cd ${GIT_REPOSITORY_DIR}
    sudo \
      --preserve-env \
      docker-compose up
    ```

## Demonstrate using Helm

### Prerequisite software for Helm demonstration

#### kubectl

1. [Install kubectl](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/install-kubectl.md).

#### minikube cluster

1. [Install minikube](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/install-minikube.md).
1. [Start cluster](https://docs.bitnami.com/kubernetes/get-started-kubernetes/#overview)

    ```console
    minikube start --cpus 4 --memory 8192
    ```

    Alternative:

    ```console
    minikube start --cpus 4 --memory 8192 --vm-driver kvm2
    ```

#### Helm/Tiller

1. [Install Helm](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/install-helm.md) on your local workstation.
1. [Install Tiller](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/install-tiller.md) in the minikube cluster.

### Clone repository for Helm demonstration

The Git repository has files that will be used in the `helm install --values` parameter.

1. Using these environment variable values:

    ```console
    export GIT_ACCOUNT=senzing
    export GIT_REPOSITORY=configurator
    export GIT_ACCOUNT_DIR=~/${GIT_ACCOUNT}.git
    export GIT_REPOSITORY_DIR="${GIT_ACCOUNT_DIR}/${GIT_REPOSITORY}"
    ```

1. Follow steps in [clone-repository](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/clone-repository.md) to install the Git repository.

### Create custom helm values files

1. :pencil2: Set environment variables.
   Example:

    ```console
    export DOCKER_REGISTRY_SECRET=my-registry-secret
    export DOCKER_REGISTRY_URL=docker.io
    ```

1. Option #1. Quick method using `envsubst`.
   Example:

    ```console
    export HELM_VALUES_DIR=${GIT_REPOSITORY_DIR}/helm-values
    mkdir -p ${HELM_VALUES_DIR}

    for file in ${GIT_REPOSITORY_DIR}/helm-values-templates/*.yaml; \
    do \
      envsubst < "${file}" > "${HELM_VALUES_DIR}/$(basename ${file})";
    done
    ```

1. Option #2. Copy and modify method.

    ```console
    export HELM_VALUES_DIR=${GIT_REPOSITORY_DIR}/helm-values
    mkdir -p ${HELM_VALUES_DIR}

    cp ${GIT_REPOSITORY_DIR}/helm-values-templates/* ${HELM_VALUES_DIR}
    ```

    :pencil2: Edit files in ${HELM_VALUES_DIR} replacing the following variables with actual values.

    1. `${DOCKER_REGISTRY_SECRET}`
    1. `${DOCKER_REGISTRY_URL}`

### Create custom kubernetes configuration files

1. :pencil2: Set environment variables.
   Example:

    ```console
    export DEMO_PREFIX=my
    export DEMO_NAMESPACE=${DEMO_PREFIX}-namespace
    ```

1. Option #1. Quick method using `envsubst`.
   Example:

    ```console
    export KUBERNETES_DIR=${GIT_REPOSITORY_DIR}/kubernetes
    mkdir -p ${KUBERNETES_DIR}

    for file in ${GIT_REPOSITORY_DIR}/kubernetes-templates/*; \
    do \
      envsubst < "${file}" > "${KUBERNETES_DIR}/$(basename ${file})";
    done
    ```

1. Option #2. Copy and modify method.

    ```console
    export KUBERNETES_DIR=${GIT_REPOSITORY_DIR}/kubernetes
    mkdir -p ${KUBERNETES_DIR}

    cp ${GIT_REPOSITORY_DIR}/kubernetes-templates/* ${KUBERNETES_DIR}
    ```

    :pencil2: Edit files in ${KUBERNETES_DIR} replacing the following variables with actual values.

    1. `${DEMO_NAMESPACE}`

### Create namespace

1. Create namespace.

    ```console
    kubectl create -f ${KUBERNETES_DIR}/namespace.yaml
    ```

1. Optional: Review namespaces.

    ```console
    kubectl get namespaces
    ```

### Create persistent volume

1. Create persistent volumes.
   Example:

    ```console
    kubectl create -f ${KUBERNETES_DIR}/persistent-volume-senzing.yaml
    ```

1. Create persistent volume claims.
   Example:

    ```console
    kubectl create -f ${KUBERNETES_DIR}/persistent-volume-claim-senzing.yaml
    ```

1. Optional: Review persistent volumes and claims.

    ```console
    kubectl get persistentvolumes \
      --namespace ${DEMO_NAMESPACE}

    kubectl get persistentvolumeClaims \
      --namespace ${DEMO_NAMESPACE}
    ```

### Add helm repositories

1. Add Senzing repository.
   Example:

    ```console
    helm repo add senzing https://senzing.github.io/charts/
    ```

1. Update repositories.

    ```console
    helm repo update
    ```

1. Optional: Review repositories

    ```console
    helm repo list
    ```

1. Reference: [helm repo](https://helm.sh/docs/helm/#helm-repo)

### Deploy Senzing

### Deploy configurator

This deployment launches the configurator.

1. Install chart.
   Example:

    ```console
    helm install \
      --name ${DEMO_PREFIX}-senzing-configurator \
      --namespace ${DEMO_NAMESPACE} \
      --values ${HELM_VALUES_DIR}/configurator.yaml \
      senzing/senzing-configurator
    ```

1. Wait for pods to run.  Example:

    ```console
    kubectl get pods \
      --namespace ${DEMO_NAMESPACE} \
      --watch
    ```

1. In a separate terminal window, port forward to local machine.

    :pencil2:  Set environment variables.  Example:

    ```console
    export DEMO_PREFIX=my
    export DEMO_NAMESPACE=${DEMO_PREFIX}-namespace
    ```

    Port forward.  Example:

    ```console
    kubectl port-forward \
      --address 0.0.0.0 \
      --namespace ${DEMO_NAMESPACE} \
      svc/${DEMO_PREFIX}-configurator 8253:8253
    ```

1. Test HTTP API.
   Note: **GIT_REPOSITORY_DIR** needs to be set.
   Example:

    ```console
    curl -X POST \
      --header "Content-Type: text/plain" \
      --data-binary @${GIT_REPOSITORY_DIR}/test/test-data-1.json \
      http://localhost:8253/resolve
    ```

### Install senzing-debug Helm chart

If debugging is needed, the `senzing/senzing-debug` chart will help with:

- Inspecting the `/opt/senzing` volume
- Debugging general issues

1. Install chart.  Example:

    ```console
    helm install \
      --name ${DEMO_PREFIX}-senzing-debug \
      --namespace ${DEMO_NAMESPACE} \
      --values ${GIT_REPOSITORY_DIR}/helm-values/senzing-debug.yaml \
       senzing/senzing-debug
    ```

1. Wait for pod to run.  Example:

    ```console
    kubectl get pods \
      --namespace ${DEMO_NAMESPACE} \
      --watch
    ```

1. In a separate terminal window, log into debug pod.

    :pencil2:  Set environment variables.  Example:

    ```console
    export DEMO_PREFIX=my
    export DEMO_NAMESPACE=${DEMO_PREFIX}-namespace
    ```

    Log into pod.  Example:

    ```console
    export DEBUG_POD_NAME=$(kubectl get pods \
      --namespace ${DEMO_NAMESPACE} \
      --output jsonpath="{.items[0].metadata.name}" \
      --selector "app.kubernetes.io/name=senzing-debug, \
                  app.kubernetes.io/instance=${DEMO_PREFIX}-senzing-debug" \
      )

    kubectl exec -it --namespace ${DEMO_NAMESPACE} ${DEBUG_POD_NAME} -- /bin/bash
    ```

### Cleanup

#### Delete everything in project

1. Example:

    ```console
    helm delete --purge ${DEMO_PREFIX}-senzing-debug
    helm delete --purge ${DEMO_PREFIX}-configurator
    helm delete --purge ${DEMO_PREFIX}-senzing-package
    helm repo remove senzing
    kubectl delete -f ${KUBERNETES_DIR}/persistent-volume-claim-opt-senzing.yaml
    kubectl delete -f ${KUBERNETES_DIR}/persistent-volume-opt-senzing.yaml
    kubectl delete -f ${KUBERNETES_DIR}/namespace.yaml
    ```

#### Delete minikube cluster

1. Example:

    ```console
    minikube stop
    minikube delete
    ```

## Develop

### Prerequisite software

The following software programs need to be installed:

1. [git](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/install-git.md)
1. [make](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/install-make.md)
1. [docker](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/install-docker.md)

### Clone repository

For more information on environment variables,
see [Environment Variables](https://github.com/Senzing/knowledge-base/blob/master/lists/environment-variables.md).

1. Set these environment variable values:

    ```console
    export GIT_ACCOUNT=senzing
    export GIT_REPOSITORY=configurator
    export GIT_ACCOUNT_DIR=~/${GIT_ACCOUNT}.git
    export GIT_REPOSITORY_DIR="${GIT_ACCOUNT_DIR}/${GIT_REPOSITORY}"
    ```

1. Follow steps in [clone-repository](https://github.com/Senzing/knowledge-base/blob/master/HOWTO/clone-repository.md) to install the Git repository.

### Build docker image for development

1. **Option #1:** Using `docker` command and GitHub.

    ```console
    sudo docker build --tag senzing/configurator https://github.com/senzing/configurator.git#main
    ```

1. **Option #2:** Using `docker` command and local repository.

    ```console
    cd ${GIT_REPOSITORY_DIR}
    sudo docker build --tag senzing/configurator .
    ```

1. **Option #3:** Using `make` command.

    ```console
    cd ${GIT_REPOSITORY_DIR}
    sudo make docker-build
    ```

    Note: `sudo make docker-build-development-cache` can be used to create cached docker layers.

## Examples

## Errors

1. See [docs/errors.md](docs/errors.md).

## References
