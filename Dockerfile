# 1. Use the official Python language box
FROM python:3.11-slim

# 2. Create a folder inside the container for our code
WORKDIR /app

# 3. Copy our grocery list of libraries inside and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy our main code file into the container
COPY main.py .

# 5. Tell the container to turn on the API server and start listening!
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]