from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)

feedback_file = "feedback1.csv"

if not os.path.exists(feedback_file):
    df = pd.DataFrame(columns=["id", "feedback_for", "school", "feedback", "rating", "date"])
    df.to_csv(feedback_file, index=False)

def read_feedback():
    if os.path.exists(feedback_file):
        return pd.read_csv(feedback_file).fillna("").to_dict(orient="records")
    return []


@app.route("/feedback/read", methods=["GET"])
def get_feedback():
    feedbacks = read_feedback()

    if not feedbacks:
        return jsonify({})  # Return an empty dictionary if no feedbacks are found

    result = {}

    # Process feedbacks
    for fb in feedbacks:
        entity_name = fb.get("school", "Unknown").strip()  # Use "school" or "teacher" as the key
        if entity_name and entity_name.lower() not in ["none", "null"]:

            # Initialize entity if not already present in result
            if entity_name not in result:
                result[entity_name] = {
                    "rating": 0,
                    "feedbacks": [],
                    "count": 0,
                    "total_rating": 0
                }

            # Extract rating
            rating_str = fb.get("rating", "0")
            if isinstance(rating_str, str) and "star" in rating_str.lower():
                match = re.search(r"(\d+)", rating_str)
                rating = float(match.group(1)) if match else 0.0
            else:
                try:
                    rating = float(rating_str)
                except (ValueError, TypeError):
                    rating = 0.0

            # Store feedback details
            if fb.get("feedback") and fb.get("feedback") != "nan" and not pd.isna(fb.get("feedback")):
                feedback_entry = {
                    "feedback": fb.get("feedback", ""),
                    "date": fb.get("date", "Unknown Date")
                }
                result[entity_name]["feedbacks"].append(feedback_entry)

            result[entity_name]["total_rating"] += rating
            result[entity_name]["count"] += 1

    # Calculate average ratings for each entity
    for entity_name, data in result.items():
        avg_rating = round(data["total_rating"] / data["count"], 1) if data["count"] > 0 else 0
        result[entity_name]["rating"] = f"{avg_rating}/5"

    return jsonify(result)



@app.route("/feedback/submit", methods=["POST"])
def submit_feedback():
    try:
        data = request.json
        feedbacks = read_feedback()
        
        # Get the highest existing ID and increment by 1
        new_id = max([fb.get("id", 0) for fb in feedbacks], default=0) + 1
        
        # Format the rating appropriately
        rating_str = data.get("rating", "0")
        if isinstance(rating_str, str) and "star" in rating_str.lower():
            # Keep the original format if it contains "star"
            formatted_rating = rating_str
        else:
            # Convert to float and format
            try:
                rating = float(rating_str)
                formatted_rating = str(rating)
            except (ValueError, TypeError):
                formatted_rating = "0"
        
        # Format the date if not provided
        if not data.get("date"):
            formatted_date = datetime.now().strftime("%d/%m/%Y")
        else:
            formatted_date = data.get("date")
        
        new_feedback = {
            "id": new_id,
            "feedback_for": data.get("feedback_for", ""),
            "school": data.get("school", ""),
            "feedback": data.get("feedback", ""),
            "rating": formatted_rating,
            "date": formatted_date,
        }
        
        # Use DataFrame to safely append to the CSV
        df = pd.DataFrame([new_feedback])
        if os.path.exists(feedback_file) and os.path.getsize(feedback_file) > 0:
            df.to_csv(feedback_file, mode="a", header=False, index=False)
        else:
            df.to_csv(feedback_file, index=False)
        
        return jsonify({"message": "Feedback submitted successfully!", "id": new_id}), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    feedbacks = read_feedback()
    print("Feedbacks:", feedbacks)
    app.run(host="0.0.0.0", debug=True, port=5000)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    