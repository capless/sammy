FROM capless/capless-docker:jupyter
COPY . /code
RUN python -m pip install --upgrade poetry
RUN poetry run pip install --upgrade pip
RUN poetry install
