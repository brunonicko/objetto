import os
import shutil
import inspect

if not hasattr(inspect, "getargspec"):
    inspect.getargspec = inspect.getfullargspec  # type: ignore

from invoke import task  # type: ignore  # noqa


@task
def conform(c):
    c.run("isort objetto tests ./docs/source/conf.py setup.py -m 3 -l 88 --up --tc --lbt 0")
    c.run("black objetto --line-length=120")
    c.run("black tests --line-length=120")
    c.run("black setup.py --line-length=120")


@task
def lint(c):
    c.run("isort objetto tests ./docs/source/conf.py setup.py -m 3 -l 88 --up --tc --lbt 0 --check-only")
    c.run("black objetto --line-length=120 --check")
    c.run("black tests --line-length=120 --check")
    c.run("black setup.py --line-length=120 --check")

    c.run("flake8 objetto --count --select=E9,F63,F7,F82 --show-source --statistics")
    c.run("flake8 tests --count --select=E9,F63,F7,F82 --show-source --statistics")
    c.run(
        "flake8 objetto --count --ignore=F811,F405,F403,F401,E203,E731,C901,W503 "
        "--max-line-length=120 --statistics"
    )
    c.run("flake8 tests --count --ignore=F811,F405,F403,F401,E203,E731,C901,W503 --max-line-length=120 --statistics")


@task
def mypy(c):
    c.run("mypy objetto")


@task
def tests(c):
    c.run("python -m pytest -vv -rs tests")
    c.run("python -m pytest --doctest-modules -vv -rs README.rst")


@task
def docs(c):
    api_docs = "./docs/source/api"
    if os.path.exists(api_docs):
        assert os.path.isdir(api_docs), "not a directory: {!r}".format(api_docs)
        shutil.rmtree(api_docs)
    os.mkdir(api_docs)
    c.run("sphinx-apidoc objetto --separate --module-first --no-toc --force --output-dir {}".format(api_docs))

    for root, dirs, files in os.walk(api_docs, topdown=False):
        for name in files:
            file_path = os.path.join(root, name)
            if file_path.endswith(".rst"):
                with open(file_path, "rb") as open_file:
                    content = open_file.read()
                content = content.replace(b"\r\n", b"\n")
                with open(file_path, "wb") as open_file:
                    open_file.write(content)

    c.run("sphinx-build -M html ./docs/source ./docs/build")


@task
def checks(c):
    conform(c)
    lint(c)
    mypy(c)
    tests(c)
    docs(c)
