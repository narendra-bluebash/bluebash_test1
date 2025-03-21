FROM python:3.12
USER root

WORKDIR /app
RUN rm -f /etc/apt/apt.conf.d/docker-clean \
    && echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache


RUN curl -sSL https://install.python-poetry.org | python3 -

ENV POETRY_HOME="/root/.local"
ENV PATH="$POETRY_HOME/bin:$PATH"
COPY pyproject.toml poetry.lock* /app/

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-root
# Copy project files
RUN apt update && apt install redis-server -y


ADD ./app /app/app
COPY main.py /app/main.py
ADD entrypoint.sh /app/
#RUN pip install gunicorn uvicorn

#CMD ["gunicorn", "-w", "3", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:7860"]
RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]