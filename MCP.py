from mcp.server.fastmcp import FastMCP
#-------------------------------------------
import time
#-------------------------------------------
from selenium import webdriver  #Interacts with the browser; clicks buttons, opens pages and reads HTML.
from selenium.webdriver.chrome.options import Options  #Configure chrome driver, not specifically needed but still helpful.
from selenium.webdriver.chrome.service import Service #Acts as a manager. Used to locate the chromedriver nad more or less manage it on the pc.
from selenium.webdriver.common.by import By  #Used to locate elements.
from selenium.webdriver.support.ui import WebDriverWait #Waits for the page to fully load.
from selenium.webdriver.support import expected_conditions as EC #Used intandem with WebDriverWit, basically used to set condition . Wait until something happens (condition) on the webpage before continuing.
from webdriver_manager.chrome import ChromeDriverManager
#Naming the MCP
mcp = FastMCP("Claims_Reader_DME")


#Creating the browser driver
def create_driver():
    """
    Options() is a chrome driver configuration object from selenium. We add specific arguments to it. Can be adjusted later on.
    "--headless" specifies to run chrome without a visible window
    "--disable-gpu" specifies to not use gpu, prevents gpu related errors/issues
    "--no-sandbox" specifies chrome to run with few permissions to avoid permission issues, not really needed here but keeping for testing purpose.

     End result:
     Launches chrome with the above settings.

    """
    options = Options()
    options.add_argument("--headless=new")  # Has to be headless when on Render
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # options.binary_location = "/usr/bin/chromium" 
    # Location to point to for chromium

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    return driver

#----------------------------------------

# Function to clean up the term provided by the user to the LLM
def term_cleanup(term):

    cleaned_term = term.replace('"','').strip().lower()

    return cleaned_term

#---------------------------------------- OIG Tool Functions ----------------------------------------

# Function to read the page......
def Read_Block(driver, wait, link):
    page = {}


    wait.until(EC.presence_of_element_located((By.XPATH, ".//main[@id = 'main-content' and @class = 'main']")))

    container = driver.find_element(By.XPATH, ".//main[@id = 'main-content' and @class = 'main']")

    heading = container.find_element(By.XPATH, ".//h1[contains(@class, 'font-heading')]").text.strip()
    content = container.find_element(By.XPATH, ".//p").text.strip()
    link = container.find_element(By.XPATH, ".//p//a[contains(@class, 'text-bold')]").get_attribute("href")

    page["Heading"] = heading
    page["Content"] = content
    page["Link to Full Report"] = link

    add_details = container.find_elements(By.XPATH, ".//h2[text()='Action Details']/following-sibling::ul[1]/li")

    for a in add_details:

        label = a.find_element(By.XPATH, ".//span").text.strip().replace(":", "")
        nested = a.find_elements(By.XPATH, ".//ul//li")
        if nested:
            val = nested[0].text.strip()
        else:
            val = driver.execute_script("return arguments[0].nextSibling.nodeValue;",a.find_element(By.XPATH, ".//span")).strip()
        page[label] = val

    return page


# Function to get first few results and their content....
def Link_Fetch_Block(url_result):
    driver = create_driver()
    wait = WebDriverWait(driver, 200)
    driver.get(url_result)

    wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id = 'results']")))
    items = driver.find_elements(By.XPATH, "//div[contains(@class,'search-result-item')]//div[@role='link']")
    result = []

    for index in range(min(10, len(items))):
        try:


            """
            Based on the iteration of the loop, select respective result webelement
            eg; at 3rd loop check the 3 result.....
            """
            i = items[index]

            title = i.find_element(By.XPATH, ".//h2[@class='result-title-label']").text.strip()

            # Scroll the page to the webelement from items
            driver.execute_script("arguments[0].scrollIntoView(true);", i)
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", i)

            wait.until(lambda d: d.current_url != url_result)

            link = driver.current_url

            page_content = Read_Block(driver, wait, link)
            time.sleep(0.3)

            result.append({"Title": title, "Link": link, "WebPage": page_content})

            driver.back()
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id = 'results']")))

        except Exception as e:
            driver.get(url_result)
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id = 'results']")))

    driver.quit()

    return result

#----------------------------------------
@mcp.tool()
def OIG_search (item: str) -> list:
    url_search = "https://search.usa.gov/search?utf8=%E2%9C%93&query=&affiliate=hhs_oig&commit=Search"
    driver = create_driver()
    wait = WebDriverWait(driver, 200)
    driver.get(url_search)

    wait.until(EC.presence_of_element_located((By.XPATH, ".//div[@class = 'grid-container']//form[contains(@class,'usa-search--small')]//input[@id = 'search-field']")))

    container = driver.find_element(By.XPATH, ".//form[contains(@class,'usa-search--small') and @role = 'search']")

    term = term_cleanup(item)

    # Finding and storing the location where terms are to be added....
    terminput = container.find_element(By.XPATH, ".//input[@id = 'search-field' and @type = 'search']")

    # Clearning input just in-case.
    terminput.clear()

    # Sending the inputs
    terminput.send_keys(term)

    # Find and storing the location of the button that allows the search process.
    search = driver.find_element(By.XPATH, "//button[contains(@class,'usa-button') and @type = 'submit' ]")
    driver.execute_script("arguments[0].click();", search)

    # Waits for changes in link.
    wait.until(lambda new: new.current_url != url_search)

    # Stores the new link.
    url_result = driver.current_url

    driver.quit()
    # Kills the chrome instance to save memory

    time.sleep(0.3)
    output = Link_Fetch_Block(url_result)

    return output



#----------------------------------------
if __name__ == "__main__":

    mcp.run()




