FROM chrisgatt/cpp-python-dev

WORKDIR var/www/html

COPY . .

RUN pip install --upgrade pip

RUN pip install --upgrade pip setuptools

RUN pip install --upgrade wheel

RUN pip install -r requirements.txt

EXPOSE 5001

CMD ["python", "gateway.py"]