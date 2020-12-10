.PHONY: all
all: clean collectstatic lambda-layers/DependenciesLayer/requirements.txt

.PHONY: clean
clean:
	rm -rf aggregator/static_files/ lambda-layers/DependenciesLayer/requirements.txt

.PHONY: collectstatic
collectstatic: export SECRET_KEY?=badf00d
collectstatic: export DJANGO_SETTINGS_MODULE?=aggregator.settings.base_lambda
collectstatic:
	python manage.py collectstatic --noinput --clear

lambda-layers/DependenciesLayer/requirements.txt: Pipfile Pipfile.lock
	pipenv lock -r | sed "s/^-e //" >lambda-layers/DependenciesLayer/requirements.txt
