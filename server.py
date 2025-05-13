# server.py
# Requires installation: pip install Flask Flask-CORS gnews newspaper3k
# Note: gnews uses newspaper3k for get_full_article. Ensure it's installed.

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from gnews import GNews # Import the GNews client
import time # To add delays if needed

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
    Endpoint to fetch news using the GNews library and attempt to
    download the full article text using get_full_article.
    Example usage: http://localhost:5000/fetch-news?category=technology
    """
    category = request.args.get('category') # Get category from query param

    # --- Input Validation ---
    if not category:
        return jsonify({"error": "Missing 'category' query parameter"}), 400

    # Map the requested category to a GNews topic
    topic = CATEGORY_TO_TOPIC_MAP.get(category.lower())
    if not topic:
        print(f"Warning: Unknown category '{category}' requested. Falling back to 'NATION'.")
        topic = 'NATION'
        # Alternatively, return an error:
        # return jsonify({"error": f"Unsupported category: {category}"}), 400

    # --- Fetch from Google News via GNews ---
    print(f"Fetching news headlines for topic '{topic}' (mapped from category '{category}')...")
    try:
        # Initialize GNews client
        google_news = GNews(language='en', country='US', max_results=10) # Reduced results due to full article fetching time

        # Fetch news headlines by the mapped topic
        articles = google_news.get_news_by_topic(topic)

        if not articles:
             print(f"No articles found by GNews for topic '{topic}'.")
             return jsonify([]) # Return empty list

        print(f"Received {len(articles)} articles from GNews for topic '{topic}'. Attempting to fetch full text...")

        # Process articles into the format expected by the frontend
        processed_articles = []
        for article_summary in articles:
            # Basic check if essential headline data is present
            article_url = article_summary.get('url')
            article_title = article_summary.get('title')
            if not article_title or not article_url:
                print(f"Skipping article due to missing title or URL: {article_summary}")
                continue

            print(f"  Attempting to fetch full article for: {article_url}")
            full_article_text = None
            scraped_successfully = False
            start_time = time.time()

            try:
                # Attempt to download and parse the full article
                # This can be slow and might fail for various reasons (paywalls, JS rendering, blocks)
                article_object = google_news.get_full_article(article_url)

                if article_object and article_object.text:
                    # Check if the extracted text is substantial
                    if len(article_object.text) > 150: # Arbitrary length check
                         full_article_text = article_object.text
                         scraped_successfully = True
                         print(f"    Successfully fetched full text ({len(full_article_text)} chars).")
                    else:
                         print(f"    Fetched text too short, likely failed extraction or summary page.")
                else:
                    print(f"    get_full_article failed or returned empty text.")

            except Exception as e:
                # Catch errors during the download/parsing process
                print(f"    Error fetching/parsing full article {article_url}: {e}")
                # Keep full_article_text as None

            end_time = time.time()
            print(f"    Fetching/parsing took {end_time - start_time:.2f} seconds.")

            # Prepare source information
            source_name = article_summary.get('publisher', {}).get('title', 'Unknown Source')

            # Use description from the initial fetch as a fallback summary
            description = article_summary.get('description', 'No description available.')

            # Use the fetched full text if available, otherwise fallback to description
            text_for_revision = full_article_text if scraped_successfully else description

            processed_articles.append({
                "title": article_title,
                "description": description, # Keep the original description for summary display
                "content": None, # NewsAPI specific field
                "url": article_url,
                "urlToImage": None, # GNews doesn't provide this directly
                "source": {"name": source_name, "id": None},
                # Use the potentially scraped full text for revision
                "fullTextForRevision": text_for_revision,
                # Flag indicating if full text was likely obtained
                "scrapedTextAvailable": scraped_successfully
            })
            # Optional delay between articles to avoid overwhelming sites (might still get blocked)
            # time.sleep(0.5)

        print(f"Finished processing for topic '{topic}'. Returning {len(processed_articles)} articles.")
        return jsonify(processed_articles)

    except Exception as e:
        # Handle potential errors during GNews fetching or processing
        print(f"Error during GNews processing for topic '{topic}': {e}")
        error_message = "An error occurred while fetching or processing news via GNews."
        return jsonify({"error": error_message}), 500

# --- Run the Server ---
if __name__ == '__main__':
    print("Starting Flask server on http://localhost:5000")
    print("This version uses GNews and attempts get_full_article (experimental).")
    # Ensure newspaper3k is installed: pip install newspaper3k
    app.run(host='0.0.0.0', port=5000, debug=True)
