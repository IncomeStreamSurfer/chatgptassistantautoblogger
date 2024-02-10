# MIT License

# Copyright (c) [2024] [Hamish Davison]

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "simplemode.py]"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.



import os
import openai
import time
import csv
import requests
from tqdm import tqdm
import concurrent.futures
import json

# Load configuration from a JSON file
with open('config.json') as config_file:
    config = json.load(config_file)

# Set your OpenAI API key from the config file
OPENAI_API_TOKEN = config["OPENAI_API_TOKEN"]
print("Setting OpenAI API Key...")
os.environ["OPENAI_API_KEY"] = OPENAI_API_TOKEN

# Update your Freeimage.host API Key here from the config file
FREEIMAGE_HOST_API_KEY = config["FREEIMAGE_HOST_API_KEY"]

# Initialize the OpenAI client
print("Initializing OpenAI client...")
client = openai.OpenAI()

# Global list to store image URLs
image_urls = []

def upload_to_freeimage_host(image_path, Keyword):
    """
    Uploads an image to Freeimage.host with {Keyword} in the filename.
    Also stores the image URL in a global list.
    """
    print(f"Uploading {image_path} to Freeimage.host...")
    with open(image_path, 'rb') as image_file:
        files = {'source': image_file}
        data = {
            'key': FREEIMAGE_HOST_API_KEY,
            'action': 'upload',
            'format': 'json',
            'name': f'{Keyword}_image.png'  # Add {Keyword} in the filename
        }
        
        response = requests.post('https://freeimage.host/api/1/upload', files=files, data=data)
        
        if response.status_code == 200:
            url = response.json().get('image', {}).get('url', '')
            if url:
                print(f"Uploaded successfully: {url}")
                image_urls.append({'idea': Keyword, 'url': url})  # Store both idea and URL
                return url
            else:
                print("Upload successful but no URL returned, something went wrong.")
        else:
            print(f"Failed to upload to Freeimage.host: {response.status_code}, {response.text}")
    return None

def upload_file(file_path, purpose):
    print(f"Uploading file: {file_path} for purpose: {purpose}")
    with open(file_path, "rb") as file:
        response = client.files.create(file=file, purpose=purpose)
    print(f"File uploaded successfully, ID: {response.id}")
    return response.id

def clear_image_urls():
    """
    Clears the global list of image URLs.
    """
    global image_urls
    image_urls.clear()
    print("Cleared global image URLs.")

print("Commencing file uploads...")
# Upload your files using paths from the config file
internal_links_file_id = upload_file(config["path_to_example_file"], 'assistants')
content_plan_file_id = upload_file(config["path_to_plan_csv"], 'assistants')
brand_plan_file_id = upload_file(config["path_to_example_file"], 'assistants')
images_file_id = upload_file(config["path_to_website_images"], 'assistants')

# Create an Assistant
print("Creating OpenAI Assistant...")
assistant = client.beta.assistants.create(
    name="Content Creation Assistant",
    model="gpt-4-turbo-preview",
    instructions=f"You are writing for {config['business_name']}. Choose product images and internal links from {config['path_to_website_images']} and {config['path_to_links_file']} and embed them with markdown in the final article. You must never EVER invent internal links or image links as this can destroy my SEO. YOU MUST INCLUDE INTERNAL LINKS FROM {config['path_to_links_file']} - read this first and make sure to include real internal links in the final article in the blog post When told to use retrieval use retrieval, when told to use code_interpreter use code interpreter. The final content should include internal links and embedded product images from {config['path_to_website_images']} and should include formatting. Your basic steps are: 1. read {config['path_to_website_images']}, get the image, create some visualizations of data, store these for the final article. 2. Find relevant brand images {config['path_to_website_images']}, create an outline, then write an article with all of this data you've either created or found Copy the tone from {config['path_to_example_file']} EXACTLY. Read {config['path_to_example_file']}. Use this as a guide to shape the final {config['page_type']}. The {config['page_type']} should follow the length and tone of {config['path_to_example_file']}. You are SEOGPT, aiming to create in-depth and interesting blog posts for {config['business_name']}, an {config['business_type']} in {config['country']}, you should write at a grade 7 level {config['language']} Every blog post should include at least 3 product images and links to their other pages from {config['business_name']}.. Ensure the brand image links are accurate. Choose only relevant brand pages. Do not invent image links. Pick 5 strictly relevant brand images and internal links for the articles. First, read the attached files, then create a detailed outline for a {config['page_type']}, including up to 5 highly relevant internal collection links and brand image links.",
    tools=[{"type": "retrieval"}, {"type": "code_interpreter"}],
    file_ids=[internal_links_file_id, content_plan_file_id, brand_plan_file_id, images_file_id]
)

print("Assistant created successfully.")

def wait_for_run_completion(thread_id, run_id, timeout=300):
    print(f"Waiting for run completion, thread ID: {thread_id}, run ID: {run_id}")
    start_time = time.time()
    while time.time() - start_time < timeout:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run_status.status == 'completed':
            print("Run completed successfully.")
            return run_status
        time.sleep(10)
    raise TimeoutError("Run did not complete within the specified timeout.")

def perplexity_research(Keyword, max_retries=3, delay=5):
    """
    Conducts perplexity research with retries on failure.
    Args:
        Keyword (str): The blog post idea to research.
        max_retries (int): Maximum number of retries.
        delay (int): Delay in seconds before retrying.
    Returns:
        dict or None: The response from the API or None if failed.
    """
    print(f"Starting perplexity research for: {Keyword}")
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "pplx-70b-online",
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise."
            },
            {
                "role": "user",
                "content": f"Find highly specific generalised data about {Keyword} in 2024. Do not give me any information about specific brands."
            }
        ]
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {config['PERPLEXITY_API_KEY']}"
    }

    for attempt in range(max_retries):
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print("Perplexity research completed successfully.")
            try:
                return response.json()
            except ValueError:
                print("JSON decoding failed")
                return None
        else:
            print(f"Perplexity research failed with status code: {response.status_code}. Attempt {attempt + 1} of {max_retries}.")
            time.sleep(delay)

    print("Perplexity research failed after maximum retries.")
    return None

def get_internal_links(thread_id, Keyword):
    print(f"Fetching internal links relevant to: {Keyword}")
    get_request = f"Use Retrieval. Read brandimagesandlinks.txt, Choose 5 relevant pages, their links and their respective images, that are relevant to {Keyword}. Don't have more than 5. Now read images.txt - choose 5 relevant product images to this article"
    client.beta.threads.messages.create(thread_id=thread_id, role="user", content=get_request)
    get_request_run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant.id)
    wait_for_run_completion(thread_id, get_request_run.id)
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    print("Internal links fetched successfully.")
    return next((m.content for m in messages.data if m.role == "assistant"), None)

def create_data_vis(thread_id, perplexity_research, Keyword):
    print("Creating data visualizations...")
    for _ in range(3):  # Loop to generate 3 visualizations
        get_request = f"Use Code Interpreter - invent a VERY simple Visualization of some interesting data from {perplexity_research}."
        client.beta.threads.messages.create(thread_id=thread_id, role="user", content=get_request)
        get_request_run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant.id)
        wait_for_run_completion(thread_id, get_request_run.id)

        messages = client.beta.threads.messages.list(thread_id=thread_id)

        if hasattr(messages.data[0].content[0], 'image_file'):
            file_id = messages.data[0].content[0].image_file.file_id

            image_data = client.files.content(file_id)
            image_data_bytes = image_data.read()

            image_path = f"./visualization_image_{_}.png"
            with open(image_path, "wb") as file:
                file.write(image_data_bytes)

            print(f"Visualization {_+1} created, attempting upload...")
            upload_to_freeimage_host(image_path, Keyword)
        else:
            print(f"No image file found in response for visualization {_+1}. Attempt aborted.")

def process_blog_post(thread_id, Keyword):
    print(f"Processing blog post for: {Keyword}")
    research_results = perplexity_research(Keyword)
    research_info = str(research_results)    

    create_data_vis(thread_id, research_info, Keyword)

    internal_links = get_internal_links(thread_id, Keyword)

    # Only include relevant image URLs for the current blog post idea
    relevant_image_urls = [img['url'] for img in image_urls if img['idea'] == Keyword]
    images_for_request = " ".join(relevant_image_urls)

    outline_request = f"Use retrieval. Look at brandimagesandlinks.txt. Create a SHORT outline for a {config['page_type']} based on {perplexity_research}. Also include data visualizations from {create_data_vis} Do not invent image links. use the product images and internal links from {internal_links} and the include the custom graphs from {images_for_request} and use them to create an outline for a {config['page_type']} about {Keyword}' In the outline do not use sources or footnotes, but just add a relevant product images in a relevant section, and a relevant internal link in a relevant section. There is no need for a lot of sources, each article needs a minimum of 5 brand images and internal links."

    client.beta.threads.messages.create(thread_id=thread_id, role="user", content=outline_request)
    outline_run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant.id)
    wait_for_run_completion(thread_id, outline_run.id)
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    outline = next((m.content for m in messages.data if m.role == "assistant"), None)

    article = None
    if outline:
        article_request = f"Please include images from {get_internal_links} Write a short, snappy article in {config['language']} Write at a grade 7 level. ONLY USE INTERNAL LINKS FROM {internal_links} You never invent internal links or image links. Include images from {create_data_vis} also include real internal links from brandimagesandlinks.txt Based on \n{outline} and Make sure to use a mix of the {images_for_request} and brand images. Include highly specific information from {research_results}. Do not use overly creative or crazy language. Use a {config['tone']} tone of voice. Write as if writing for The Guardian newspaper.. Just give information. Don't write like a magazine. Use simple language. Do not invent image links. You are writing from a first person plural perspective for the business, refer to it in the first person plural. Add a key takeaway table at the top of the article, summarzing the main points. Never invent links or brand images Choose 5 internal links and 5 brand images that are relevant to a pillar page and then create a pillar page with good formatting based on the following outline:\n{outline}, Title should be around 60 characters. Include the brand images and internal links to other pillar pages naturally and with relevance inside the {config['page_type']}. Use markdown formatting and ensure to use tables and lists to add to formatting. Use 3 relevant brand images and pillar pages with internal links maximum. Never invent any internal links.  Include all of the internal links and brand images from {outline} Use different formatting to enrich the pillar page. Always include a table at the very top wtih key takeaways, also include lists to make more engaging content. Use Based on the outline: {outline}, create an article. Use {images_for_request} with the image name inside [] and with the link from {images_for_request} in order to enrich the content, create a pillar page about this topic. Use the brand images and internal links gathered from {internal_links}. Use {research_info} to make the  more relevant. The end product shuold look like {config['path_to_example_file']} as an example"
        client.beta.threads.messages.create(thread_id=thread_id, role="user", content=article_request)
        article_run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant.id)
        wait_for_run_completion(thread_id, article_run.id)
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        article = next((m.content for m in messages.data if m.role == "assistant"), None)

    if article:
        print("Article created successfully.")
        clear_image_urls()  # Call the new function here to clear the image URLs
    else:
        print("Failed to create an article.")
    return outline, article

def process_keywords_concurrent():
    input_file = 'keywords.csv'
    output_file = 'processed_keywords.csv'

    # Corrected fieldnames array to include a missing comma and ensure it matches expected output
    fieldnames = ['Keyword', 'Outline', 'Article', 'Processed']

    # Read all rows to be processed
    with open(input_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows_to_process = [row for row in reader]

    # Process each blog post idea concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_row = {executor.submit(process_blog_post, client.beta.threads.create().id, row['Keyword']): row for row in rows_to_process}
        
        # Initialize tqdm progress bar
        progress = tqdm(concurrent.futures.as_completed(future_to_row), total=len(rows_to_process), desc="Processing Keywords")
        
        # Collect results first to avoid writing to the file inside the loop
        results = []
        for future in progress:
            row = future_to_row[future]
            try:
                outline, article = future.result()  # Assuming this returns an outline and an article
                # Create a new dictionary for CSV output to ensure it matches the specified fieldnames
                processed_row = {
                    'Keyword': row['Keyword'],
                    'Outline': outline,
                    'Article': article,
                    'Processed': 'Yes'
                }
                results.append(processed_row)
            except Exception as exc:
                print(f'Keyword {row["Keyword"]} generated an exception: {exc}')
                # Handle failed processing by marking as 'Failed' but still match the fieldnames
                processed_row = {
                    'Keyword': row['Keyword'],
                    'Outline': '',  # or you might use 'N/A' or similar placeholder
                    'Article': '',  # same as above
                    'Processed': 'Failed'
                }
                results.append(processed_row)

    # Write all results to the output file after processing
    with open(output_file, 'w', newline='', encoding='utf-8') as f_output:  # Use 'w' to overwrite or create anew
        writer = csv.DictWriter(f_output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

# Example usage
if __name__ == "__main__":
    process_keywords_concurrent()
