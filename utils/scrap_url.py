import time
import random
from tqdm import tqdm
import pandas as pd

def wait():
    time.sleep(random.uniform(1, 3))


ENDPOINT = "https://www.booking.com/searchresults.fr.html?ss="

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

options = Options()
options.set_preference("dom.webdriver.enabled", False)  # Try to hide Selenium
options.set_preference("useAutomationExtension", False)
options.set_preference("general.useragent.override", 
                       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36")  # Fake user-agent


driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)


def get_hotel_url(hotel, town):
    query = build_query(hotel, town)
    driver.get(query)

    wait()

    try:
        # Wait until at least one div with data-soldout is present
        a_tag = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='hotel']"))
        )
        
        href = a_tag.get_attribute("href")
        return href.split("?")[0]

    except Exception as e:
        print(f"No link found or error: {e}")
        return ""

def read_file(filename):
    """
    Read  (.xlsx) file from the first sheet into a pandas DataFrame.
    """
    try:
        df = pd.read_csv(filename)  # always first sheet
        print(f"Loaded '{filename}'  successfully.")
        return df
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None



def build_query(hotel_name, town):
    query = ENDPOINT + '+'.join(town.split()) + '+' + '+'.join(hotel_name.split())
    return query.lower()


def main():
    # Read Excel/CSV file
    df = read_file('Hotels+villes.csv')

    # Create list of tuples (id, name, town)
    name_town_tuples = [
        (id_, name, town)  # avoid overwriting 'id' builtin
        for id_, name, town in zip(df["id"], df["name"], df["town"])
    ]

    results = []

    for id_, name, town in tqdm(name_town_tuples):
        if type(town) == float: town = " "
        url = get_hotel_url(name, town)
        print(id_, name, town, url)
        results.append({
            "id": id_,
            "name": name,
            "town": town,
            "url": url
        })

    driver.quit()
    # Save results to CSV
    results_df = pd.DataFrame(results)
    results_df.to_csv("hotels_with_urls.csv", index=False, encoding="utf-8")
    print("Results saved to 'hotels_with_urls.csv'")

if __name__ == "__main__":
    main()