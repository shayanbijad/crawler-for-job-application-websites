from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import csv

# === CONFIG ===
EMAIL = "ENTER YOUR EMAIL"
PASSWORD = "ENTER YOUR PASSWORD"
BASE_URL = "https://jobvision.ir/jobs/category/network"
LOGIN_URL = "https://account.jobvision.ir/Candidate?returnUrl=%2Fconnect%2Fauthorize%2Fcallback%3Fclient_id%3DJobVisionAngularClient%26redirect_uri%3Dhttps%253A%252F%252Fjobvision.ir%252Fauth-callback%26response_type%3Did_token%2520token%26scope%3Dopenid%2520profile%2520JobVisionApi%2520roles%2520offline_access%2520IdentityServerApi%26nonce%3D7eaede2148c9b68d2bcec0000fbabbd5c2gvF6VaG%26state%3D8ba661bf1996a88b033f6201f8d4b26271yAomDaj%26role"
CSV_FILE = os.path.expanduser(f"~/Desktop/jobvision_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
MAX_PAGES = 44  # Total number of pages
BATCH_SIZE = 2  # Number of pages to crawl in each batch
START_PAGE = 14  # Page to start from

# === SETUP ===
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--disable-third-party-cookies")  # Ensure cookies are not blocked

# Initialize driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# === LOGIN ===
def login():
    print("🔐 Logging in manually...")
    driver.get(LOGIN_URL)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(1)
    
    # Step 1: Enter username
    username_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "Username"))
    )
    username_field.send_keys(EMAIL)
    
    # Step 2: Click "ادامه" button
    try:
        continue_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'ادامه')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", continue_button)
        time.sleep(0.5)
        continue_button.click()
    except Exception as e:
        print(f"⚠️ Standard click failed for 'ادامه': {e}")
        print("Attempting JavaScript click...")
        try:
            continue_button = driver.find_element(By.XPATH, "//a[contains(text(), 'ادامه')]")
            driver.execute_script("arguments[0].click();", continue_button)
        except Exception as e:
            print(f"❌ JavaScript click failed: {e}")
            with open("continue_button_error.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            raise
    
    print("⚠️ First CAPTCHA appeared. Solve it in the browser.")
    input("🔎 Press Enter after solving the first CAPTCHA...")
    
    # Step 3: Enter password
    password_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "Password"))
    )
    password_field.send_keys(PASSWORD)
    
    # Step 4: Click "ورود" button
    try:
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'ورود')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
        time.sleep(0.5)
        login_button.click()
    except Exception as e:
        print(f"⚠️ Standard click failed for 'ورود': {e}")
        print("Attempting JavaScript click...")
        try:
            login_button = driver.find_element(By.XPATH, "//a[contains(text(), 'ورود')]")
            driver.execute_script("arguments[0].click();", login_button)
        except Exception as e:
            print(f"❌ JavaScript click failed: {e}")
            with open("login_button_error.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            raise
    
    print("⚠️ Second CAPTCHA appeared. Solve it in the browser.")
    input("🔎 Press Enter after solving the second CAPTCHA and login is complete...")

# === CSV HANDLING ===
def save_to_csv(data):
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "title", "company", "location", "salary", "features", "posted", "urgent_tag",
            "cooperation_type", "work_days_hours", "industry", "experience", "skills", "gender"
        ])
        if not file_exists:
            writer.writeheader()
        writer.writerows(data)

# === SCRAPING FUNCTIONS ===
def scroll_to_load_jobs():
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)  # Reduced from 2 seconds
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def scrape_job_page(job_url):
    driver.get(job_url)  # Navigate without waiting for full load
    
    # Save page source for debugging
    debug_file = f"job_page_source_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(debug_file, "w", encoding="utf-8") as f:
        f.write(driver.page_source)

    details = {
        "cooperation_type": "",
        "work_days_hours": "",
        "industry": "",
        "experience": "",
        "skills": "",
        "gender": ""
    }

    try:
        # Cooperation Type
        try:
            cooperation = driver.find_element(By.CSS_SELECTOR, "div.font-size-6.ml-3.text-muted")
            details["cooperation_type"] = cooperation.text.strip()
        except:
            print("⚠️ Cooperation type not found")

        # Work Days/Hours
        try:
            work_hours = driver.find_element(By.XPATH, "//div[@class='col-4']//label[contains(text(), 'روز و ساعت کاری')]/following-sibling::div")
            details["work_days_hours"] = work_hours.text.strip()
        except:
            print("⚠️ Work days/hours not found")

        # Industry
        try:
            industry = driver.find_element(By.CSS_SELECTOR, "div.text-muted:not(.font-size-6):not(.yn_category)")
            details["industry"] = industry.text.strip()
        except:
            print("⚠️ Industry not found")

        # Experience
        try:
            experience = driver.find_element(By.CSS_SELECTOR, "span.word-break")
            details["experience"] = experience.text.strip()
        except:
            print("⚠️ Experience not found")

        # Skills
        try:
            skills = []
            skill_elements = driver.find_elements(By.CSS_SELECTOR, "div.row.col-11.px-0 span.d-flex.bg-white.text-black.border.border-secondary")
            skills.extend([skill.text.strip() for skill in skill_elements])
            app_tag_elements = driver.find_elements(By.CSS_SELECTOR, "app-tag span.tag")
            for tag in app_tag_elements:
                try:
                    title = tag.find_element(By.CSS_SELECTOR, "span.tag-title").text.strip()
                    value = tag.find_element(By.CSS_SELECTOR, "span.tag-value").text.strip()
                    skills.append(f"{title} - {value}")
                except:
                    continue
            details["skills"] = ", ".join(skills)
        except:
            print("⚠️ Skills not found")

        # Gender
        try:
            gender = driver.find_element(By.XPATH, "//div[contains(@class, 'requirement-title') and contains(text(), 'جنسیت')]/following-sibling::div[contains(@class, 'requirement-value')]")
            details["gender"] = gender.text.strip()
        except:
            print("⚠️ Gender not found")

    except Exception as e:
        print(f"❌ Error scraping job page: {e}")

    driver.back()  # Return to listing page
    return details

def scrape_job_card(card):
    details = {
        "title": "",
        "company": "",
        "location": "",
        "salary": "",
        "features": "",
        "posted": "",
        "urgent_tag": ""
    }

    try:
        # Title
        try:
            title = card.find_element(By.CSS_SELECTOR, "div.job-card-title.w-100.font-weight-bolder.text-black.px-0.pl-4.line-height-24")
            details["title"] = title.text.strip()
        except:
            print("⚠️ Title not found")

        # Company
        try:
            company = card.find_element(By.CSS_SELECTOR, "a.text-black.line-height-24.pointer-events-none")
            details["company"] = company.text.strip()
        except:
            print("⚠️ Company not found")

        # Location
        try:
            location = card.find_element(By.CSS_SELECTOR, "span.text-secondary.pointer-events-none.ng-star-inserted")
            details["location"] = location.text.strip()
        except:
            print("⚠️ Location not found")

        # Salary
        try:
            salary = card.find_element(By.CSS_SELECTOR, "span.font-size-12px")
            details["salary"] = salary.text.strip()
        except:
            print("⚠️ Salary not found")

        # Features
        try:
            feature_elements = card.find_elements(By.CSS_SELECTOR, "span.filter-label span.text-secondary.font-size-12px.pointer-events-none")
            details["features"] = ", ".join([elem.text.strip() for elem in feature_elements])
        except:
            print("⚠️ Features not found")

        # Posted
        try:
            posted = card.find_element(By.CSS_SELECTOR, "span.d-flex.align-items-center[style*='color: #8E9CB2']")
            details["posted"] = posted.text.strip()
        except:
            print("⚠️ Posted not found")

        # Urgent Tag
        try:
            urgent_tag = card.find_element(By.CSS_SELECTOR, "div.urgent-tag")
            details["urgent_tag"] = urgent_tag.text.strip()
        except:
            print("⚠️ Urgent tag not found")

        # Navigate to job page for additional details
        try:
            job_link = card.find_element(By.XPATH, "./ancestor::a[@href]")
            job_url = job_link.get_attribute("href")
            print(f"Navigating to job page: {job_url}")
            job_details = scrape_job_page(job_url)
            details.update(job_details)
        except Exception as e:
            print(f"❌ Error navigating to job page: {e}")

    except Exception as e:
        print(f"❌ Error scraping job card: {e}")

    return details

# === MAIN SCRAPING LOGIC ===
def main():
    os.system('clear')
    
    # Login flow
    print("🔐 Starting login...")
    login()

    # Calculate batches
    total_batches = (MAX_PAGES - START_PAGE + 1) // BATCH_SIZE
    if (MAX_PAGES - START_PAGE + 1) % BATCH_SIZE != 0:
        total_batches += 1

    for batch in range(total_batches):
        start_page = START_PAGE + (batch * BATCH_SIZE)
        end_page = min(START_PAGE + ((batch + 1) * BATCH_SIZE) - 1, MAX_PAGES)
        
        print(f"\n=== Processing batch {batch + 1}/{total_batches} (pages {start_page}-{end_page}) ===")
        batch_data = []

        for page in range(start_page, end_page + 1):
            print(f"\n📄 Visiting page {page}/{MAX_PAGES}...")
            try:
                page_url = f"{BASE_URL}?page={page}"
                driver.get(page_url)
                WebDriverWait(driver, 5).until(  # Ensure initial page loads
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(1)  # Reduced from 2 seconds
                scroll_to_load_jobs()
                
                job_cards = driver.find_elements(By.CSS_SELECTOR, "div.col-12.row.px-3")
                print(f"🔗 Found {len(job_cards)} job links.")

                # Save page source for debugging
                debug_file = f"listing_page_source_page_{page}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)

                for i, card in enumerate(job_cards, 1):
                    try:
                        print(f"  Processing job {i}/{len(job_cards)}")
                        job_details = scrape_job_card(card)
                        batch_data.append(job_details)
                    except Exception as e:
                        print(f"❌ Error scraping job {i}: {e}")
                        continue

            except Exception as e:
                print(f"❌ Error processing page {page}: {e}")
                with open(f"error_page_source_page_{page}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                continue

        # Save batch results and pause
        if batch_data:
            save_to_csv(batch_data)
            print(f"💾 Saved {len(batch_data)} jobs to {CSV_FILE}")
            time.sleep(7)  # Wait 7 seconds before next batch
        else:
            print("⚠️ No jobs found in this batch")
            with open(f"empty_batch_page_source_page_{page}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            time.sleep(7)  # Wait 7 seconds before next batch

    print(f"\n✅ Done! Check the final results in {CSV_FILE}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Script interrupted by user!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        with open("error_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    finally:
        if 'driver' in locals():
            driver.quit()