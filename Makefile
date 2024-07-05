.DEFAULT_GOAL := build

.PHONY:build

IMAGE_NAME=starwiz_ai_django
TEST_CONTAINER_NAME=test_starwiz_ai_django
VERSION_TAG=1.1


build:
	docker build -t ${IMAGE_NAME}:${VERSION_TAG} -f ./build/docker/Dockerfile .
	docker save -o ./build/images/${IMAGE_NAME}.tar.gz ${IMAGE_NAME}:${VERSION_TAG}

build_prox:
	docker build \
	--build-arg HTTP_PROXY=http://192.168.3.118:7890 \
  --build-arg HTTPS_PROXY=https://192.168.3.118:7890 \
	-t ${IMAGE_NAME}:${VERSION_TAG} -f ./build/docker/Dockerfile .
	docker save -o ./build/images/${IMAGE_NAME}.tar.gz ${IMAGE_NAME}:${VERSION_TAG}

test:
	docker run -d --name ${TEST_CONTAINER_NAME} -v /d/Work/project/Python/starwizAi:/app	-p 5177:5177  ${IMAGE_NAME}:${VERSION_TAG}

test1:
	docker run -d --name ${TEST_CONTAINER_NAME} -v /d/Work/Golang/run/django/.env:/app/.env \
	-v /d/Work/Golang/run/django/starwizAi/settings.py:/app/starwizAi/settings.py \
	-v /d/Work/Golang/run/django/db.sqlite3:/app/starwizAi/db.sqlite3 \
	-p 5177:5177  ${IMAGE_NAME}:${VERSION_TAG}

test2:
	docker run -d --name ${TEST_CONTAINER_NAME}_qcluster -v /d/Work/Golang/run/django/.env:/app/.env \
	-v /d/Work/Golang/run/django/starwizAi/settings.py:/app/starwizAi/settings.py \
	-p 5177:5177	-p 5177:5177  ${IMAGE_NAME}:${VERSION_TAG} -i gunicorn --bind 0.0.0.0:5177 starwizAi.wsgi:application  

clean_test:
	docker stop ${TEST_CONTAINER_NAME}
	docker container rm ${TEST_CONTAINER_NAME}
	docker rmi ${IMAGE_NAME}:${VERSION_TAG}

clean_docker_cache:
	docker builder prune

# docker container prune
# docker image prune

clean:clean_test clean_docker_cache\
