# Use the official lightweight Python image
FROM python:3.12

# Set working directory
WORKDIR /app

# Copy the rest of the app code
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install datamapplot
# Expose the default Streamlit port
EXPOSE 8000

# Print debug
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

# Run the Streamlit app
CMD ["python", "api.py"]
