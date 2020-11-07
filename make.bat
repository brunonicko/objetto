@ECHO OFF

pushd %~dp0
cd /d %~dp0

IF "%1" == "" (
    goto tests
) ELSE IF "%1" == "tests" (
    goto tests
) ELSE IF "%1" == "mypy" (
    goto mypy
) ELSE IF "%1" == "environment" (
    goto environment
) ELSE IF "%1" == "clean" (
    goto clean
) ELSE IF "%1" == "format" (
    goto format
) ELSE IF "%1" == "lint" (
    goto lint
) ELSE (
    echo Invalid Command
    goto end
)

:tests
python -m pytest .\tests
rem # pytest sandbox --doctest-modules
goto end

:mypy
mypy sandbox
goto end

:environment
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r dev_requirements.txt
goto end

:clean
rmdir /s /q .\.mypy_cache 2>nul
rmdir /s /q .\.pytest_cache 2>nul
rmdir /s /q .\dist 2>nul
del /S *.pyc >nul 2>&1
goto end

:format
forfiles /p .\sandbox /s /m *.py /c "cmd /c start /b black @path"
forfiles /p .\tests /s /m *.py /c "cmd /c start /b black @path"
black setup.py
goto end

:lint
rem # Stop if there are Python syntax errors or undefined names.
flake8 .\sandbox --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 .\tests --count --select=E9,F63,F7,F82 --show-source --statistics
rem # Exit-zero treats all errors as warnings.
flake8 .\sandbox --count --exit-zero --ignore=F403,F401 --max-complexity=10 --max-line-length=88 --statistics
flake8 .\tests --count --exit-zero --ignore=F403,F401 --max-complexity=10 --max-line-length=88 --statistics
goto end

:end
popd
