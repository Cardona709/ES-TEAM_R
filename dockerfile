FROM python:3.12

WORKDIR /app

RUN apt-get -y update && apt-get install -yqq wget curl unzip xvfb
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
RUN apt-get update && \
  apt-get install -y google-chrome-stable
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/` curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE `/chromedriver_linux64.zip

# Download the specific version of ChromeDriver for Chrome 124.0.6367.91
RUN wget "https://storage.googleapis.com/chrome-for-testing-public/124.0.6367.91/linux64/chrome-linux64.zip" && \
  unzip chrome-linux64.zip -d /usr/bin/chromedriver 

ENV DISPLAY=:99

# Build the app
COPY requirements.txt .
RUN pip install --upgrade pip && \
  pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "-u", "main.py" ]
