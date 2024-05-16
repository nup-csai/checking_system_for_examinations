#!/bin/bash

while getopts ":n:p:u:" opt; do
  case $opt in
    n) NETWORK_NAME="$OPTARG";;
    p) PORT_NUMBER="$OPTARG";;
    u) URLS+=("$OPTARG");;
    \?) echo "Invalid option: -$OPTARG"; exit 1;;
  esac
done

NETWORK_NAME=${NETWORK_NAME:-"new-net"}
PORT_NUMBER=${PORT_NUMBER:-"9090"}

docker network create $NETWORK_NAME
docker build -t checking_system .
for url in "${URLS[@]}"; do
  echo "$url"
  directory=$(basename "$url" .git)
  docker run -v /var/run/docker.sock:/var/run/docker.sock -d -p 8080:8080 --network $NETWORK_NAME -v "$(pwd)/$directory:/app" checking_system "$url" "$directory"
done

for container in $(docker ps -q); do
  docker wait $container
  exit_status=$(docker inspect -f '{{.State.ExitCode}}' $container)
  if [ $exit_status -ne 0 ]; then
    echo "Container $container exited with status $exit_status"
  fi
done