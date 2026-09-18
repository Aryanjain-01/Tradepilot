FROM python:3.13-slim as backend-builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM node:20 as frontend-builder

WORKDIR /app
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim

WORKDIR /app

# Install backend dependencies from builder
COPY --from=backend-builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=backend-builder /usr/local/bin/ /usr/local/bin/

# Copy backend source
COPY backend/ ./backend/

# Copy sample market data
COPY data/ ./data/

# Copy built frontend
COPY --from=frontend-builder /app/dist/ ./frontend/dist/

# Environment settings
ENV RENDER=true
ENV PYTHONPATH=/app/backend

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
