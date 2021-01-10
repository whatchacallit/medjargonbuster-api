#!/bin/bash
source .env
docker login $container_registry -p $container_registry_password -u $container_registry_user

docker run --env-file ../.env -p 5000:5000 $container_name
#docker tag $container_name $container_registry/$container_name
#docker push $container_registry/$container_name

