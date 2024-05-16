docker network create new-net
docker build -t checking_system .
docker run -v /var/run/docker.sock:/var/run/docker.sock -it -p 8080:8080 --network new-net checking_system