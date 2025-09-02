from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time
import json
import os
import csv

# === CONFIG ===
EMAIL = "ENTER YOUR EMAIL"
PASSWORD = "ENTER YOUR PASSWORD"
COOKIE_FILE = "jobinja_cookies.json"
BASE_URL = "https://jobinja.ir/jobs/category/it-devops-server-jobs/%D8%A7%D8%B3%D8%AA%D8%AE%D8%AF%D8%A7%D9%85-%D8%A2%DB%8C-%D8%AA%DB%8C-%D8%AF%D9%88%D8%A7%D9%BE%D8%B3-%D8%B3%D8%B1%D9%88%D8%B1"
CSV_FILE = os.path.expanduser(f"~/Desktop/jobinja_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")  # Fixed path to actual file
MAX_PAGES = 40  # Total number of pages
BATCH_SIZE = 5  # Number of pages to crawl in each batch
START_PAGE = 33  # Page to start from

# === SETUP ===
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")

# Initialize driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# === COOKIE HANDLING ===
def load_cookies():
    if not os.path.exists(COOKIE_FILE) or os.path.getsize(COOKIE_FILE) == 0:
        return False
    try:
        driver.get("https://jobinja.ir")
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
            for cookie in cookies:
                cookie.pop("sameSite", None)
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"⚠️ Couldn't add cookie: {e}")
        driver.get("https://jobinja.ir/user")
        return True
    except json.JSONDecodeError:
        print("⚠️ Cookie file is corrupted, will create new one")
        return False

def save_cookies():
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        json.dump(driver.get_cookies(), f, ensure_ascii=False, indent=2)
    print("✅ Cookies saved.")

def login():
    print("🔐 Logging in manually...")
    driver.get("https://jobinja.ir/login/user")
    time.sleep(2)
    driver.find_element(By.ID, "identifier").send_keys(EMAIL)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, 'input[type="submit"].c-btn--primary').click()
    print("⚠️ If CAPTCHA appears, solve it in browser.")
    input("🔎 Press Enter after login and CAPTCHA are done...")
    save_cookies()

def is_logged_in():
    return "/user" in driver.current_url or "dashboard" in driver.current_url

# === CSV HANDLING ===
def save_to_csv(data):
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "title", "url", "category", "location", "cooperation_type", 
            "experience", "salary", "skills", "gender", "education"
        ])
        if not file_exists:
            writer.writeheader()
        writer.writerows(data)

# === SCRAPING FUNCTIONS ===
def scrape_job_page(job_url):
    driver.execute_script("window.open(arguments[0]);", job_url)
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(1.5)

    details = {
        "title": driver.title.split("|")[0].strip(),
        "url": job_url,
        "category": "",
        "location": "",
        "cooperation_type": "",
        "experience": "",
        "salary": "",
        "skills": "",
        "gender": "",
        "education": ""
    }

    try:
        info_items = driver.find_elements(By.CSS_SELECTOR, "li.c-infoBox__item")
        for item in info_items:
            try:
                label = item.find_element(By.CSS_SELECTOR, "h4.c-infoBox__itemTitle").text.strip()
                value_elements = item.find_elements(By.CSS_SELECTOR, "div.tags span.black")
                values = [el.text.strip() for el in value_elements]
            except:
                continue

            if "دسته‌بندی شغلی" in label:
                details["category"] = ", ".join(values)
            elif "موقعیت مکانی" in label:
                details["location"] = ", ".join(values)
            elif "نوع همکاری" in label:
                details["cooperation_type"] = ", ".join(values)
            elif "حداقل سابقه کار" in label:
                details["experience"] = ", ".join(values)
            elif "حقوق" in label:
                details["salary"] = ", ".join(values)
            elif "مهارت‌های مورد نیاز" in label:
                details["skills"] = ", ".join(values)
            elif "جنسیت" in label:
                details["gender"] = ", ".join(values)
            elif "حداقل مدرک تحصیلی" in label:
                details["education"] = ", ".join(values)
    except Exception as e:
        print(f"⚠️ Error scraping job details: {e}")

    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return details

# === MAIN SCRAPING LOGIC ===
def main():
    # Clear console (for better visibility)
    os.system('clear')
    
    # Login flow
    if not load_cookies():
        print("🔐 No valid cookies found, starting login...")
        login()
    else:
        print("✅ Cookies loaded successfully.")
        if not is_logged_in():
            print("🔁 Session expired, logging in again...")
            login()

    # Calculate batches
    total_batches = (MAX_PAGES - START_PAGE + 1) // BATCH_SIZE
    if (MAX_PAGES - START_PAGE + 1) % BATCH_SIZE != 0:
        total_batches += 1

    for batch in range(total_batches):
        start_page = START_PAGE + (batch * BATCH_SIZE)
        end_page = min(START_PAGE + ((batch + 1) * BATCH_SIZE) - 1, MAX_PAGES)  # Fixed missing parenthesis
        
        print(f"\n=== Processing batch {batch + 1}/{total_batches} (pages {start_page}-{end_page}) ===")
        batch_data = []

        for page in range(start_page, end_page + 1):
            print(f"\n📄 Visiting page {page}/{MAX_PAGES}...")
            try:
                page_url = f"{BASE_URL}?page={page}"
                driver.get(page_url)
                time.sleep(2)

                job_links = driver.find_elements(By.CSS_SELECTOR, "a.c-jobListView__titleLink")
                print(f"🔗 Found {len(job_links)} job links.")

                for i, link in enumerate(job_links, 1):
                    job_url = link.get_attribute("href")
                    print(f"  Processing job {i}/{len(job_links)}: {job_url}")
                    try:
                        job_details = scrape_job_page(job_url)
                        batch_data.append(job_details)
                    except Exception as e:
                        print(f"❌ Error scraping job: {e}")
                        continue

            except Exception as e:
                print(f"❌ Error processing page {page}: {e}")
                continue

        # Save batch results
        if batch_data:
            save_to_csv(batch_data)
            print(f"💾 Saved {len(batch_data)} jobs to CSV")
        else:
            print("⚠️ No jobs found in this batch")

    print(f"\n✅ Done! Check the results in {CSV_FILE}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Script interrupted by user!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()