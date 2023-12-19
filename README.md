## How to autoblog using the ChatGPT Assistant's API

Firstly check out Income Stream Surfers on YouTube. There will be a few videos on how to use this script.

This is really powerful because we can use retrieval with some relevant files and upload them at the start of each thread, we can then use these files to create contextually relevant blog posts with very little effort, but with products and internal links already inside.

## Step 1 - Products

You need to firstly get a few things, if you're on Shopify you're in luck and this will work instantly, however other CMS may need some tweaking. Go to your sitemap yourwebsite.com/sitemap.xml on Shopify - and then go to your products and right click download it as .xml file. You then need to get Visual Studio Code, and put the .xml inside a new folder. Make sure you have Python and the latest version of OpenAI (pip install openai --upgrade). Then you need to use 2mentest.py in order to pick 200 random products from the sitemap. These should then be put into a .txt file. 

## Step 2 - Keywords

You'll need a csv file formatted like this, Topic Cluster,Topic,Type,Blog Post Ideas,Keywords,Word Count

You can put your niche into this into ChatGPT and ask for some stuff, give it some prompting, eventually it'll come out with something workable. You can even add your products to it to get better results. 

Once you've got that, make sure it's formatted in the same way, sometimes formatting can get weird, so just ask for it in markdown and the same formatting as the original document (2men_it_blog_content_plan_expanded (1).csv) this is an example

## Step 3 Internal links

My blogging strategy personally is geared towards pushing to our /collections/ on Shopify. Now I know that might not be true for everyone, so you can do this next part as you like. But you basically just need to clean some data, go to your collections sitemap on Shopify and either use [sitemaptoclipboard](https://chromewebstore.google.com/detail/sitemaptoclipboard/ilephboodpbklhnfckkkcilidgeclfhm?pli=1), or use Google Sheets to clean the data. This file should be called internallinks.txt and should be a list of your internal links.

## Step 4 - OpenAI 

Add your Secret Key from OpenAI, change the propmts if you want they are these parts of the script:

    instructions="Never use sources or footnotes Read internallinks.txt and products.txt - You always choose 5 strictly relevant product images and internal links for the articles. You do not use sources in the outline, you just pick 5 product images that are highly relevant to the article. First you read the attached files and understand them completely, then you create a detailed outline on the blog post topic, including a maximum of 5 HIGHLY relevant internal collection links and product image links. These will finally be used to write an article.",
    get_request = f"Choose 5 internal links and 5 product image urls that are relevant to {blog_post_idea}. For example for exotic leather shoes look for crocodile shoes etc. For suit articles look for suits.'."
    outline_request = f"use the product images and internal links from {get_internal_links} and use them to create an outline for an article about {blog_post_idea}' In the outline do not use sources or footnotes, but just add a relevant product image in a relevant section, and a relevant internal link in a relevant section. There is no need for a lot of sources, each article needs a maximum of 5 product images and internal links."
    article_request = f"Choose 5 internal links and 5 product images that are relevant to an article and then Write a detailed article based on the following outline:\n{outline}. Include the product images and internal links naturally and with relevance inside the article. Use markdown formatting and ensure to use tables and lists to add to formatting. Use 3 relevant product images and internal links maximum. Never invent any internal links."

You don't really have to change the prompts I don't think, but feel free to tinker with them to get some better output.

## Step 5 - The Content

You should see good results, around 700-1000 words, with product images, internal links, tables, lists, etc. You can use ChatGPT 3.5 in order to format them easily either using automation, or just simply while you're waiting for the script to run. If you run it all night you can probably achieve 500 articles in a night. I personally don't think that using automated uploading works that well and I think Google doesn't like it, so I'm not including any automations in the uploading of the articles in this particular autoblogger that I've made.



