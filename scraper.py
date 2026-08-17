import asyncio
from playwright.async_api import async_playwright
from db import is_table_exist, execute_query, insert_data
import re

# Number of threads/concurrency limit
CONCURRENT_LIMIT = 2

async def response_intercept(response):
    print(response.url)
    if "search/general/full" in response.url:
        print("\n\nrony----------------------")
        print(await response.json())

async def collect_post_details(context, keyword):
    all_info = []
    page = await context.new_page()
    page.on("response", response_intercept)
    await page.goto('https://www.tiktok.com/search/video')
    await page.wait_for_load_state('domcontentloaded')
    await page.type('input[type="search"]', keyword)
    await page.click('button[aria-label="Search"]')
    await page.wait_for_load_state('domcontentloaded')
    
    # Manual breakpoint for CAPTCHA handling if triggered
    input("Press Enter once CAPTCHA is solved...")
    
    for i in range(10):
        await page.mouse.wheel(0, 17000)
        await asyncio.sleep(2)

    video_elements = await page.locator('div[data-e2e="search_video-item-list"] > div').all()
    for element in video_elements:
        video_url = await element.locator('div[data-e2e="search_video-item"] a').get_attribute("href")
        caption = await element.locator('div[data-e2e="search-card-desc"] h1').inner_text()
        username = await element.locator('div[data-e2e="search-card-desc"] p[data-e2e="search-card-user-unique-id"]').inner_text()

        video_info = {
            "video_url": video_url,
            "video_caption": caption,
            "author_username": username
        }
        all_info.append(video_info)
        
    await page.close()
    return all_info

async def collect_auther_details(context, username, all_author_details, semaphore):
    async with semaphore:     
        page = await context.new_page()
        try:
            await page.goto(f"https://www.tiktok.com/@{username}", timeout=30000)        
            following_count = await page.locator('strong[data-e2e="following-count"]').inner_text()
            followers_count = await page.locator('strong[data-e2e="followers-count"]').inner_text()
            like_count = await page.locator('strong[data-e2e="likes-count"]').inner_text()

            author_info = {
                "username": username,
                "following_count": following_count,
                "follower_count": followers_count,
                "like_count": like_count
            }
            all_author_details.append(author_info)
        except Exception as e:
            print(f"Error fetching profile for {username}: {e}")
        finally:
            await page.close()

async def save_data(table_name, all_info=[]):
    is_exist = is_table_exist(table_name)
    if not is_exist:
        if table_name == "tiktok_post_details":
            sql_query = ''' CREATE TABLE tiktok_post_details (
                video_url VARCHAR, 
                video_caption VARCHAR,
                author_username VARCHAR
            )'''
            execute_query(sql_query)
        elif table_name == "author_info":
            sql_query = ''' CREATE TABLE author_info (
                username VARCHAR, 
                follower_count VARCHAR,
                following_count VARCHAR,
                like_count VARCHAR
            )'''
            execute_query(sql_query)
        elif table_name == "top_influencers_info":
            sql_query = ''' CREATE TABLE top_influencers_info (
                username VARCHAR, 
                follower_count VARCHAR,
                following_count VARCHAR,
                like_count VARCHAR
            )'''
            execute_query(sql_query)
    
    insert_data(table_name, all_info)            

def convert_to_number(value):
    if "k" in value.lower():
        value_from_string = re.findall(r'\d+', value)[-1]
        new_value = float(value_from_string) * 1000  # Fixed multiplier from 10000 to 1000
    elif "m" in value.lower():
        value_from_string = re.findall(r'\d+', value)[-1]
        new_value = float(value_from_string) * 1000000
    else:
        new_value = float(value)
    return new_value

async def scrape_tiktok(search_input = []):
    semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)   # Limit concurrency
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
        )
        for keyword in search_input:
            print(f"Processing keyword: {keyword}")
            videos_details = await collect_post_details(context=context, keyword=keyword)
            print(f"Collected {len(videos_details)} videos.")
            
            await save_data("tiktok_post_details", videos_details)
            all_author_details = []
            tasks = [collect_auther_details(context, video_detail["author_username"], all_author_details, semaphore) for video_detail in videos_details]
            await asyncio.gather(*tasks)
            
            if len(all_author_details) != 0:
                await save_data("author_info", all_author_details)

            top_influencers = []
            for author_info in all_author_details:
                follower = author_info["follower_count"]
                follower_number = convert_to_number(follower)
                like = author_info["like_count"]
                like_number = convert_to_number(like)

                if follower_number >= 1000000 and like_number >= 1000000:
                    top_influencers.append(author_info)

            print(f"Identified {len(top_influencers)} top influencers.")
            if len(top_influencers) != 0:
                await save_data("top_influencers_info", top_influencers)

async def main():
    hashtag_list = ["#traveltok", "#wanderlust"]
    await scrape_tiktok(hashtag_list)

if __name__ == '__main__':
    asyncio.run(main())
