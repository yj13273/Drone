ARG PYTHON_VERSION=3.11-slim
ARG CMAKE_BUILD_TYPE=Release
ARG CPP_EXECUTABLE_NAME=uav_pipeline

FROM python:${PYTHON_VERSION} AS builder

ARG CMAKE_BUILD_TYPE=Release
ARG CPP_EXECUTABLE_NAME=uav_pipeline

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

COPY env_generator/requirements.txt ./env_generator/requirements.txt

RUN pip install \
    --no-cache-dir \
    --no-compile \
    --target=/opt/python \
    -r env_generator/requirements.txt

COPY cpp_engine ./cpp_engine

RUN cmake -S cpp_engine -B cpp_engine/build -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE} \
    && cmake --build cpp_engine/build --config ${CMAKE_BUILD_TYPE} -j \
    && cp cpp_engine/build/${CPP_EXECUTABLE_NAME} /usr/local/bin/${CPP_EXECUTABLE_NAME} \
    && strip /usr/local/bin/${CPP_EXECUTABLE_NAME} || true

FROM python:${PYTHON_VERSION} AS runtime

ARG CPP_EXECUTABLE_NAME=uav_pipeline

ENV CPP_EXECUTABLE_NAME=${CPP_EXECUTABLE_NAME}
ENV PYTHONPATH=/opt/python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MPLBACKEND=Agg

WORKDIR /app

COPY --from=builder /opt/python /opt/python
COPY --from=builder /usr/local/bin/${CPP_EXECUTABLE_NAME} /usr/local/bin/${CPP_EXECUTABLE_NAME}

COPY env_generator ./env_generator
COPY scripts ./scripts

RUN mkdir -p data plots outputs \
    && chmod +x scripts/run_all.sh \
    && rm -rf \
        /opt/python/pip \
        /opt/python/pip-* \
        /opt/python/setuptools \
        /opt/python/setuptools-* \
        /opt/python/pkg_resources \
    && find /opt/python -type d -name "__pycache__" -prune -exec rm -rf {} + \
    && find /opt/python -type d -name "tests" -prune -exec rm -rf {} + \
    && find /opt/python -type d -name "test" -prune -exec rm -rf {} + \
    && find /opt/python -type f -name "*.pyc" -delete \
    && find /opt/python -type f -name "*.pyo" -delete \
    && rm -rf /tmp/* /var/tmp/*

CMD ["sh", "scripts/run_all.sh"]
