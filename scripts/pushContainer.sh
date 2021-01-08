#!/bin/bash
source .env.local
docker login $container_registry -p $container_registry_password -u $container_registry_user

pushd .
cd ..
docker build . -t $container_name
#docker tag $container_name $container_registry/$container_name
#docker push $container_registry/$container_name

popd
