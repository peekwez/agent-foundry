include Make.in

REGISTRY_NAME=docker.agent-foundry.canadacentral.cloudapp.azure.com
TAG:=latest


push:
	$(call log_green, Pushing Docker images to the registry...)
	docker tag agent-foundry-api/python312:$(TAG) $(REGISTRY_NAME)/agent-foundry-api/python312:$(TAG) || true
	docker push $(REGISTRY_NAME)/agent-foundry-api/python312:$(TAG)
	docker tag blackboard-mcp/python313:$(TAG) $(REGISTRY_NAME)/blackboard-mcp/python313:$(TAG) || true
	docker push $(REGISTRY_NAME)/blackboard-mcp/python313:$(TAG)

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
	mkdir -p data/agent-foundry/api/logs || true

up:
    $(call log_green, Starting Docker containers...)
    docker compose up -d --env-file .env.compose

down:
    $(call log_green, Stopping Docker containers...)
    docker compose down

check:
    $(call log_green, Checking Docker containers...)
    docker compose ps

clean:
    $(call log_green, Cleaning up Docker containers and images...)
    docker system prune -f
    docker container prune -f
