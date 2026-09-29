FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Train models at image build time so the API starts with artifacts present.
RUN python training/build_training_data.py \
    && python training/train_sentiment.py \
    && python training/train_review_detector.py

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
