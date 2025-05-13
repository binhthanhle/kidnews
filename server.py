# server.py
# Requires installation: pip install Flask Flask-CORS gnews
# Note: gnews might install newspaper3k as a dependency.

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from gnews import GNews # Import the GNews client
import time

# --- Configuration ---
# No API Key needed for GNews basic usage

# Map frontend categories to GNews topics
# GNews topics: WORLD, NATION, BUSINESS, TECHNOLOGY, ENTERTAINMENT, SPORTS, SCIENCE, HEALTH
CATEGORY_TO_TOPIC_MAP = {
    'business': 'BUSINESS',
    'entertainment': 'ENTERTAINMENT',
    'general': 'NATION', # Map general to Nation (or WORLD)
    'health': 'HEALTH',
    'science': 'SCIENCE',
    'sports': 'SPORTS',
    'technology': 'TECHNOLOGY',
    # Add other mappings if needed, e.g., 'world': 'WORLD'
}

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app) # Enable CORS for all origins

# --- API Endpoint ---
@app.route('/fetch-news', methods=['GET'])
def fetch_news():
    """
    Endpoint to fetch news using the GNews library based on a category query parameter.
    Example usage: http://localhost:5000/fetch-news?category=technology
    """
    category = request.args.get('category') # Get category from query param

    # --- Input Validation ---
    if not category:
        return jsonify({"error": "Missing 'category' query parameter"}), 400

    # Map the requested category to a GNews topic
    topic = CATEGORY_TO_TOPIC_MAP.get(category.lower())
    if not topic:
        # You could fall back to a default topic or return an error
        print(f"Warning: Unknown category '{category}' requested. Falling back to 'NATION'.")
        topic = 'NATION'
        # Alternatively, return an error:
        # return jsonify({"error": f"Unsupported category: {category}"}), 400

    # --- Fetch from Google News via GNews ---
    print(f"Fetching news for topic '{topic}' (mapped from category '{category}')...")
    try:
        # Initialize GNews client (can specify language and country)
        # Consider making the client a global variable if performance is critical,
        # but re-initializing per request is often fine for moderate traffic.
        google_news = GNews(language='en', country='US', max_results=15) # Get more results initially

        # Fetch news by the mapped topic
        articles = google_news.get_news_by_topic(topic)

        if not articles:
             print(f"No articles found by GNews for topic '{topic}'.")
             return jsonify([]) # Return empty list

        print(f"Received {len(articles)} articles from GNews for topic '{topic}'. Processing...")

        # Process articles into the format expected by the frontend
        processed_articles = []
        for article in articles:
            # Basic check if essential data is present
            if not article.get('title') or not article.get('url'):
                print(f"Skipping article due to missing title or URL: {article}")
                continue

            # Prepare source information
            source_name = article.get('publisher', {}).get('title', 'Unknown Source')

            # Use description for summary and revision text (GNews doesn't reliably provide more)
            description = article.get('description', 'No description available.')

            processed_articles.append({
                "title": article.get('title'),
                "description": description,
                "content": None, # NewsAPI specific field, set to None
                "url": article.get('url'),
                "urlToImage": None, # GNews doesn't provide a direct image URL
                "source": {"name": source_name, "id": None}, # Match frontend structure
                # Use description for revision (no reliable full text)
                "fullTextForRevision": description,
                "scrapedTextAvailable": False # Indicate scraping wasn't done/successful
            })
            # Optional delay if needed
            # time.sleep(0.1)

        print(f"Finished processing for topic '{topic}'. Returning {len(processed_articles)} articles.")
        return jsonify(processed_articles)

    except Exception as e:
        # Handle potential errors during GNews fetching or processing
        print(f"Error using GNews for topic '{topic}': {e}")
        # Check for common network-related errors if possible, otherwise generic error
        error_message = "An error occurred while fetching news via GNews."
        # Add more specific error checks if needed based on GNews library exceptions
        return jsonify({"error": error_message}), 500

# --- Run the Server ---
if __name__ == '__main__':
    print("Starting Flask server on http://localhost:5000")
    print("This version uses the GNews library to fetch news headlines.")
    # Note: No API key needed for GNews basic usage
    app.run(host='0.0.0.0', port=5000, debug=True) # Keep debug=True for development
