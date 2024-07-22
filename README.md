# Django Template
Template API with django

### Set up environment and run

1.  Make sure Python 3.9 and virtualenv are already installed.
2.  Clone the repo and configure the virtual environment and run [pre-commit][pre-commit] for the first time:

```
$ python -m venv env
$ source env/bin/activate for mac or env\scripts\activate for windows
$ pip install -r requirements/local.txt
$ pre-commit install
$ pre-commit run --all-files
```

3. Set up environment variables. Examples exist in `.env.sample`:

```
cp .env.sample .env
```

4. Edit `.env` to reflect your local environment settings and export them to your terminal

```
(env) $ source .env 
```

5.  Run the initial migrations, build the database, create user and run project

```
(env) $ python manage.py migrate
(env) $ python manage.py createsuperuser
(env) $ python manage.py runserver
```


### Contribution

1. Create a new branch of the `dev` branch.
2. Make your changes.
3. Push the new branch to github and create a PR to the `dev` branch

