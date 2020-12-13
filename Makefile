.DEFAULT_GOAL := help

export SECRET_KEY?=badf00d
export DJANGO_SETTINGS_MODULE?=aggregator.settings.base_lambda
export APP_IS_BEHIND_CLOUDFRONT?=False

.PHONY: all
all: clean collectstatic lambda-layers/DependenciesLayer/requirements.txt aggregator/apps/api/v1/templates/api_docs_rendered.html ## Rebuild everything this Makefile knows how to build

.PHONY: clean
clean: ## Delete any generated static asset or req.txt files and git-restore the rendered API documentation file
	rm -rf aggregator/static_files/ lambda-layers/DependenciesLayer/requirements.txt
	git checkout aggregator/apps/api/v1/templates/api_docs_rendered.html

.PHONY: collectstatic
collectstatic: ## Rebuild the static assets
	python manage.py collectstatic --noinput --clear

lambda-layers/DependenciesLayer/requirements.txt: Pipfile Pipfile.lock ## Update the requirements.txt file used to build this Lambda function's DependenciesLayer
	pipenv lock -r | sed "s/^-e //" >lambda-layers/DependenciesLayer/requirements.txt

.PHONY: aggregator/apps/api/v1/templates/api_docs_rendered.html
aggregator/apps/api/v1/templates/api_docs_rendered.html: ## Rebuild the API documentation page
	python manage.py build_docs

.PHONY: help
# gratuitously adapted from https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help: ## Display this help text
	@grep -E '^[-a-zA-Z0-9_/.]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%s\033[0m\n\t%s\n", $$1, $$2}'
