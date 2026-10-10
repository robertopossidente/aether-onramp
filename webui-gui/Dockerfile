FROM python:3.12-alpine
WORKDIR /app
COPY app.py index.html ./
USER nobody
EXPOSE 8088
CMD ["python", "-u", "app.py"]
