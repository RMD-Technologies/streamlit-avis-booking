# Use the official lightweight Python image
FROM python:3.12

# Set working directory
WORKDIR /app

# Install system dependencies for Firefox and Selenium
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    firefox-esr \
    unzip \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install GeckoDriver 
RUN GECKO_VERSION=0.36.0 && \
    wget https://github.com/mozilla/geckodriver/releases/download/v${GECKO_VERSION}/geckodriver-v${GECKO_VERSION}-linux64.tar.gz && \
    tar -xvzf geckodriver-v${GECKO_VERSION}-linux64.tar.gz && \
    mv geckodriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/geckodriver && \
    rm geckodriver-v${GECKO_VERSION}-linux64.tar.gz

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code
COPY app/ .

# Expose the default Streamlit port
EXPOSE 8501

# Print debug
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

# Run the Streamlit app
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
