from invoke import task  # type: ignore


@task
def docs(c):
    c.run("sphinx-build -M html ./docs/source ./docs/build")


@task
def tests(c):
    c.run("python -m pytest -vv -rs tests")
    c.run("python -m pytest --doctest-modules -vv -rs README.rst")


@task
def tox(c):
    c.run("tox")


@task
def mypy(c):
    c.run("mypy objetto")


@task
def lint(c):
    c.run("flake8 objetto --count --select=E9,F63,F7,F82 --show-source --statistics")
    c.run("flake8 tests --count --select=E9,F63,F7,F82 --show-source --statistics")
    c.run(
        "flake8 objetto --count --ignore=F403,F401,E203,E731,C901,W503,F811 "
        "--max-line-length=120 --statistics"
    )
    c.run(
        "flake8 tests --count --ignore=F403,F401,E203,E731,C901,W503,F811 "
        "--max-line-length=120 --statistics"
    )


@task
def black(c):
    c.run("black objetto --line-length=120")
    c.run("black tests --line-length=120")


@task
def checks(c):
    black(c)
    lint(c)
    mypy(c)
    tox(c)
    docs(c)
