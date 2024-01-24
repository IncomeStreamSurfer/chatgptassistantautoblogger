import os
import openai
import time
import csv
from tqdm import tqdm

# Set your OpenAI API key
OPENAI_API_TOKEN = "put_your_secret_key_here"
os.environ["OPENAI_API_KEY"] = OPENAI_API_TOKEN

# Initialize the OpenAI client
client = openai.OpenAI()

# Function to upload a file to OpenAI
def upload_file(file_path, purpose):
    with open(file_path, "rb") as file:
        response = client.files.create(file=file, purpose=purpose)
    return response.id

# Upload your files
internal_links_file_id = upload_file('internallinks.txt', 'assistants')
products_file_id = upload_file('products.txt', 'assistants')
content_plan_file_id = upload_file('2men_it_blog_content_plan_expanded (1).csv', 'assistants')

# Create an Assistant
assistant = client.beta.assistants.create(
    name="Content Creation Assistant",
    model="gpt-4-1106-preview",
    instructions="Read internallinks.txt and products.txt - You always choose 5 strictly relevant product images and internal links for the articles. You do not use sources in the outline, you just pick 5 product images that are highly relevant to the article. First you read the attached files and understand them completely, then you create a detailed outline on the blog post topic, including a maximum of 5 HIGHLY relevant internal collection links and product image links. These will finally be used to write an article.",
    tools=[{"type": "retrieval"}],
    file_ids=[internal_links_file_id, products_file_id, content_plan_file_id]
)


def wait_for_run_completion(thread_id, run_id, timeout=300):
    start_time = time.time()
    while time.time() - start_time < timeout:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run_status.status == 'completed':
            return run_status
        time.sleep(10)
    raise TimeoutError("Run did not complete within the specified timeout.")

def get_internal_links(thread_id, blog_post_idea):
    # Generate outline
    get_request = f"Choose 5 internal links and 5 product image urls that are relevant to {blog_post_idea}. For example for exotic leather shoes look for crocodile shoes etc. For suit articles look for suits.'."
    client.beta.threads.messages.create(thread_id=thread_id, role="user", content=get_request)
    get_request = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant.id)
    wait_for_run_completion(thread_id, get_request.id)
    # Retrieve outline from the thread
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    get_request = next((m.content for m in messages.data if m.role == "assistant"), None)

def process_blog_post(thread_id, blog_post_idea):
    # Generate outline
    outline_request = f"use the product images and internal links from {get_internal_links} and use them to create an outline for an article about {blog_post_idea}'."
    client.beta.threads.messages.create(thread_id=thread_id, role="user", content=outline_request)
    outline_run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant.id)
    wait_for_run_completion(thread_id, outline_run.id)
    # Retrieve outline from the thread
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    outline = next((m.content for m in messages.data if m.role == "assistant"), None)

    # Initialize article variable
    article = None

    # Generate article
    if outline:
        article_request = f"Write a detailed article based on the following outline:\n{outline} use markdown formatting and ensure to use tables and lists to add to formatting. Use 5 relevant product images and internal links maximum."
        client.beta.threads.messages.create(thread_id=thread_id, role="user", content=article_request)
        article_run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant.id)
        wait_for_run_completion(thread_id, article_run.id)
        # Retrieve article from the thread
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        article = next((m.content for m in messages.data if m.role == "assistant"), None)

    return outline, article


def process_content_plan():
    input_file = '2men_it_blog_content_plan_expanded (1).csv'
    output_file = 'processed_content_plan.csv'
    processed_rows = []

    # Create a single thread for processing the content plan
    thread_id = client.beta.threads.create().id

    with open(input_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in tqdm(reader, desc="Processing Blog Posts"):
            if row.get('Processed', 'No') == 'Yes':
                continue

            blog_post_idea = row['Blog Post Ideas']
            outline, article = process_blog_post(thread_id, blog_post_idea)

            if outline and article:
                row.update({'Blog Outline': outline, 'Article': article, 'Processed': 'Yes'})
                processed_rows.append(row)

    # Write the processed rows to the output file
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=processed_rows[0].keys())
        writer.writeheader()
        writer.writerows(processed_rows)

# Example usage
process_content_plan()
