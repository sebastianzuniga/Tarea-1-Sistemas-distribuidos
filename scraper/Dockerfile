FROM python:3.11-slim

# Evitar preguntas de zona horaria, etc.
ENV DEBIAN_FRONTEND=noninteractive

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl gnupg unzip fonts-liberation libappindicator3-1 libasound2 \
    libnspr4 libnss3 libxss1 libxtst6 xdg-utils libatk-bridge2.0-0 libgtk-3-0 \
    libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 libxi6 libxrandr2 \
    libgbm-dev libxshmfence-dev ca-certificates fonts-freefont-ttf \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Instalar Chrome estable
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Instalar ChromeDriver
ENV CHROMEDRIVER_VERSION=114.0.5735.90

RUN wget -q https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm chromedriver_linux64.zip

# Copiar código fuente
WORKDIR /app
COPY scraper/ /app/scraper
COPY requirements.txt /app/
COPY wait-for-redis.sh /app/

RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x /app/wait-for-redis.sh

# Variables de entorno
ENV PYTHONPATH=/app

# Comando para esperar redis y ejecutar el scraper
CMD ["sh", "-c", "./wait-for-redis.sh && python -m scraper.main"]

# Verificación
RUN google-chrome --version && chromedriver --version
