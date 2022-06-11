#
# Makefile for Funance app
#

.PHONY: help init update clean tail test

.DEFAULT_GOAL := help

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

#
# https://click.palletsprojects.com/en/7.x/setuptools/#setuptools-integration
#
init: ## Create venv and install dependencies
	@pip3 install --editable .[dev]

update: ## Update the pip package
	@pip3 install --upgrade .

clean: ## Clean python cache files
	@find . -type f -name "*.py[co]" -delete
	@find . -type d -name "__pycache__" -delete

tail: ## Tail the log file
	@tail -f .tmp/log.tmp

test: ## Run python unit tests
	@nose2