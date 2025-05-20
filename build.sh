docker compose -f /home/ubuntu/apps/docker/docker-compose.yml down karatuben
docker rmi mservatius/karatuben:arm
docker build -t karatuben:arm .
docker tag karatuben:arm mservatius/karatuben:arm
docker push mservatius/karatuben:arm
docker rmi karatuben:arm
docker rmi mservatius/karatuben:arm
docker compose -f /home/ubuntu/apps/docker/docker-compose.yml up karatuben -d