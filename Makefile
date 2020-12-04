.DEFAULT_GOAL := please-explicitly-choose-a-target

.PHONY: collectstatic
collectstatic: export SECRET_KEY?=badf00d
collectstatic: export DJANGO_SETTINGS_MODULE?=aggregator.settings.base_lambda
collectstatic:
	python manage.py collectstatic --noinput --clear

lambda-layers/DependenciesLayer/requirements.txt: Pipfile Pipfile.lock
	pipenv lock -r | sed "s/^-e //" >lambda-layers/DependenciesLayer/requirements.txt
