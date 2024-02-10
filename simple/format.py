import pandas as pd
import openai
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm.auto import tqdm
import json


# Load configuration from a JSON file
with open('config.json') as config_file:
    config = json.load(config_file)

# Set your OpenAI API key from the config file
OPENAI_API_TOKEN = config["OPENAI_API_TOKEN"]
print("Setting OpenAI API Key...")
openai.api_key = config["OPENAI_API_TOKEN"]

# Define the formatting function with custom prompts
def format_article(text):
    if pd.isna(text) or text.strip() == "":
        return ""
    
    # Define the custom prompt for formatting the Article. Adjust as necessary.
    prompt = "Please format this article for better readability and structure, without changing its core information. Ensure to embed any image links and always contain internal links."
    
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
        return formatted_text
    except Exception as e:
        print(f"Error during formatting: {e}")
        return "Formatting Error"

# Function to handle concurrent formatting of articles
def format_articles_concurrently(df, column_name):
    formatted_articles = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust max_workers as needed based on your system and API rate limits
        future_to_article = {executor.submit(format_article, article): article for article in df[column_name]}
        for future in tqdm(as_completed(future_to_article), total=len(df[column_name]), desc="Formatting Articles"):
            article_result = future_to_article[future]
            try:
                formatted_articles.append(future.result())
            except Exception as exc:
                print(f'{article_result} generated an exception: {exc}')
                formatted_articles.append(article_result)  # Append the original article in case of an error
                
    return formatted_articles

# Load your CSV file
print("Loading CSV file...")
df = pd.read_csv("processed_keywords.csv")  # Replace 'your_csv_file.csv' with the actual file path

# Apply concurrent formatting to the "Article" column
print("Starting concurrent formatting of 'Article' column.")
formatted_articles = format_articles_concurrently(df, "Article")
df["Article"] = formatted_articles
print("Completed concurrent formatting of 'Article' column.")

# Save the processed DataFrame to a new CSV file
output_file = "formatted_articles_concurrently.csv"
df.to_csv(output_file, index=False)
print("Concurrent formatting complete. Output saved to", output_file)
