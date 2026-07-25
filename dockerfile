FROM python:3.11-slim

RUN my-nginx -p

WORKDIR /my-nginx

COPY index.html /my-nginx/

EXPOSE 8000

CMD ["my-app", "--host", "0.0.0.0", "--port", "8000"]
