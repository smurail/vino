# Vino

This project is mainly hosted at [SourceSup](https://sourcesup.renater.fr/projects/vino/).
Please, consult the [Wiki](https://sourcesup.renater.fr/wiki/vino/index) for more information.

## Setup development environment

As of december 2019, ViNO is using `pipenv` to manage dependencies and virtual
environment. To install required modules, generate default config files, and
create local database, simply run:

    make init

You should then create a Django super user:

    pipenv run ./manage.py createsuperuser

You are now all setup to launch the debug server:

    pipenv run ./manage.py runserver
    # Go to <http://localhost:8000/admin> to work with ViNO!

To run a command inside the virtual environment you can either enter pipenv
shell, either run it with `pipenv run`. For example, to launch Django shell:

    pipenv shell
    # You are now in your local virtual environment
    ./manage.py shell
    # To quit use <ctrl-D>, once for the Django shell, once for the pipenv one

    # Alternatively you can do
    pipenv run ./manage.py shell


## Database maintenance

Don't forget to migrate database when pulling last commits:

    pipenv run ./manage.py migrate

To import all samples in `data/samples` directory run this command (don't
forget to specify your username):

    pipenv run ./manage.py populatedb <username>

You want to completely reset whole ViNO database without messing with Django
users and groups? Just do:

    # This will unapply each migration one by one
    pipenv run ./manage.py migrate sharekernel zero
    # As usual, to update database to latest migration
    pipenv run ./manage.py migrate

Alternatively, you can empty vino data from database with this custom command:

    # This will drop sharekernel data without resetting AUTOINCREMENT
    pipenv run ./manage.py resetdb


## Docker: production server

Docker Compose can be used to easily set up a simple production server. You
will need [Docker](https://www.docker.com) and
[Docker Compose](https://docs.docker.com/compose).

The `docker-compose.yml` file defines two services: a backend that uses
[uWSGI](https://uwsgi-docs.readthedocs.io) to run
[Django](https://www.djangoproject.com) web application, and an HTTP frontend
that runs [nginx](https://www.nginx.com/) as an interface to this backend. You
can of course use this production configuration as an example to deploy your
own custom solution. Configuration files for uWSGI and nginx are located in
`./tools/docker` directory.

### Prerequisites

Once you have [installed Docker](https://docs.docker.com/get-docker/), you
need to install [Compose](https://docs.docker.com/compose/install/). To install
it locally easily you can do it with pip:

    pipenv run pip install docker-compose

### Start the production server

Production server listen on port 80 by default, you can customize it with
VINO_FRONTEND_PORT environment variable.

    # To build and start the production server on port 8080
    # Run this command from the vino source directory
    VINO_FRONTEND_PORT=8080 docker-compose up -d --build
    # Or, if you installed docker-compose with pip
    VINO_FRONTEND_PORT=8080 pipenv run docker-compose up -d --build

Then open your web browser and go to <http://localhost:8080/>.

    # To stop server
    docker-compose down
    # Or restart it
    docker-compose restart
