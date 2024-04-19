docker build -t checking_system .
docker run -v /var/run/docker.sock:/var/run/docker.sock -it -p 9090:9090 --network new-net checking_system