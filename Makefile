init:
	./tools/mkconf.sh
	pip install pipenv --upgrade
	pipenv install --dev
