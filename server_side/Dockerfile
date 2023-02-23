FROM python:3.9.1

WORKDIR var/www/html

COPY . .

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "chat_server.py"]