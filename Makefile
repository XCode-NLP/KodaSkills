.PHONY: help install metadata clean

help: ## Показать справку по командам
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Подготовить виртуальное окружение генератора
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip -q
	.venv/bin/pip install -r requirements.txt -q

metadata: ## Запустить генерацию metadata.json
	@.venv/bin/python generator.py

clean: ## Удалить виртуальное окружение генератора
	rm -rf .venv
