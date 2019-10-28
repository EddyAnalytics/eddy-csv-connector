FROM python:3.7-slim as requirements

COPY Pipfile Pipfile.lock ./
RUN pip install pipenv \
    && pipenv check    \
    && pipenv lock -r > /requirements.txt


FROM python:3.7-slim

COPY --from=requirements /requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home app
WORKDIR /home/app
USER app

COPY *.py ./

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["eddy-csv-connector"]
