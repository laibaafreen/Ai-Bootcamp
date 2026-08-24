# Excercise
# EXERCISE: Build a Prediction API with Rate Limiting and Performance Metrics
# ----------------------------------------------------------------------------
# In this exercise, you will:
# 1. Create a FastAPI application that serves a machine learning model
# 2. Implement rate limiting to prevent API abuse
# 3. Add performance tracking to measure prediction latency
# 4. Implement a custom logging system to track model inputs and outputs
# 5. Create a dashboard endpoint to visualize model performance
# SETUP: Run this cell first to prepare the exercise environment
# !pip install fastapi uvicorn scikit-learn numpy pandas python-multipart
import numpy as np
import pandas as pd
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
import uuid
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris
import pickle
import uvicorn

# Create a simple ML model for the exercise
iris = load_iris()
X = iris.data
y = iris.target
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# Save model as a global variable for this exercise
iris_model = model
feature_names = iris.feature_names


# Define the input data model
class IrisFeatures(BaseModel):
    features: List[float]

    class Config:
        schema_extra = {
            "example": {
                "features": [5.1, 3.5, 1.4, 0.2]
            }
        }


# YOUR TASK: Complete the following code to build the API with rate limiting and performance tracking

# PART 1: Create the FastAPI application with rate limiting
# ---------------------------------------------------------
# Implement a rate limiter that allows each client (identified by IP address)
# to make a maximum of 5 requests per minute
# TODO: Complete the code below to create a rate limiter
class RateLimiter:
    def __init__(self, requests_limit: int = 5, window_seconds: int = 60):
        # TODO: Initialize the rate limiter with empty request tracking
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        # Dictionary mapping client_id -> list of timestamps of their recent requests
        self.request_log: Dict[str, List[float]] = {}

    def is_rate_limited(self, client_id: str) -> bool:
        # TODO: Check if the client has exceeded the rate limit
        current_time = time.time()

        # If we've never seen this client, they can't be rate limited
        if client_id not in self.request_log:
            return False

        # Keep only the timestamps that fall inside the current time window
        window_start = current_time - self.window_seconds
        recent_requests = [
            timestamp for timestamp in self.request_log[client_id]
            if timestamp > window_start
        ]
        # Save the cleaned-up list back (so old timestamps don't pile up forever)
        self.request_log[client_id] = recent_requests

        # If they already made "requests_limit" or more requests in this window, block them
        return len(recent_requests) >= self.requests_limit

    def add_request(self, client_id: str) -> None:
        # TODO: Record a new request for the client
        current_time = time.time()
        if client_id not in self.request_log:
            self.request_log[client_id] = []
        self.request_log[client_id].append(current_time)


# Create the app and rate limiter
app = FastAPI(title="Iris Model API with Rate Limiting")

# TODO: Initialize the rate limiter
rate_limiter = RateLimiter(requests_limit=5, window_seconds=60)


# TODO: Implement the rate limiting dependency
async def check_rate_limit(request: Request):
    # Extract client IP or use a default for testing
    client_id = request.client.host if request.client else "test-client"

    # Check if client is rate limited
    if rate_limiter.is_rate_limited(client_id):
        # If limited, raise HTTPException
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {rate_limiter.requests_limit} "
                   f"requests per {rate_limiter.window_seconds} seconds."
        )

    # Record this request as having happened
    rate_limiter.add_request(client_id)


# PART 2: Implement performance tracking
# --------------------------------------
# Create a system to track prediction latency and model performance

# TODO: Complete the code below to track performance metrics
performance_metrics = {
    # TODO: Initialize performance metrics dictionary
    "total_requests": 0,
    "successful_predictions": 0,
    "failed_predictions": 0,
    "total_response_time": 0.0,
    "avg_response_time": 0.0,
    "min_response_time": None,
    "max_response_time": None,
    "prediction_distribution": {0: 0, 1: 0, 2: 0},
    "last_updated": None,
}

# Keep a small log of recent predictions, similar to the monitoring example above
prediction_logs: List[Dict[str, Any]] = []


# TODO: Implement the function to update performance metrics
async def update_metrics(features, prediction, response_time, success: bool = True):
    # TODO: Update the performance metrics with the new prediction data
    performance_metrics["total_requests"] += 1

    if success:
        performance_metrics["successful_predictions"] += 1
        pred_class = int(prediction[0])
        performance_metrics["prediction_distribution"][pred_class] += 1
    else:
        performance_metrics["failed_predictions"] += 1

    # Update running total and average response time
    performance_metrics["total_response_time"] += response_time
    performance_metrics["avg_response_time"] = (
        performance_metrics["total_response_time"] / performance_metrics["total_requests"]
    )

    # Track fastest / slowest response seen so far
    if performance_metrics["min_response_time"] is None or response_time < performance_metrics["min_response_time"]:
        performance_metrics["min_response_time"] = response_time
    if performance_metrics["max_response_time"] is None or response_time > performance_metrics["max_response_time"]:
        performance_metrics["max_response_time"] = response_time

    performance_metrics["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Store a detailed record of this individual prediction
    prediction_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "features": features,
        "prediction": prediction,
        "response_time": response_time,
        "success": success,
    })

    # Keep only the last 100 logs so memory doesn't grow forever
    if len(prediction_logs) > 100:
        prediction_logs.pop(0)


# PART 3: Create the prediction endpoint
# --------------------------------------
# Implement the prediction endpoint with rate limiting and performance tracking

@app.post("/predict")
async def predict(iris_data: IrisFeatures, request: Request, rate_limit: None = Depends(check_rate_limit)):
    # TODO: Implement the prediction endpoint
    # 1. Record start time
    start_time = time.time()
    success = True
    prediction = None

    try:
        # 2. Make prediction
        features = np.array(iris_data.features).reshape(1, -1)
        prediction = iris_model.predict(features).tolist()
        prediction_proba = iris_model.predict_proba(features).tolist()

        response = {
            "prediction": prediction,
            "probability": prediction_proba,
        }
    except Exception as e:
        success = False
        response = {"error": str(e)}

    # 3. Calculate response time
    response_time = time.time() - start_time

    # 4. Update metrics
    await update_metrics(
        iris_data.features,
        prediction if success else None,
        response_time,
        success,
    )

    if not success:
        raise HTTPException(status_code=500, detail=response["error"])

    # 5. Return prediction response
    return response


# PART 4: Create a dashboard endpoint
# -----------------------------------
# Implement an endpoint to display performance metrics

@app.get("/dashboard")
async def dashboard():
    # TODO: Return a dashboard with performance metrics
    success_rate = 0.0
    if performance_metrics["total_requests"] > 0:
        success_rate = (
            performance_metrics["successful_predictions"] /
            performance_metrics["total_requests"] * 100
        )

    return {
        "summary": {
            "total_requests": performance_metrics["total_requests"],
            "successful_predictions": performance_metrics["successful_predictions"],
            "failed_predictions": performance_metrics["failed_predictions"],
            "success_rate_percent": round(success_rate, 2),
        },
        "latency": {
            "avg_response_time_sec": round(performance_metrics["avg_response_time"], 4),
            "min_response_time_sec": performance_metrics["min_response_time"],
            "max_response_time_sec": performance_metrics["max_response_time"],
        },
        "prediction_distribution": performance_metrics["prediction_distribution"],
        "last_updated": performance_metrics["last_updated"],
        "recent_predictions": prediction_logs[-10:],
    }


# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)