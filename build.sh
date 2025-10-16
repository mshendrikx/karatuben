docker compose -f /home/msh/docker/compose/docker-compose.yml down karatuben
docker rmi mservatius/karatuben:latest
docker build -t karatuben:latest .
docker tag karatuben:latest mservatius/karatuben:latest
docker push mservatius/karatuben:latest
docker rmi karatuben:latest
docker rmi mservatius/karatuben:latest
docker compose -f /home/msh/docker/compose/docker-compose.yml up karatuben -d