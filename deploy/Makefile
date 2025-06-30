include Make.in

REGISTRY_NAME=agent-foundry.canadacentral.cloudapp.azure.com:8888
LOCAL_REGISTRY_NAME=localhost:8888
FOUNDRY_IMAGE=agent-foundry/amd64
BLACKBOARD_IMAGE=blackboard-mcp/amd64
TAG:=latest

deploy: build tag push clean-up

clean-up:
	$(call log_green, Cleaning up Docker containers and images...)
	docker rmi $(FOUNDRY_IMAGE):$(TAG) || true
	docker rmi $(BLACKBOARD_IMAGE):$(TAG) || true
	docker rmi $(REGISTRY_NAME)/$(FOUNDRY_IMAGE):$(TAG) || true
	docker rmi $(REGISTRY_NAME)/$(BLACKBOARD_IMAGE):$(TAG) || true

build:
	$(call log_green, Building Docker images...)
	docker build -t $(FOUNDRY_IMAGE):$(TAG) \
		-f ../Dockerfile ../ --platform linux/amd64
	docker build -t $(BLACKBOARD_IMAGE):$(TAG) \
		-f ../mcp-blackboard/Dockerfile ../mcp-blackboard --platform linux/amd64

tag:
	$(call log_green, Tagging Docker images...)
	docker tag $(FOUNDRY_IMAGE):$(TAG) $(REGISTRY_NAME)/$(FOUNDRY_IMAGE):$(TAG)
	docker tag $(BLACKBOARD_IMAGE):$(TAG) $(REGISTRY_NAME)/$(BLACKBOARD_IMAGE):$(TAG)

push:
	$(call log_green, Pushing Docker images to the registry...)
	docker push $(REGISTRY_NAME)/$(BLACKBOARD_IMAGE):$(TAG)
	docker push $(REGISTRY_NAME)/$(FOUNDRY_IMAGE):$(TAG)

pull:
	$(call log_green, Pulling Docker images from the registry...)
	docker pull $(LOCAL_REGISTRY_NAME)/$(BLACKBOARD_IMAGE):$(TAG)
	docker pull $(LOCAL_REGISTRY_NAME)/$(FOUNDRY_IMAGE):$(TAG)
	docker tag $(LOCAL_REGISTRY_NAME)/$(FOUNDRY_IMAGE):$(TAG) $(FOUNDRY_IMAGE):$(TAG)
	docker tag $(LOCAL_REGISTRY_NAME)/$(BLACKBOARD_IMAGE):$(TAG) $(BLACKBOARD_IMAGE):$(TAG)
	docker rmi $(LOCAL_REGISTRY_NAME)/$(FOUNDRY_IMAGE):$(TAG) || true
	docker rmi $(LOCAL_REGISTRY_NAME)/$(BLACKBOARD_IMAGE):$(TAG) || true

stop:
	$(call log_green, Stopping Docker containers...)
	docker compose stop || true

up: pull
	$(call log_green, Starting Docker containers with custom environment file...)
	@if [ ! -f .env.agent ] || [ ! -f .env.compose ] || [ ! -f .env.blackboard ]; then \
		echo "Error: Required environment files (.env.agent, .env.compose, .env.blackboard) not found."; \
		exit 1; \
	fi
	docker compose --env-file .env.compose up -d --remove-orphans

down:
	$(call log_green, Stopping Docker containers and removing orphaned containers...)
	docker compose down --remove-orphans

check:
	$(call log_green, Checking Docker containers...)
	docker compose ps

init: down
	docker volume rm $$(docker volume ls -q --filter dangling=true) || true
	sudo rm -fr data
	mkdir -p data/clickhouse/data || true
	mkdir -p data/clickhouse/logs || true
	mkdir -p data/postgres/data || true
	mkdir -p data/minio/data || true
	mkdir -p data/agent-registry/data || true
	mkdir -p data/blackboard/data || true
	mkdir -p data/blackboard/logs || true
	mkdir -p data/blackboard/backup || true
	mkdir -p data/agent-foundry/worker/logs || true
	mkdir -p data/agent-foundry/worker/data || true
	mkdir -p data/agent-foundry/api/logs || true

clean:
	$(call log_green, Cleaning up Docker containers and images...)
	docker system prune -f
	docker container prune -f
	docker volume prune -f
	docker network prune -f
