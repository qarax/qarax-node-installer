#!/bin/bash

# Remove existing container
podman rm qarax-node-installer -f

# Build the image
podman build -t qarax-node-installer .

# Run the container
podman run -d --name qarax-node-installer -p 8000:80 -it qarax-node-installer:latest
