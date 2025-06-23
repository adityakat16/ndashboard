# Use a base image that includes Python and has a good foundation for Chrome
FROM python:3.9-slim-buster

# Install Chrome and its dependencies
# This is a common set of dependencies for Chrome headless
RUN apt-get update && apt-get install -y \
    gnupg \
    wget \
    curl \
    unzip \
    fontconfig \
    libnspr4 \
    libnss3 \
    libxss1 \
    libappindicator1 \
    libindicator7 \
    fonts-liberation \
    xdg-utils \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Download and install Google Chrome
# Using the stable version
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable

# Set working directory
WORKDIR /app

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port your Flask app will run on
# Render typically maps internal port 10000 (THIS IS A COMMENT ON ITS OWN LINE)
EXPOSE 10000

# Command to run the application using Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
