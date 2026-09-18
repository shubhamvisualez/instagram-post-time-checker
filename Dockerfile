FROM mcr.microsoft.com/playwright/python:v1.63.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "--timeout", "60", "app:app"]
