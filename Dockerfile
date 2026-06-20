FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 创建挂载目录
RUN mkdir -p /strm /downloads /videos

ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
