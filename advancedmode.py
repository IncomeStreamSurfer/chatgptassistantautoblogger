import os
import openai
import time
import csv
import requests
from tqdm import tqdm
import time

# Set your OpenAI API key
OPENAI_API_TOKEN = "your_api_key"
print("Setting OpenAI API Key...")
os.environ["OPENAI_API_KEY"] = OPENAI_API_TOKEN

# Update your Freeimage.host API Key here
FREEIMAGE_HOST_API_KEY = "your_api_key"

# Initialize the OpenAI client
print("Initializing OpenAI client...")
client = openai.OpenAI()

# Global list to store image URLs
image_urls = []

def upload_to_freeimage_host(image_path, blog_post_idea):
    """
    Uploads an image to Freeimage.host with {blog_post_idea} in the filename.
    Also stores the image URL in a global list.
    """
    print(f"Uploading {image_path} to Freeimage.host...")
    with open(image_path, 'rb') as image_file:
        files = {'source': image_file}
        data = {
            'key': FREEIMAGE_HOST_API_KEY,
            'action': 'upload',
            'format': 'json',
            'name': f'{blog_post_idea}_image.png'  # Add {blog_post_idea} in the filename
        }
        
        response = requests.post('https://freeimage.host/api/1/upload', files=files, data=data)
        
        if response.status_code == 200:
            url = response.json().get('image', {}).get('url', '')
            if url:
                print(f"Uploaded successfully: {url}")
                image_urls.append({'idea': blog_post_idea, 'url': url})  # Store both idea and URL
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

# Add this new function
def clear_image_urls():
    """
    Clears the global list of image URLs.
    """
    global image_urls
    image_urls.clear()
    print("Cleared global image URLs.")

print("Commencing file uploads...")
# Upload your files
internal_links_file_id = upload_file('brandimagesandlinks.txt', 'assistants')
content_plan_file_id = upload_file('content_plan.csv', 'assistants')
brand_plan_file_id = upload_file('example.txt', 'assistants')
brand_logo_file_id = upload_file('brandlogo.txt', 'assistants')

# Create an Assistant
print("Creating OpenAI Assistant...")
assistant = client.beta.assistants.create(
    name="Content Creation Assistant",
    model="gpt-4-turbo-preview",
    instructions=f"You must never EVER invent internal links or image links as this can destroy my SEO. YOU MUST INCLUDE INTERNAL LINKS FROM brandimagesandlinks.txt - read this first and make sure to include real internal links in the final article in the pillar page When told to use retrieval use retrieval, when told to use code_interpreter use code interpreter. The final content should include internal links from brandimagesandlinks.txt and should include formatting. Your basic steps are: 1. read brandlogo.txt, get the image, create some visualizations of data, store these for the final article. 2. Find relevant brand images and internal links from brandimagesandlinks.txt, create an outline, then write an article with all of this data you've either created or found Copy the tone from example.txt EXACTLY. Read brandimagesandlinks.txt. Use this as a guide to shape the final pillar pages. The pillar pages should follow the length and tone of example.txt. You are PillarPageGPT, aiming to create in-depth and interesting service pages for tinyhomehub, a tiny home niche website. Every pillar page should include 3 brand images and links to their pillar pages. Ensure the brand image links are accurate. Choose only relevant brand pages. Do not invent image links. Pick 5 strictly relevant brand images and internal links for the articles. First, read the attached files, then create a detailed outline on the blog post topic, including up to 5 highly relevant internal collection links and brand image links.",
    tools=[{"type": "retrieval"}, {"type": "code_interpreter"}],
    file_ids=[internal_links_file_id, content_plan_file_id, brand_plan_file_id, brand_logo_file_id]
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

def perplexity_research(blog_post_idea, max_retries=3, delay=5):
    """
    Conducts perplexity research with retries on failure.
    Args:
        blog_post_idea (str): The blog post idea to research.
        max_retries (int): Maximum number of retries.
        delay (int): Delay in seconds before retrying.
    Returns:
        dict or None: The response from the API or None if failed.
    """
    print(f"Starting perplexity research for: {blog_post_idea}")
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
                "content": f"Find highly specific generalised data about {blog_post_idea} in 2024."
            }
        ]
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Bearer your_api_key"
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

def get_internal_links(thread_id, blog_post_idea):
    print(f"Fetching internal links relevant to: {blog_post_idea}")
    get_request = f"Use Retrieval. Read brandimagesandlinks.txt, Choose 5 relevant pages, their links and their respective images, that are relevant to {blog_post_idea}. Don't have more than 5."
    client.beta.threads.messages.create(thread_id=thread_id, role="user", content=get_request)
    get_request_run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant.id)
    wait_for_run_completion(thread_id, get_request_run.id)
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    print("Internal links fetched successfully.")
    return next((m.content for m in messages.data if m.role == "assistant"), None)

def create_data_vis(thread_id, perplexity_research, blog_post_idea):
    print("Creating data visualizations...")
    for _ in range(3):  # Loop to generate 3 visualizations
        get_request = f"Use Code Interpreter - invent a Visualization of some interesting data from {perplexity_research}."
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
            upload_to_freeimage_host(image_path, blog_post_idea)
        else:
            print(f"No image file found in response for visualization {_+1}. Attempt aborted.")

def process_blog_post(thread_id, blog_post_idea):
    print(f"Processing blog post for: {blog_post_idea}")
    research_results = perplexity_research(blog_post_idea)
    research_info = str(research_results)    

    create_data_vis(thread_id, research_info, blog_post_idea)

    internal_links = get_internal_links(thread_id, blog_post_idea)

    # Only include relevant image URLs for the current blog post idea
    relevant_image_urls = [img['url'] for img in image_urls if img['idea'] == blog_post_idea]
    images_for_request = " ".join(relevant_image_urls)

    outline_request = f"Use retrieval. Look at brandimagesandlinks.txt. Create a SHORT outline for a PILLAR PAGE based on {perplexity_research}. Not a blog post. Do not invent image links. use the brand images and internal links from {internal_links} and the include the custom graphs from {images_for_request} and use them to create an outline for an article about {blog_post_idea}' In the outline do not use sources or footnotes, but just add a relevant brand images in a relevant section, and a relevant internal link in a relevant section. There is no need for a lot of sources, each article needs a minimum of 5 brand images and internal links."

    client.beta.threads.messages.create(thread_id=thread_id, role="user", content=outline_request)
    outline_run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant.id)
    wait_for_run_completion(thread_id, outline_run.id)
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    outline = next((m.content for m in messages.data if m.role == "assistant"), None)

    article = None
    if outline:
        article_request = f"ONLY USE INTERNAL LINKS FROM {internal_links} You never invent internal links or image links. include real internal links from brandimagesandlinks.txt Based on \n{outline} and Make sure to use a mix of the {images_for_request} and brand images. Include highly specific information from {research_results} Use grade 7 level US English. Do not use overly creative or crazy language. Write as if writing for The Guardian newspaper.. Just give information. Don't write like a magazine. Use simple language. Do not invent image links. You are writing from a first person plural perspective for the business, refer to it in the first person plural. Add a key takeaway table at the top of the article, summarzing the main points. Never invent links or brand images Choose 5 internal links and 5 brand images that are relevant to a pillar page and then create a pillar page with good formatting based on the following outline:\n{outline}, Use consulting in the title as this is a consulting service subpage., Title should be around 60 characters. Include the brand images and internal links to other pillar pages naturally and with relevance inside the article. Use markdown formatting and ensure to use tables and lists to add to formatting. Use 3 relevant brand images and pillar pages with internal links maximum. Never invent any internal links.  Include all of the internal links and brand images from {outline} Use different formatting to enrich the pillar page. Always include a table at the very top wtih key takeaways, also include lists to make more engaging content. Use Based on the outline: {outline}, create an article. Use {images_for_request} with the image name inside [] and with the link from {images_for_request} in order to enrich the content, create a pillar page about this topic. Use the brand images and internal links gathered from {internal_links}. Use {research_info} to make the pilalr page more relevant. The end product shuold look like {brand_plan_file_id} as an example"
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

def process_content_plan():
    print("Starting content plan processing...")
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
                print(f"Processing row for topic: {blog_post_idea}, thread ID: {thread_id}")

                outline, article = process_blog_post(thread_id, blog_post_idea)

                if outline and article:
                    row.update({'Blog Outline': outline, 'Article': article, 'Processed': 'Yes'})
                    writer.writerow(row)
                    print("Finished processing article. Here's the final output:")
                    print(article)  # New print statement to output the finished article.
                else:
                    print(f"An issue occurred, unable to complete processing for the topic: {blog_post_idea}")

# Example usage
process_content_plan()
