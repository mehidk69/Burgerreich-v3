FROM python:3.12-slim

# Pi4 is arm64 — python:3.12-slim supports it natively
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY collectors/requirements.txt /app/collectors/requirements.txt
RUN pip install --no-cache-dir -r collectors/requirements.txt

# Copy project
COPY . /app/

# Nginx config
COPY deploy/nginx-docker.conf /etc/nginx/sites-available/default

# Cron schedule — every 30 minutes
RUN echo "*/30 * * * * cd /app && /usr/local/bin/python run_all.py >> /var/log/burgerreich.log 2>&1" > /etc/cron.d/burgerreich \
    && chmod 0644 /etc/cron.d/burgerreich \
    && crontab /etc/cron.d/burgerreich

# Create log file
RUN touch /var/log/burgerreich.log

# Initial data collection on build
RUN cd /app && python run_all.py --quick || true

EXPOSE 80

# Start cron + nginx
CMD cron && nginx -g "daemon off;"
