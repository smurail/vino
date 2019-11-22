init:
	./tools/mkconf.sh
	pip install pipenv --upgrade
	pipenv install --dev
	mkdir -p data
	pipenv run ./manage.py migrate
