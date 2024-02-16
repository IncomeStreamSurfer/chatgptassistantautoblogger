import pandas as pd
import openai
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm.auto import tqdm
import json
from bs4 import BeautifulSoup

# Load configuration from a JSON file
with open('config.json') as config_file:
    config = json.load(config_file)

# Set your OpenAI API key from the config file
OPENAI_API_TOKEN = config["OPENAI_API_TOKEN"]
print("Setting OpenAI API Key...")
openai.api_key = config["OPENAI_API_TOKEN"]

# Define the formatting function with custom prompts and HTML title extraction
def format_article(text):
    if pd.isna(text) or text.strip() == "":
        return "", ""
    
    prompt = "Please format this article into HTML for better readability and structure, I will be posting to WordPress so do not include <html> <header> and <body tags> start at <h2>, do not include an <h1> tag without changing its core information. Ensure to embed any image links and always contain internal links."
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "system", "content": prompt},
                      {"role": "user", "content": text}],
            temperature=0.5,
            max_tokens=3000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
        formatted_text = response.choices[0].message['content'].strip()
        
        # Use BeautifulSoup to extract <h2> title
        soup = BeautifulSoup(formatted_text, 'html.parser')
        title = soup.h2.text if soup.h2 else ""  # Extracts text within the first <h2> tag, if it exists
        
        return formatted_text, title
    except Exception as e:
        print(f"Error during formatting: {e}")
        return "Formatting Error", ""

# Function to handle concurrent formatting of articles and title extraction
def format_articles_concurrently(df, column_name):
    formatted_articles = []
    titles = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_article = {executor.submit(format_article, article): article for article in df[column_name]}
        for future in tqdm(as_completed(future_to_article), total=len(df[column_name]), desc="Formatting Articles"):
            article_result = future_to_article[future]
            try:
                article_content, article_title = future.result()
                formatted_articles.append(article_content)
                titles.append(article_title)
            except Exception as exc:
                print(f'{article_result} generated an exception: {exc}')
                # Append the original article and a default/empty title in case of an error
                formatted_articles.append(article_result)
                titles.append("")
                
    return formatted_articles, titles

# Load your CSV file
print("Loading CSV file...")
df = pd.read_csv("processed_keywords_with_images.csv")  # Make sure this file contains 'Image_Path' among other columns

# Apply concurrent formatting to the "Article" column
print("Starting concurrent formatting of 'Article' column.")
formatted_articles, titles = format_articles_concurrently(df, "Article")
df["Formatted_Article"] = formatted_articles  # This line adds the formatted articles to the DataFrame
df["Title"] = titles  # This line adds the extracted titles to the DataFrame
print("Completed concurrent formatting of 'Article' column.")

# At this point, df still contains all its original columns, including 'Keyword', 'Outline', 'Processed', 'Image_Path', etc.
# The addition of 'Formatted_Article' and 'Title' does not remove or alter these original columns.

# Save the processed DataFrame to a new CSV file, preserving all original data along with the new additions
output_file = "formatted_articles_with_titles.csv"
df.to_csv(output_file, index=False)
print(f"Concurrent formatting complete. Output saved to {output_file}")

