import os
import time
import re
import enum
import urllib.request

import backoff
import selenium.common.exceptions

from tqdm import tqdm

USERNAME = ''
PASSWORD = ''
CHAT_ID = 1


class AttachmentType(str, enum.Enum):
    PHOTOS = 'photos'
    VIDEOS = 'videos'


ATTACHMENT_TYPE = AttachmentType.PHOTOS


@backoff.on_exception(backoff.expo, selenium.common.exceptions.NoSuchElementException, max_tries=5)
def download_photo(url, photos_path):
    driver.get(url)

    menu = driver.find_element(By.CSS_SELECTOR, value='#photo_context > button')
    menu.click()

    item = driver.find_element(By.CSS_SELECTOR, value='a.mva_item[target="_blank"]')
    download_url = item.get_attribute('href')
    matches = next(iter(re.findall(r'([\d\w\-]*)\.jpg\?size=(\d*x\d*)', download_url)), None)
    if len(matches):
        code, size = matches
        urllib.request.urlretrieve(download_url, os.path.join(photos_path, f'{code}.jpg'))


def download_photos():
    item_urls = [item.get_attribute('href')
                 for item in driver.find_elements(By.CSS_SELECTOR, '.photos_page > a.al_photo')]
    print('Total items: ', len(item_urls))
    for url in tqdm(item_urls):
        # print('Downloading url=%s...', url)
        download_photo(url, photos_path=download_path)


def get_video_data(source):
    code, size = next(iter(re.findall(r'([\d\w]*)\.(\d*)\.mp4', source)), None)
    return code, size, source


def download_video(url, videos_path):
    driver.get(url)

    sources = [item.get_attribute('src')
               for item in driver.find_elements(By.CSS_SELECTOR, value='video > source[type="video/mp4"]')]
    matches = [get_video_data(source) for source in sources]
    matches = sorted([match for match in matches if match], key=lambda values: values[1], reverse=True)

    print(matches)
    if len(matches):
        code, size, url = matches[0]
        urllib.request.urlretrieve(url, os.path.join(videos_path, f'{code}.{size}.mp4'))


def scroll_to_end():
    print('Scroll to end...')
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        time.sleep(1)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def download_videos():
    item_urls = [item.get_attribute('href') for item in driver.find_elements(By.CSS_SELECTOR, '.video_item > a')]
    print('Total items: ', len(item_urls))
    for url in item_urls:
        print('Downloading url=%s...', url)
        download_video(url, videos_path=download_path)


if __name__ == '__main__':
    download_path = os.path.join('data/', str(CHAT_ID), ATTACHMENT_TYPE.value)
    os.makedirs(download_path, exist_ok=True)

    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys

    options = webdriver.ChromeOptions()
    options.add_argument('--disable-browser-side-navigation')

    mobile_emulation = {'deviceName': 'iPad Pro'}

    options.add_experimental_option('mobileEmulation', mobile_emulation)

    driver = webdriver.Chrome(options=options)

    driver.implicitly_wait(3)

    driver.get('https://vk.com')

    email = driver.find_element(by=By.NAME, value='email')
    email.click()
    email.clear()
    email.send_keys(USERNAME)

    password = driver.find_element(by=By.NAME, value='pass')
    password.click()
    password.clear()
    password.send_keys(PASSWORD)

    password.send_keys(Keys.RETURN)

    # login = browser.find_element(by=By.CSS_SELECTOR, value='input[type="submit"][value="Sign in"]')
    # login.click()

    from urllib.parse import urljoin

    driver.get(urljoin(driver.current_url, f'/mail?act=show_medias&peer={CHAT_ID}&section={ATTACHMENT_TYPE}'))

    scroll_to_end()

    if ATTACHMENT_TYPE == AttachmentType.PHOTOS:
        download_photos()
    elif ATTACHMENT_TYPE == ATTACHMENT_TYPE.VIDEOS:
        download_videos()

    input('Press Enter any key to exit...')

    driver.close()
