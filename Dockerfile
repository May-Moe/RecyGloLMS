# Use official Python image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PORT=8080

# Expose port
EXPOSE 8080

# Start the app with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "--workers=4", "--timeout=120", "recyglolms:create_app()"]
