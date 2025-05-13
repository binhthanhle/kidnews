# streamlit_news_viewer.py
# Requires installation: pip install streamlit gnews newspaper3k

import streamlit as st
from gnews import GNews
import time

# --- Configuration ---
# Map frontend categories to GNews topics
CATEGORY_TO_TOPIC_MAP = {
    'Business': 'BUSINESS',
    'Entertainment': 'ENTERTAINMENT',
    'General': 'NATION',  # Or 'WORLD'
    'Health': 'HEALTH',
    'Science': 'SCIENCE',
    'Sports': 'SPORTS',
    'Technology': 'TECHNOLOGY',
}
NEWS_CATEGORIES_DISPLAY = list(CATEGORY_TO_TOPIC_MAP.keys())

# --- Helper Functions (from previous server, adapted for Streamlit) ---
def fetch_news_from_gnews(category_display_name):
    """
    Fetches news headlines using GNews and attempts to get full article text.
    """
    topic = CATEGORY_TO_TOPIC_MAP.get(category_display_name)
    if not topic:
        st.error(f"Invalid category mapped: {category_display_name}")
        return []

    processed_articles = []
    try:
        with st.spinner(f"📰 Fetching headlines for '{category_display_name}'... This might take a moment for full text attempts."):
            gnews_client = GNews(language='en', country='US', max_results=7) # Keep max_results low for performance
            headlines = gnews_client.get_news_by_topic(topic)

            if not headlines:
                st.info(f"🤔 No articles found by GNews for topic '{topic}'.")
                return []

            st.write(f"Found {len(headlines)} headlines. Attempting to fetch full articles...")

            for i, headline in enumerate(headlines):
                article_url = headline.get('url')
                article_title = headline.get('title')

                if not article_title or not article_url:
                    print(f"Skipping article due to missing title or URL: {headline}")
                    continue

                full_article_text = None
                scraped_successfully = False
                progress_bar = st.progress(0, text=f"Processing article {i+1}/{len(headlines)}: {article_title[:50]}...")

                try:
                    # This is the part that can be slow and unreliable
                    article_object = gnews_client.get_full_article(article_url)
                    if article_object and article_object.text:
                        if len(article_object.text) > 150: # Basic check for substantial text
                            full_article_text = article_object.text
                            scraped_successfully = True
                            print(f"Successfully fetched full text for: {article_url}")
                        else:
                            print(f"Fetched text too short for: {article_url}")
                    else:
                        print(f"get_full_article failed or returned empty for: {article_url}")
                except Exception as e:
                    print(f"Error fetching/parsing full article {article_url}: {e}")

                processed_articles.append({
                    "title": article_title,
                    "description": headline.get('description', 'No description available.'),
                    "url": article_url,
                    "sourceName": headline.get('publisher', {}).get('title', 'Unknown Source'),
                    "fullTextForDisplay": full_article_text if scraped_successfully else headline.get('description', 'Full text not available, showing description.'),
                    "wasFullTextScraped": scraped_successfully
                })
                progress_bar.progress((i + 1) / len(headlines), text=f"Processed article {i+1}/{len(headlines)}")
                time.sleep(0.1) # Small delay to allow UI to update and be polite

            progress_bar.empty() # Clear progress bar when done
        st.success(f"✅ Finished processing {len(processed_articles)} articles for '{category_display_name}'.")
        return processed_articles

    except Exception as e:
        st.error(f"🚨 An error occurred: {e}")
        print(f"Error during GNews processing for topic '{topic}': {e}")
        return []

# --- Streamlit App UI ---
st.set_page_config(layout="wide", page_title="Kids News Viewer", page_icon="📰")

st.title("📰 Kids News Viewer (via GNews)")
st.markdown("Select a category to fetch news. The app will attempt to retrieve the full article text, which can be slow and may not always succeed.")
st.markdown("---")

# --- Sidebar for Controls ---
with st.sidebar:
    st.header("⚙️ Controls")
    selected_category = st.selectbox(
        "🗂️ Choose a News Category:",
        options=NEWS_CATEGORIES_DISPLAY,
        index=0 # Default to the first category
    )

    if st.button("🚀 Fetch News", type="primary", use_container_width=True):
        if selected_category:
            # Store fetched articles in session state to persist them
            st.session_state.articles = fetch_news_from_gnews(selected_category)
            st.session_state.current_category = selected_category # Store category for display
        else:
            st.warning("Please select a category first.")

    st.markdown("---")
    if st.button("ℹ️ Show Host Info", use_container_width=True):
        st.info("""
        This Streamlit app is running locally on your computer.
        You can typically access it via:
        - **Host:** `localhost`
        - **Port:** `8501` (default Streamlit port)
        So, the URL is usually: `http://localhost:8501`
        """)

# --- Main Area for Displaying News ---
st.header("🗞️ Fetched News Articles")

if 'articles' in st.session_state and st.session_state.articles:
    st.subheader(f"Showing articles for: {st.session_state.current_category}")
    for i, article in enumerate(st.session_state.articles):
        with st.expander(f"{i+1}. {article['title']}", expanded=(i==0)): # Expand the first article by default
            st.markdown(f"**Source:** {article['sourceName']}")
            st.markdown(f"**Original URL:** [Read more]({article['url']})", unsafe_allow_html=True)

            if article['wasFullTextScraped']:
                st.markdown("📝 **Attempted Full Article Text:**")
                st.markdown(f"<div style='background-color:#f0f9ff; border-left: 4px solid #3b82f6; padding: 10px; border-radius: 4px; max-height: 400px; overflow-y: auto;'>{article['fullTextForDisplay'].replace_new_lines}</div>", unsafe_allow_html=True)
            else:
                st.markdown("📄 **Description (Full text unavailable):**")
                st.markdown(f"<div style='background-color:#fffbeb; border-left: 4px solid #f59e0b; padding: 10px; border-radius: 4px;'>{article['fullTextForDisplay']}</div>", unsafe_allow_html=True)
            st.markdown("---")
elif 'articles' in st.session_state and not st.session_state.articles: # Explicitly check for empty list after fetch attempt
    st.info(f"No articles were found or processed for the selected category: {st.session_state.get('current_category', '')}")
else:
    st.info("Select a category and click 'Fetch News' to see articles here.")

st.markdown("---")
st.caption("Streamlit News Viewer App - Full article text retrieval is experimental.")
