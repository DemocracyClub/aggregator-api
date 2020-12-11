export SECRET_KEY?=badf00d
export DJANGO_SETTINGS_MODULE?=aggregator.settings.base_lambda
export APP_IS_BEHIND_CLOUDFRONT?=False

.PHONY: all
all: clean collectstatic lambda-layers/DependenciesLayer/requirements.txt aggregator/apps/api/v1/templates/api_docs_rendered.html

.PHONY: clean
clean:
	rm -rf aggregator/static_files/ lambda-layers/DependenciesLayer/requirements.txt

.PHONY: collectstatic
collectstatic:
	python manage.py collectstatic --noinput --clear

lambda-layers/DependenciesLayer/requirements.txt: Pipfile Pipfile.lock
	pipenv lock -r | sed "s/^-e //" >lambda-layers/DependenciesLayer/requirements.txt

.PHONY: aggregator/apps/api/v1/templates/api_docs_rendered.html
aggregator/apps/api/v1/templates/api_docs_rendered.html:
	python manage.py build_docs
