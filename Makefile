init:
	# Auto-generate vino configuration files
	./tools/mkconf.sh
	# Install pipenv: use pip3 if it exists, or fallback to pip
	command -v pip3 2>&1 >/dev/null && pip3 install pipenv --upgrade || \
		pip install pipenv --upgrade
	# Install dependencies in a virtual environment
	pipenv install --dev
	# Create data directory if needed
	mkdir -p data
	# Create or upgrade database
	pipenv run ./manage.py migrate
