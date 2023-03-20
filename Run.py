import streamlit as st
import pandas as pd
import concurrent.futures
import openai
import pandas as pd
import numpy as np
import requests
import json
import os
from serpapi import GoogleSearch
from newspaper import Article
import nltk
import concurrent.futures

nltk.download('punkt')

serpapi_key = 'enter your serpapi key'
openai_key = 'enter your openai key'



def download_and_parse_article(url):
    article = Article(url)
    article.download()
    article.parse()
    return article.text




def get_google_news_data(query, num_results=10, api_key=None):
    params = {
        "api_key": api_key if api_key else serpapi_key,
        "engine": "google",
        "q": query,
        "tbm": "nws",
        "num": num_results
    }
    response = requests.get('https://serpapi.com/search.json', params=params)
    data = json.loads(response.text)
    articles = []
    for result in data['news_results']:
        articles.append({
            'title': result['title'],
            'link': result['link'],
            'date': result['date'],
            'source': result['source']
        })
    return articles

def scrape_article_text(url):
    article = Article(url)
    article.download()
    article.parse()
    return article.text

def generate_summary(text, api_key=None):
    prompt = f"Please provide a short summary of the salient points for newsjacking ideation for this article: {text}"
    response = openai.ChatCompletion.create(
        model="gpt-4-0314",
        messages=[
            {"role": "system", "content": "You are an expert at summarizing articles for newsjacking ideation."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=500,
        n=1,
        stop=None,
        temperature=0.5,
        api_key=api_key if api_key else openai_key
    )
    summary = response['choices'][0]['message']['content']
    return summary.strip()

def generate_content(articles, summaries, api_key=None):
    content = []
    for i, summary in enumerate(summaries):
        prompt = f"Based on the summary of article '{articles[i]['title']}', please provide a story title, description, and dataset sources for newsjacking ideation."
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert at generating newsjacking ideas based on article summaries."},
                {"role": "user", "content": f"{prompt}: {summary}"},
            ],
            max_tokens=2000,
            n=1,
            stop=None,
            temperature=0.5,
            api_key=api_key if api_key else openai_key
        )
        generated_content = response['choices'][0]['message']['content'].strip()
        content.append({
            'article_title': articles[i]['title'],
            'input_summary': summary,
            'generated_content': generated_content
        })
    return content
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

