ARG BASE_IMAGE=senzing/senzingapi-runtime:3.10.1

# -----------------------------------------------------------------------------
# Stage: builder
# -----------------------------------------------------------------------------

FROM ${BASE_IMAGE} AS builder

ENV REFRESHED_AT=2024-05-22

LABEL Name="senzing/configurator" \
  Maintainer="support@senzing.com" \
  Version="1.1.11"

# Run as "root" for system installation.

USER root

# Install packages via apt.

RUN apt-get update \
  && apt-get -y install \
  python3 \
  python3-dev \
  python3-pip \
  python3-venv \
  && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment.

RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install packages via PIP.

COPY requirements.txt .
RUN pip3 install --upgrade pip \
  && pip3 install -r requirements.txt \
  && rm requirements.txt

# -----------------------------------------------------------------------------
# Stage: Final
# -----------------------------------------------------------------------------

# Create the runtime image.

FROM ${BASE_IMAGE} AS runner

ENV REFRESHED_AT=2024-05-22

LABEL Name="senzing/configurator" \
  Maintainer="support@senzing.com" \
  Version="1.1.11"

# Define health check.

HEALTHCHECK CMD ["/app/healthcheck.sh"]

# Run as "root" for system installation.

USER root

# Install packages via apt.

RUN apt-get update \
  && apt-get -y install \
  librdkafka-dev \
  libssl1.1 \
  libxml2 \
  postgresql-client \
  python3 \
  python3-venv \
  unixodbc \
  && rm -rf /var/lib/apt/lists/*

# Copy files from repository.

COPY ./rootfs /
COPY ./configurator.py /app/

# Copy python virtual environment from the builder image.

COPY --from=builder /app/venv /app/venv

# The port for the Flask is 8253.

EXPOSE 8253

# Make non-root container.

USER 1001

# Activate virtual environment.

ENV VIRTUAL_ENV=/app/venv
ENV PATH="/app/venv/bin:${PATH}"

# Runtime environment variables.

ENV LD_LIBRARY_PATH=/opt/senzing/g2/lib:/opt/senzing/g2/lib/debian:/opt/IBM/db2/clidriver/lib
ENV PATH=${PATH}:/opt/senzing/g2/python:/opt/IBM/db2/clidriver/adm:/opt/IBM/db2/clidriver/bin
ENV PYTHONPATH=/opt/senzing/g2/sdk/python
ENV PYTHONUNBUFFERED=1
ENV SENZING_DOCKER_LAUNCHED=true

# Runtime execution.

WORKDIR /app
ENTRYPOINT ["/app/configurator.py"]
CMD ["service"]
