.DEFAULT_GOAL := help

export SECRET_KEY?=badf00d
export DJANGO_SETTINGS_MODULE?=frontend.settings.base_lambda
export APP_IS_BEHIND_CLOUDFRONT?=False

REQUIREMENTS = "lambda-layers/DependenciesLayer/requirements.txt"


.PHONY: all
all: clean collectstatic lambda-layers/DependenciesLayer/requirements.txt ## Rebuild everything this Makefile knows how to build

.PHONY: clean
clean: ## Delete any generated static asset or req.txt files and git-restore the rendered API documentation file
	rm -rf frontend/static_files/ lambda-layers/DependenciesLayer/requirements.txt

.PHONY: collectstatic
collectstatic: ## Rebuild the static assets
	pipenv run collectstatic

.PHONY: check_empty
check_empty: ## Check if the requirements.txt file is empty
	if [ ! -s "${REQUIREMENTS}" ]; then
		echo "File is empty"
	else
		echo "File is not empty"
	fi

lambda-layers/DependenciesLayer/requirements.txt: Pipfile Pipfile.lock ## Update the requirements.txt file used to build this Lambda function's DependenciesLayer
	pipenv requirements | sed "s/^-e //" >lambda-layers/DependenciesLayer/requirements.txt

.PHONY: help
# gratuitously adapted from https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help: ## Display this help text
	@grep -E '^[-a-zA-Z0-9_/.]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%s\033[0m\n\t%s\n", $$1, $$2}'
