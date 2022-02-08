ARG BASE_IMAGE=debian:11.2-slim@sha256:4c25ffa6ef572cf0d57da8c634769a08ae94529f7de5be5587ec8ce7b9b50f9c
FROM ${BASE_IMAGE} as builder

ENV REFRESHED_AT=2022-02-08

LABEL Name="senzing/configurator" \
      Maintainer="support@senzing.com" \
      Version="1.1.2"

# -----------------------------------------------------------------------------
# Stage: builder
# -----------------------------------------------------------------------------

# Run as "root" for system installation.

USER root

RUN apt-get update \
 && apt-get -y install \
    python3 \
    python3-dev \
    python3-venv \
    python3-pip \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment.

RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install packages via PIP.

COPY requirements.txt .
RUN pip3 install --upgrade pip \
 && pip3 install -r requirements.txt \
 && rm /requirements.txt

# -----------------------------------------------------------------------------
# Stage: Final
# -----------------------------------------------------------------------------

FROM ${BASE_IMAGE} AS runner

HEALTHCHECK CMD ["/app/healthcheck.sh"]

# Run as "root" for system installation.

USER root

# Install packages via apt.

RUN apt update \
 && apt -y install \
      librdkafka-dev \
      libxml2 \
      python3 \
      python3-venv \
      postgresql-client \
      unixodbc \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Copy files from repository.

COPY ./rootfs /
COPY ./configurator.py /app

# Copy python virtual environment from the builder image.

COPY --from=builder /app/venv /app/venv

# The port for the Flask is 8253.

EXPOSE 8253

# Make non-root container.

USER 1001

# Make sure all messages always reach console.

ENV PYTHONUNBUFFERED=1

# Activate virtual environment.

ENV VIRTUAL_ENV=/app/venv
ENV PATH="/app/venv/bin:$PATH"

# Set environment variables for USER 1001.

ENV LD_LIBRARY_PATH=/opt/senzing/g2/lib:/opt/senzing/g2/lib/debian:/opt/IBM/db2/clidriver/lib
ENV ODBCSYSINI=/etc/opt/senzing
ENV PATH=${PATH}:/opt/senzing/g2/python:/opt/IBM/db2/clidriver/adm:/opt/IBM/db2/clidriver/bin
ENV PYTHONPATH=/opt/senzing/g2/python
ENV SENZING_ETC_PATH=/etc/opt/senzing

# Runtime execution.

ENV SENZING_DOCKER_LAUNCHED=true

WORKDIR /app
ENTRYPOINT ["/app/configurator.py"]
CMD ["service"]
