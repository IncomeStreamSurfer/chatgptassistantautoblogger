import pandas as pd
import openai
from tqdm.auto import tqdm

# Initialize tqdm for pandas
tqdm.pandas()

# Your OpenAI API key
openai.api_key = 'your_api_key'

# Define the translation function with custom prompts
def translate(text, target_language, column_name):
    if pd.isna(text) or text.strip() == "":
        return ""

    prompts = {
        "post_title": f"Transcreate this meta title into {target_language} - You are writing for COMPANY_NAME_HERE - Do not translate Brand Names or Specific Names of products.",
        "post_content": f"Without translating directly, but transcreating, Write a simple, direct version of the content in {target_language}, at a grade 7 reading level. Do not translate Brand Names or Names or Products",
        "post_excerpt": f"Without translating directly, but transcreating, Write a simple, direct version of the content in {target_language}, at a grade 7 reading level. Do not translate Brand Names or Names or Products",
    }
    
    system_prompt = prompts.get(column_name, "Write anything such as do not translate this word or use this word instead of this word etc here.")
    
    print(f"Translating '{text[:50]}...' from column '{column_name}' to {target_language}.")  # Print before translation
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": text}],
            temperature=0.2,
            max_tokens=2000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
        translated_text = response.choices[0].message['content'].strip()
        print(f"API Response: {translated_text[:200]}")  # This prints the first 200 characters of the API response
        return translated_text
    except Exception as e:
        print(f"Error during translation of '{text[:50]}...' to {target_language}: {e}")
        return "Translation Error"

# Load your CSV file
print("Loading CSV file...")
df = pd.read_csv("WooCommerce-Products-Import-csv-sample-file.csv")

# Specify target languages
languages = ["German", "French", "Dutch"]

# Translate content
for col in df.columns:
    for lang in languages:
        print(f"Starting translation of column '{col}' to {lang}.")  # Print before starting column translation
        df[f"{col}_{lang}"] = df[col].progress_apply(lambda x: translate(x, lang, col))
        print(f"Completed translations for column '{col}' to {lang}.")  # Print after completing column translation

# Save the processed DataFrame to a new CSV file
output_file = "translated_content.csv"
df.to_csv(output_file, index=False)
print("Translation complete. Output saved to", output_file)
