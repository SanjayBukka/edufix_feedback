from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

feedback_file = "feedback2.csv"

def initialize_feedback_file():
    if not os.path.exists(feedback_file):
        df = pd.DataFrame(columns=["id", "feedback_for", "school", "teacher", "feedback", "rating", "date"])
        df.to_csv(feedback_file, index=False)

def read_feedback():
    if os.path.exists(feedback_file):
        return pd.read_csv(feedback_file).fillna("").to_dict(orient="records")
    return []

def convert_rating(rating_str):
    try:
        if isinstance(rating_str, str) and 'star' in rating_str.lower():
            return float(rating_str.split()[0])
        return float(rating_str)
    except (ValueError, TypeError):
        return 0

@app.route("/feedback/read", methods=["GET"])
def get_feedback():
    feedbacks = read_feedback()
    result = {}

    for fb in feedbacks:
        feedback_type = fb.get("feedback_for", "").strip().lower()
        school_name = fb.get("school", "Unknown").strip()
        rating = convert_rating(fb.get("rating", 0))
        
        # Skip invalid ratings
        if not 1 <= rating <= 5:
            continue

        feedback_date = fb.get("date", "Unknown Date")
        feedback_text = fb.get("feedback", "")

        # Process school feedback
        if feedback_type == "school":
            if school_name not in result:
                result[school_name] = {
                    "count": 0,
                    "feedbacks": [],
                    "total_rating": 0
                }
            
            result[school_name]["feedbacks"].append({
                "date": feedback_date,
                "feedback": feedback_text
            })
            result[school_name]["total_rating"] += rating
            result[school_name]["count"] += 1

        # Process teacher feedback
        elif feedback_type == "teacher":
            teacher_name = fb.get("teacher", "").strip()
            if not teacher_name:
                continue

            teacher_key = f"{teacher_name} ({school_name})"
            
            if teacher_key not in result:
                result[teacher_key] = {
                    "count": 0,
                    "feedbacks": [],
                    "total_rating": 0
                }
            
            result[teacher_key]["feedbacks"].append({
                "date": feedback_date,
                "feedback": feedback_text
            })
            result[teacher_key]["total_rating"] += rating
            result[teacher_key]["count"] += 1

    # Calculate average ratings and sort feedbacks
    for key, data in result.items():
        if data["count"] > 0:
            avg_rating = data["total_rating"] / data["count"]
            data["rating"] = f"{avg_rating:.1f}/5"
            
            # Sort feedbacks by date (newest first)
            data["feedbacks"].sort(key=lambda x: x["date"] if x["date"] else "0", reverse=True)
            
            # Remove duplicate feedbacks
            seen_feedbacks = set()
            unique_feedbacks = []
            for fb in data["feedbacks"]:
                feedback_key = f"{fb['feedback']}_{fb['date']}"
                if feedback_key not in seen_feedbacks:
                    seen_feedbacks.add(feedback_key)
                    unique_feedbacks.append(fb)
            data["feedbacks"] = unique_feedbacks

    return jsonify(result)

@app.route("/feedback/submit", methods=["POST"])
def submit_feedback():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        feedbacks = read_feedback()
        
        # Get the highest existing ID and increment by 1
        new_id = max([fb.get("id", 0) for fb in feedbacks], default=0) + 1
        
        # Handle rating conversion
        try:
            rating_str = str(data.get("rating", "0"))
            if "star" in rating_str.lower():
                rating = float(rating_str.split()[0])
            else:
                rating = float(rating_str)
            
            if not 1 <= rating <= 5:
                return jsonify({"error": "Rating must be between 1 and 5"}), 400
                
            formatted_rating = str(rating)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid rating format"}), 400
        
        # Format the date
        try:
            if "date" in data and data["date"]:
                datetime.strptime(data["date"], "%Y-%m-%d")  # Update date format
                formatted_date = data["date"]
            else:
                formatted_date = datetime.now().strftime("%Y-%m-%d")  # Update date format
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        new_feedback = {
            "id": new_id,
            "feedback_for": data.get("feedback_for", ""),
            "school": data.get("school", ""),
            "teacher": data.get("teacher", ""),
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
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == "__main__":
    initialize_feedback_file()
    app.run(host="0.0.0.0", debug=True, port=5000)