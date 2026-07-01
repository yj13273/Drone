ARG PYTHON_VERSION=3.11-slim
ARG CMAKE_BUILD_TYPE=Release
ARG CPP_EXECUTABLE_NAME=uav_pipeline

FROM python:${PYTHON_VERSION}

ARG CMAKE_BUILD_TYPE=Release
ARG CPP_EXECUTABLE_NAME=uav_pipeline

ENV CPP_EXECUTABLE_NAME=${CPP_EXECUTABLE_NAME}
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MPLBACKEND=Agg

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

COPY env_generator/requirements.txt ./env_generator/requirements.txt

RUN pip install --no-cache-dir -r env_generator/requirements.txt

COPY cpp_engine ./cpp_engine

RUN cmake -S cpp_engine -B cpp_engine/build -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE} \
    && cmake --build cpp_engine/build --config ${CMAKE_BUILD_TYPE} -j

COPY env_generator ./env_generator
COPY scripts ./scripts

RUN mkdir -p data plots outputs \
    && chmod +x scripts/run_all.sh

CMD ["sh", "scripts/run_all.sh"]