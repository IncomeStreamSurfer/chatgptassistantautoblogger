import os
import openai
import time
import csv
import requests
from tqdm import tqdm

# Set your OpenAI API key
OPENAI_API_TOKEN = "YOUR_API_KEY"
os.environ["OPENAI_API_KEY"] = OPENAI_API_TOKEN

# Initialize the OpenAI client
client = openai.OpenAI()

# Function to upload a file to OpenAI
def upload_file(file_path, purpose):
    with open(file_path, "rb") as file:
        response = client.files.create(file=file, purpose=purpose)
    return response.id

# Upload your files
internal_links_file_id = upload_file('brandimagesandlinks.txt', 'assistants')
content_plan_file_id = upload_file('content_plan.csv', 'assistants')
brand_plan_file_id = upload_file('example.txt', 'assistants')

# Create an Assistant
assistant = client.beta.assistants.create(
    name="Content Creation Assistant",
    model="gpt-4-1106-preview",
    instructions="Copy the tone from example.txt EXACTLY. Read brandimagesandlinks.txt. Use this as a guide to shape the final pillar pages. The pillar pages should follow the length and tone of example.txt. You are PillarPageGPT, aiming to create in-depth and interesting service pages for YOUR_BUSINESS_NAME, a SERVICE NICHE. Every pillar page should include 3 brand images and links to their pillar pages. Ensure the brand image links are accurate. Choose only relevant brand pages. Do not invent image links. Pick 5 strictly relevant brand images and internal links for the articles. First, read the attached files, then create a detailed outline on the blog post topic, including up to 5 highly relevant internal collection links and brand image links.",
    tools=[{"type": "retrieval"}],
    file_ids=[internal_links_file_id, content_plan_file_id, brand_plan_file_id]
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
    get_request = f"Read brandimagesandlinks.txt, Choose 5 relevant pages, their links and their respective images, that are relevant to {blog_post_idea}. Don't have more than 5."
    client.beta.threads.messages.create(thread_id=thread_id, role="user", content=get_request)
    get_request_run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant.id)
    wait_for_run_completion(thread_id, get_request_run.id)
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    return next((m.content for m in messages.data if m.role == "assistant"), None)

# Function to make a request to Perplexity AI
def perplexity_research(blog_post_idea):
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
                "content": f"{blog_post_idea}"
            }
        ]
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Bearer YOUR_BEARER_TOKEN"
    }

    response = requests.post(url, json=payload, headers=headers)
    print(response.text)
    return response.json()


def process_blog_post(thread_id, blog_post_idea):
    research_results = perplexity_research(blog_post_idea)
    research_info = str(research_results)

    outline_request = f"Based on the following research: {research_info}, create a SHORT outline for a PILLAR PAGE about {blog_post_idea}. Use the brand images and internal links from {get_internal_links(thread_id, blog_post_idea)} and create an outline for an article. Each article needs a minimum of 5 brand images and internal links."

    client.beta.threads.messages.create(thread_id=thread_id, role="user", content=outline_request)
    outline_run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant.id)
    wait_for_run_completion(thread_id, outline_run.id)
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    outline = next((m.content for m in messages.data if m.role == "assistant"), None)

    article = None
    if outline:
        article_request = f"Use grade 7 level US English. Use {research_results} Write as if writing for The Guardian newspaper. Just give information. Don't write like a magazine. Use simple language. Do not invent image links. You are writing from a first person plural perspective for the business, refer to it in the first person plural. Add a key takeaway table at the top of the article, summarizing the main points. Never invent links or brand images. Choose 5 internal links and 5 brand images that are relevant to a pillar page and then create a pillar page with good formatting based on the following outline:\n{outline}, Use consulting in the title as this is a consulting service subpage., Title should be around 60 characters. Include the brand images and internal links to other pillar pages naturally and with relevance inside the article. Use markdown formatting and ensure to use tables and lists to add to formatting. Use 3 relevant brand images and pillar pages with internal links maximum. Never invent any internal links."
        client.beta.threads.messages.create(thread_id=thread_id, role="user", content=article_request)
        article_run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant.id)
        wait_for_run_completion(thread_id, article_run.id)
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        article = next((m.content for m in messages.data if m.role == "assistant"), None)

    return outline, article

def process_content_plan():
    input_file = 'content_plan.csv'
    output_file = 'processed_content_plan.csv'

    fieldnames = ['Topic Cluster', 'Topic', 'Type', 'Blog Post Ideas', 'Keywords', 'Word Count', 'Blog Outline', 'Article', 'Processed']

    with open(output_file, 'a', newline='', encoding='utf-8') as f_output:
        writer = csv.DictWriter(f_output, fieldnames=fieldnames)
        if f_output.tell() == 0:
            writer.writeheader()

        with open(input_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in tqdm(reader, desc="Processing Blog Posts"):
                if row.get('Processed', 'No') == 'Yes':
                    continue

                blog_post_idea = row['Blog Post Ideas']
                thread_id = client.beta.threads.create().id
                outline, article = process_blog_post(thread_id, blog_post_idea)

                if outline and article:
                    row.update({'Blog Outline': outline, 'Article': article, 'Processed': 'Yes'})
                    writer.writerow(row)

# Example usage
process_content_plan()
