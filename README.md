# configurator

## Synopsis

The [configurator.py](configurator.py) python script is used to configure Senzing via HTTP.
The [senzing/configurator](https://hub.docker.com/repository/docker/senzing/configurator)
docker image is a wrapper for use in docker formations (e.g. docker-compose, kubernetes).

## Overview

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

### Contents

1. [Demonstrate using Docker](#demonstrate-using-docker)
    1. [Set environment variables for Docker](#set-environment-variables-for-docker)
    1. [Run Docker container](#run-docker-container)
1. [Demonstrate using docker-compose](#demonstrate-using-docker-compose)
    1. [Download artifacts](#download-artifacts)
    1. [Prerequisite docker-compose stack](#prerequisite-docker-compose-stack)
    1. [Bring up docker-compose stack](#bring-up-docker-compose-stack)
1. [Demonstrate using Command Line](#demonstrate-using-command-line)
    1. [Install](#install)
    1. [Set environment variables for command line](#set-environment-variables-for-command-line)
    1. [Run command](#run-command)
1. [Configuration](#configuration)
1. [References](#references)

### Legend

1. :thinking: - A "thinker" icon means that a little extra thinking may be required.
   Perhaps you'll need to make some choices.
   Perhaps it's an optional step.
1. :pencil2: - A "pencil" icon means that the instructions may need modification before performing.
1. :warning: - A "warning" icon means that something tricky is happening, so pay attention.

### Expectations

- **Space:** This repository and demonstration require 6 GB free disk space.
- **Time:** Budget 40 minutes to get the demonstration up-and-running, depending on CPU and network speeds.
- **Background knowledge:** This repository assumes a working knowledge of:
  - [Docker](https://github.com/Senzing/knowledge-base/blob/main/WHATIS/docker.md)

## Demonstrate using Docker

### Set environment variables for Docker

1. Construct URL to database containing Senzing data.
   Example:

    ```console
    export SENZING_DATABASE_URL="postgresql://username:password@hostname:5432/G2"
    ```

### Run Docker container

1. Run docker container.
   Example:

    ```console
    docker run \
      --env SENZING_DATABASE_URL \
      --publish 8253:8253 \
      --rm \
      senzing/configurator

    ```

1. To try it out, see [Test](docs/development.md#test).

## Demonstrate using docker-compose

### Download artifacts

1. Specify a new directory to place artifacts in.
   Example:

    ```console
    export SENZING_VOLUME=~/my-senzing

    ```

1. Create directories.
   Example:

    ```console
    export PGADMIN_DIR=${SENZING_VOLUME}/pgadmin
    export POSTGRES_DIR=${SENZING_VOLUME}/postgres
    export RABBITMQ_DIR=${SENZING_VOLUME}/rabbitmq
    export SENZING_UID=$(id -u)
    export SENZING_GID=$(id -g)
    mkdir -p ${PGADMIN_DIR} ${POSTGRES_DIR} ${RABBITMQ_DIR}
    chmod -R 777 ${SENZING_VOLUME}

    ```

1. Download artifacts.
   Example:

    ```console
    wget \
      -O ${SENZING_VOLUME}/docker-compose-backing-services-only.yaml \
      "https://raw.githubusercontent.com/Senzing/docker-compose-demo/main/resources/postgresql/docker-compose-rabbitmq-postgresql-backing-services-only.yaml"

    wget \
      -O ${SENZING_VOLUME}/docker-compose.yaml \
      "https://raw.githubusercontent.com/Senzing/configurator/main/docker-compose.yaml"

    ```

### Prerequisite docker-compose stack

1. Bring up a Docker Compose stack with backing services.
   Example:

    ```console
    docker-compose -f ${SENZING_VOLUME}/docker-compose-backing-services-only.yaml pull
    docker-compose -f ${SENZING_VOLUME}/docker-compose-backing-services-only.yaml up

    ```

### Bring up docker-compose stack

1. Download `docker-compose.yaml` file and deploy stack.
   *Note:* `SENZING_VOLUME` needs to be set.
   Example:

    ```console
    docker-compose -f ${SENZING_VOLUME}/docker-compose.yaml pull
    docker-compose -f ${SENZING_VOLUME}/docker-compose.yaml up

    ```

1. To try it out, see [Test](docs/development.md#test).

## Demonstrate using Command Line

### Install

1. Install prerequisites:
    1. [Debian-based installation](docs/debian-based-installation.md) - For Ubuntu and [others](https://en.wikipedia.org/wiki/List_of_Linux_distributions#Debian-based)
    1. [RPM-based installation](docs/rpm-based-installation.md) - For Red Hat, CentOS, openSuse and [others](https://en.wikipedia.org/wiki/List_of_Linux_distributions#RPM-based).

### Set environment variables for command line

1. :pencil2: Identify where
   [senzing/apt](https://github.com/Senzing/docker-apt)
   placed the Senzing directories.
   Example:

    ```console
    export SENZING_DATA_VERSION_DIR=/opt/senzing/data/3.0.0
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

1. To try it out, see [Test](docs/development.md#test).

## Configuration


Configuration values specified by environment variable or command line parameter.

- **[SENZING_DATABASE_URL](https://github.com/Senzing/knowledge-base/blob/main/lists/environment-variables.md#senzing_database_url)**
- **[SENZING_DEBUG](https://github.com/Senzing/knowledge-base/blob/main/lists/environment-variables.md#senzing_debug)**
- **[SENZING_SUBCOMMAND](https://github.com/Senzing/knowledge-base/blob/main/lists/environment-variables.md#senzing_subcommand)**

## References

1. [Development](docs/development.md)
1. [Errors](docs/errors.md)
1. [Examples](docs/examples.md)
1. Related artifacts:
    1. [DockerHub](https://hub.docker.com/r/senzing/configurator)
    1. [Helm Chart](https://github.com/Senzing/charts/tree/main/charts/senzing-configurator)
