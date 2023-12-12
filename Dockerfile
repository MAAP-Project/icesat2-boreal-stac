FROM --platform=linux/amd64 python:3.11

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && unzip awscliv2.zip && ./aws/install

RUN apt-get install git

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY *.py .

CMD python cli.py --s3_path=s3://nasa-maap-data-store/file-staging/nasa-map/icesat2-boreal/${ICESAT_S3_ITEM}.tif && aws s3 cp /tmp/${ICESAT_S3_ITEM}.json s3://icesat2-boreal-items/${ICESAT_S3_ITEM}.json