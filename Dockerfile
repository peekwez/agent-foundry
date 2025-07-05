FROM python:3.12-slim

RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libavcodec-extra \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    --no-install-recommends curl ca-certificates


# Set working directory
WORKDIR /app

# Copy local code to the container image.
COPY . /app

# Install pip dependencies
RUN --mount=type=cache,target=/var/cache/pip \
    pip install --upgrade pip \
    && pip install -e .


EXPOSE 5000

# Run the MCP Server
CMD ["ferros" , "api", "--host", "0.0.0.0", "--port", "5000"]
