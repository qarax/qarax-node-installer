FROM python:3

WORKDIR /code

RUN apt-get update && apt-get install -y sshpass \
    && pip install ansible

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
