import streamlit as st
import pandas as pd
import concurrent.futures

# Import your existing functions and variables from your original script
from getdata import get_google_news_data, download_and_parse_article, generate_summary, generate_content

def main():
    st.set_page_config(page_title='Newsjacking Ideation', layout='wide')
    st.title('Newsjacking Ideation App')

    # Add custom CSS
    st.markdown("""
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f2f6;
        }
        h1 {
            color: #1d3557;
        }
    </style>
    """, unsafe_allow_html=True)

    # API key input fields
    openai_key = st.text_input("OpenAI API Key:", value="", type="password")
    serpapi_key = st.text_input("SerpAPI API Key:", value="", type="password")

    query = st.text_input("Search term:", "Anti-Trans")
    num_results = st.number_input("Number of results:", min_value=1, max_value=100, value=20, step=1)

    if st.button("Generate Content"):
        if openai_key and serpapi_key:
            with st.spinner("Generating content..."):
                articles = get_google_news_data(query, num_results, serpapi_key)

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    article_texts = list(executor.map(download_and_parse_article, [article['link'] for article in articles]))

                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    article_summaries = list(executor.map(lambda text: generate_summary(text, openai_key), article_texts))

                articles_df = pd.DataFrame(articles)
                articles_df['text'] = article_texts
                articles_df['summary'] = article_summaries

                content = generate_content(articles, article_summaries, openai_key)
                content_df = pd.DataFrame(content)

                st.write(content_df)

                csv = content_df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="content.csv">Download as CSV</a>'
                st.markdown(href, unsafe_allow_html=True)
        else:
            st.error("Please enter both OpenAI and SerpAPI API keys.")

if __name__ == "__main__":
    main()

