from DrissionPage import ChromiumPage, ChromiumOptions
import os
import time
from datetime import datetime
import urllib.parse
from time import sleep
import json
import re
import traceback
from bs4 import BeautifulSoup
from db import insert_data

def get_browser():
    if os.name == 'nt':
        browser_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    else:
        browser_path = "/usr/bin/google-chrome-stable"

    op = ChromiumOptions().set_browser_path(browser_path)
    op.auto_port()
    page = ChromiumPage(op)
    return page

def get_current_epoch():
    current_epoch_ms = int(time.time() * 1000)
    print(f"Current epoch timestamp (milliseconds): {current_epoch_ms}")
    return current_epoch_ms

def structure_keyword_data(search_results):
    content_final_results = []
    auth_final_results = []
    for search_result in search_results:
        if search_result['type'] != 1:
            continue
        
        video_id = search_result['item']['video']['id']
        thumbnail_url = search_result["item"]['video']['cover']
        unique_id = search_result["item"]["author"]["id"]
        author_username = search_result['item']['author']['uniqueId']
        author_nickname = search_result['item']['author']['nickname']
        author_follower_count = search_result['item']["authorStats"]["followerCount"]
        author_like_count = search_result['item']["authorStats"]["heartCount"]
        video_url = "https://www.tiktok.com/@" + author_username + "/video/" + video_id
        video_caption = search_result['item']['desc']
        video_view_count = search_result["item"]["stats"]["playCount"]
        video_comment_count = search_result["item"]["stats"]["commentCount"]
        video_share_count = search_result["item"]["stats"]["shareCount"]
        video_like_count = search_result["item"]["stats"]["diggCount"]
        timestamp = search_result["item"]["createTime"]
        text_extra = search_result["item"]["textExtra"]
        
        hashtag = ""
        for hashtag_obj in text_extra:
            hashtag = hashtag + hashtag_obj["hashtagName"] + ","

        auth_final_results.append({
            "name": author_nickname,
            "title": author_nickname,
            "username": author_username,
            "unique_id": unique_id,
            "url" : f"https://www.tiktok.com/@{author_username}",
            "followers": author_follower_count,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })

        content_final_results.append({
            "author": author_username,
            "unique_id": unique_id,
            "url": video_url,
            "title": video_caption,
            "like_count": video_like_count,
            "comment_count": video_comment_count,
            "view_count": video_view_count,
            "share_count": video_share_count,
            "thumbnail_url": thumbnail_url,
            "timestamp": timestamp  
        })
    
    insert_data("chickenapi_author", auth_final_results)
    insert_data("chickenapi_content", content_final_results)

def scrape_keyword_videos(keyword):
    try:
        browser = get_browser()
        encoded_keyword = urllib.parse.quote(keyword)
        URL = f"https://www.tiktok.com/search?q={encoded_keyword}&t={get_current_epoch()}"
        print(f"Scraping URL: {URL}")
        browser.listen.start('search/general/full/')
        browser.get(URL)
        has_more = 1
        all_video_data = []
        while has_more:
            for request in browser.listen.steps():
                request_url = request.url
                print(f"Request URL: {request_url}")
                response_data = json.loads(request._raw_body)
               
                with open(f"sample_data/response.{get_current_epoch()}.json", "w", encoding="utf-8") as f:
                    json.dump(response_data, f, indent=4)
               
                has_more = response_data['has_more']
                scrolling_retry = 0
                scraping_ended = False
                while scrolling_retry < 3:
                    soup = BeautifulSoup(browser.html, 'html.parser')
                    if soup.body and "No more results".lower() in soup.body.get_text().lower():
                        has_more = 0
                        break
                    try:
                        processed_data = structure_keyword_data(response_data['data'])
                        all_video_data.extend(processed_data)
                        browser.run_js_loaded('document.querySelector(\'[data-e2e="search_top-item-list"]\').lastChild.scrollIntoView({ behavior: "smooth" })')
                        break
                    except:
                        print(traceback.format_exc())
                        browser.run_js_loaded('document.querySelector(\'[data-e2e="search_top-item-list"]\').firstChild.scrollIntoView({ behavior: "smooth" })')
                        time.sleep(2)
                        browser.run_js_loaded('document.querySelector(\'[data-e2e="search_top-item-list"]\').lastChild.scrollIntoView({ behavior: "smooth" })')
                        time.sleep(2)
                        scrolling_retry += 1
                        if scrolling_retry == 3:
                            scraping_ended = True
                            break
                if scraping_ended:
                    has_more = 0
                    break
                time.sleep(2)
            
        browser.listen.stop()
        browser.close()
        return all_video_data
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Exiting...")

if __name__ == "__main__":
    keyword_list = ["traveltok", "wanderlust"]
    for keyword in keyword_list:
        info = scrape_keyword_videos(keyword)
        print("Done----------------------------")
        print(info)
