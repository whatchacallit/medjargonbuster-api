#!/bin/bash
source .env
docker login $container_registry -p $container_registry_password -u $container_registry_user

docker build .. -t $container_name

