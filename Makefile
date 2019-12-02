init:
	./tools/mkconf.sh
	# Install pipenv: use pip3 if it exists, or fallback to pip
	command -v pip3 2>&1 >/dev/null && pip3 install pipenv --upgrade || \
		pip install pipenv --upgrade
	pipenv install --dev
	mkdir -p data
	pipenv run ./manage.py migrate
