FROM python:3.11.2-alpine3.16

WORKDIR var/www/html/QaService

COPY . .

RUN pip install -r requirements.txt

CMD ["pytest", "-v", "-m", "sanity"]