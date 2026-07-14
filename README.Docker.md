### Building and running your application

When you're ready, start your application by running:
`docker compose up --build`.

This repository does not expose a web server, so there is no `localhost:8000` endpoint.
The compose workflow builds the container and runs the UAV generation pipeline, then
writes results to `data/`, `outputs/`, and `plots/`.

If you want a browser-accessible app, add a service that listens on a port and update
`compose.yaml` to publish it.

### Deploying your application to the cloud

First, build your image, e.g.: `docker build -t myapp .`.
If your cloud uses a different CPU architecture than your development
machine (e.g., you are on a Mac M1 and your cloud provider is amd64),
you'll want to build the image for that platform, e.g.:
`docker build --platform=linux/amd64 -t myapp .`.

Then, push it to your registry, e.g. `docker push myregistry.com/myapp`.

Consult Docker's [getting started](https://docs.docker.com/go/get-started-sharing/)
docs for more detail on building and pushing.

### References
* [Docker's Python guide](https://docs.docker.com/language/python/)