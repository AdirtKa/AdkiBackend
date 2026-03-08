up:
	@docker compose -f docker-compose-dev.yml up --build -d

down:
	@docker compose -f docker-compose-dev.yml down

create-env:
	@cp ./.env.example ./.env
	@chmod 0700 ./.env