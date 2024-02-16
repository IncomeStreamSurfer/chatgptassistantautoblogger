import csv
import base64
import requests
import json
import os
from datetime import datetime, timedelta

# Load configuration from config.json
with open('config.json') as config_file:
    config = json.load(config_file)

wp_url = f"https://{config['wordpress_url']}/wp-json/wp/v2"
wp_post_url = wp_url + "/posts"
wp_media_url = wp_url + "/media"

credentials = config['user_id'] + ':' + config['user_app_password'].replace(" ", "")
token = base64.b64encode(credentials.encode())
header = {'Authorization': 'Basic ' + token.decode('utf-8')}

# Adjust the function to accept a date parameter
def post_post(article_title, article_body, post_status="draft", featured_media_id=0, post_date=None):
    post_data = {
        "title": article_title,
        "content": article_body,
        "status": post_status,
        "featured_media": featured_media_id,
        "comment_status": "closed",
        "categories": [1]
    }
    if post_date:
        post_data["date"] = post_date.isoformat()
    response = requests.post(wp_post_url, headers=header, json=post_data)
    return response

def post_file(file_path):
    filename = os.path.basename(file_path)
    mime_type = 'image/' + filename.split('.')[-1]  # Assumes extension is the MIME type
    headers = {'Authorization': header['Authorization'], 'Content-Disposition': f'attachment; filename={filename}', 'Content-Type': mime_type}
    data = open(file_path, "rb").read()
    response = requests.post(wp_media_url, headers=headers, data=data)
    return response

# Start the schedule one hour from now
schedule_time = datetime(2024, 2, 13, 9, 44)

# Read and process the CSV
with open('formatted_articles_with_titles.csv', mode='r', encoding='utf-8') as csvfile:
    csv_reader = csv.DictReader(csvfile)
    for row in csv_reader:
        image_path = row['Image_Path']
        featured_media_id = 0
        if image_path:
            image_response = post_file(image_path)
            if image_response.status_code == 201:
                featured_media_id = image_response.json().get('id')
                
        post_response = post_post(row['Title'], row['Formatted_Article'], 'future', featured_media_id, schedule_time)
        if post_response.status_code == 201:
            print(f"Post '{row['Title']}' scheduled successfully for {schedule_time.isoformat()} UTC.")
        else:
            print(f"Failed to schedule post '{row['Title']}'. Error: {post_response.text}")
        
        # Schedule the next post one hour later
        schedule_time += timedelta(hours=1)
