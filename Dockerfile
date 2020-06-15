FROM python:3.6-slim-stretch

WORKDIR /app

COPY Categorization/ /app/Categorization

COPY uncategorized.txt /app/

COPY categorization.py /app/

COPY methodology.py /app/

RUN pip install numpy scipy scikit-learn

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y netcat-openbsd gcc && \
    apt-get clean

RUN pip install psycopg2-binary

RUN pip install nltk

CMD [ "python","categorization.py" ] 
