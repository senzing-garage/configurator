# configurator development

## Prerequisite software

The following software programs need to be installed:

1. [git](https://github.com/senzing-garage/knowledge-base/blob/main/WHATIS/git.md)
1. [make](https://github.com/senzing-garage/knowledge-base/blob/main/WHATIS/make.md)
1. [docker](https://github.com/senzing-garage/knowledge-base/blob/main/WHATIS/docker.md)

## Clone repository

For more information on environment variables,
see [Environment Variables](https://github.com/senzing-garage/knowledge-base/blob/main/lists/environment-variables.md).

1. Set these environment variable values:

    ```console
    export GIT_ACCOUNT=senzing
    export GIT_REPOSITORY=configurator
    export GIT_ACCOUNT_DIR=~/${GIT_ACCOUNT}.git
    export GIT_REPOSITORY_DIR="${GIT_ACCOUNT_DIR}/${GIT_REPOSITORY}"
    ```

1. Follow steps in [clone-repository](https://github.com/senzing-garage/knowledge-base/blob/main/HOWTO/clone-repository.md) to install the Git repository.

## Build docker image for development

1. **Option #1:** Using `docker` command and GitHub.

    ```console
    sudo docker build --tag senzing/configurator https://github.com/senzing-garage/configurator.git#main
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

## Test

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
