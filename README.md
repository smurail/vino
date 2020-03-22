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

You want to completely reset whole ViNO database without messing with Django
users and groups? Just do:

    # This will unapply each migration one by one
    pipenv run ./manage.py migrate sharekernel zero
    # As usual, to update database to latest migration
    pipenv run ./manage.py migrate


## Working with Docker

**WARNING: This section must be updated!**

A "Dockerfile" is provided for easily building your development environment. It is achieved in 3 steps:

 - [install](https://docs.docker.com/engine/installation/) docker on your computer
 - build the docker image: 
   `docker build -t vinosite .`
 - run the docker image just created: 
 `docker run --rm -p 8000:8000 --volume=$(pwd):/vino vinosite`

Then you can test the web application by opening a web browser on `http://localhost:8000/sharekernel`.

If you want to run the image in interactive mode, you can run:
 `docker run -i -t --rm --volume=$(pwd):/vino vinosite ipython`
and then run in the console `%run shell.py`. Now you can import modules from vino-py and vinosite.

You can also get a `bash` console with this command:
  `docker run -i -t --rm --volume=$(pwd):/vino vinosite bash`

For entering in debug mode, first start a shell on your container (with port redirection):
  `docker run -i -t --rm -p 8000:8000 --volume=$(pwd):/vino vinosite bash`
And then, start the server in debug mode:
  `python -m pdb manage.py runserver 0.0.0.0:8000`
You can now add a breackpoint anywhere in your code with `import pdb; pdb.set_trace()`

See also this tutorial for using the debugger pdb https://mike.tig.as/blog/2010/09/14/pdb/
