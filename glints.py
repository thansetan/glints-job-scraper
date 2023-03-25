import bs4
import pandas as pd
import requests
from selenium.webdriver import (
    ActionChains,
    Edge,
    EdgeOptions,
    Chrome,
    ChromeOptions,
    Firefox,
    FirefoxOptions,
    Safari,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from tqdm import tqdm
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import DriverManager
from selenium.webdriver.edge.service import Service as e_service
from selenium.webdriver.chrome.service import Service as c_service
from selenium.webdriver.firefox.service import Service as f_service


class Glints:
    def __init__(self, title, job_type, yoe, remote):
        self.title = title.lower()
        self.type = job_type.lower()
        self.yoe = yoe
        self.remote = remote

    def generate_url(self):
        type_dict = {
            "intern": "INTERNSHIP",
            "fulltime": "FULL_TIME",
            "parttime": "PART_TIME",
            "freelance": "PROJECT_PASED",
        }
        yoe_dict = {
            "<1": "LESS_THAN_A_YEAR",
            "1-3": "ONE_TO_THREE_YEARS",
            "3-5": "THREE_TO_FIVE_YEARS",
            "5-10": "FIVE_TO_TEN_YEARS",
            "10+": "MORE_THAN_TEN_YEARS",
        }
        valid_yoe = all(map(lambda x: x in yoe_dict, self.yoe.split(" ")))
        valid_type = all(map(lambda x: x in type_dict, self.type.split(" ")))
        if not valid_type:
            raise ValueError(
                f"Unknown Type: {self.type} \nlist of valid Type: {list(type_dict.keys())}"
            )
        if not valid_yoe:
            raise ValueError(
                f"Unknown YoE: {self.yoe} \nlist of valid YoE: {list(yoe_dict.keys())}"
            )
        for t in type_dict.keys():
            self.type = self.type.replace(t, type_dict[t])
        for y in yoe_dict.keys():
            self.yoe = self.yoe.replace(y, yoe_dict[y])
        return f"https://glints.com/id/opportunities/jobs/explore?keyword={'%20'.join(self.title.split(' '))}&country=ID&locationName=Indonesia&jobTypes={self.type.replace(' ', '%2C')}&yearsOfExperienceRanges={self.yoe.replace(' ', '%2C')}&isRemote={str(self.remote).lower()}"

    def get_page(self, driver, url):
        driver.get(url)
        driver.execute_script("window.scrollBy(0,50)", "")  # trigger modal to show up
        modal_container = driver.find_element(
            By.XPATH, "//*[@data-testid='modal-container']"
        )  # get modal element
        if modal_container.is_enabled():
            driver.find_element(By.TAG_NAME, "body").send_keys(
                Keys.ESCAPE
            )  # remove modal
        annoying_element = driver.find_element(
            By.CLASS_NAME, "stylessc__CompactJobCardWrapper-sc-y7hwri-0"
        )  # get annoying element that make the loop fails
        if annoying_element.is_enabled():
            annoying_element.find_element(
                By.CLASS_NAME, "UnstyledButton-sc-ausmal-0"
            ).click()  # remove annoying element that make the loop fails
        return driver

    def handle_infinite_scroll(self, driver):
        infinite_scroll = driver.find_element(
            By.CLASS_NAME, "InfiniteScrollsc__InfiniteScrollContainer-sc-1nmx8l5-0"
        )  # get infinite scroll element
        while (
            infinite_scroll.text != "Semua lowongan sudah ditampilkan"
        ):  # loop until all jobs is displayed
            elem = driver.find_element(
                By.CLASS_NAME, "InfiniteScrollsc__InfiniteScrollContainer-sc-1nmx8l5-0"
            )
            ActionChains(driver).move_to_element(elem).perform()

    def get_all_jobs(self, driver):
        job_list = driver.find_elements(By.CLASS_NAME, "compact_job_card")
        return job_list

    def get_job_details(self, idx, job):
        job_dict = {
            "category": None,
            "title": None,
            "company_name": None,
            "location": None,
            "salary": None,
            "YoE": None,
            "last_updated": None,
            "url": None,
        }
        job_card = job.find_element(By.XPATH, f"//div[@data-position='{idx}']")
        title_and_company = job_card.find_element(
            By.CLASS_NAME, "job-card-info"
        ).text.split("\n")
        job_info = [
            job.text
            for job in job_card.find_elements(
                By.CLASS_NAME, "CompactOpportunityCardsc__OpportunityInfo-sc-1y4v110-13"
            )
        ]
        last_updated = job_card.find_element(
            By.CLASS_NAME, "CompactOpportunityCardsc__UpdatedAtMessage-sc-1y4v110-17"
        ).text.strip()
        url = job_card.find_element(
            By.CLASS_NAME, f"job-search-results_job-card_link"
        ).get_attribute("href")
        job_dict["category"] = job_card.get_attribute("data-gtm-job-category")
        job_dict["title"] = title_and_company[0]
        job_dict["company_name"] = title_and_company[1]
        job_dict["location"] = job_info[0]
        job_dict["salary"] = job_info[1]
        job_dict["YoE"] = job_info[2]
        job_dict["last_updated"] = last_updated.replace("Diperbarui ", "")
        job_dict["url"] = url
        return job_dict

    def get_job_pages(self, url):
        job_page_dict = {
            "job_type": None,
            "benefit_list": None,
            "skill_list": None,
            "job_desc": None,
            "company_size": None,
            "company_desc": None,
            "company_social_list": None,
            "company_address": None,
        }
        has_benefit = False
        res = requests.get(url)
        soup = bs4.BeautifulSoup(res.content, "html.parser")
        job_type = soup.find_all(class_="TopFoldsc__JobOverViewInfo-sc-kklg8i-9")[2]
        container = soup.find(class_="MainContainersc__MainBody-sc-iy5ixg-2 dyvvBG")
        first = container.find(
            class_="Opportunitysc__DividerContainer-sc-1gsvee3-5 cukPBF"
        )
        try:
            benefits = first.next_sibling
            list_of_benefit = list(benefits.children)
            benefit_list = [
                benefit.find("h3").text.strip() for benefit in list_of_benefit[1]
            ]
            has_benefit = True
        except:
            pass
        skills = benefits.next_sibling if has_benefit else first.next_sibling
        skills_list = list(skills.children)[1:]
        skill_list = [skill.text for skill in skills_list]
        job_desc = soup.find(
            class_="JobDescriptionsc__DescriptionContainer-sc-1jylha1-2"
        ).find("div", attrs={"data-contents": True})
        job_desc = "\n".join([desc.text.strip() for desc in list(job_desc.children)])
        company_card = soup.find(
            class_="AboutCompanySectionsc__Main-sc-7g2mk6-0 jZPEPE"
        )
        company_size = soup.find(
            class_="AboutCompanySectionsc__CompanyIndustryAndSize-sc-7g2mk6-7"
        ).text.strip()
        company_desc = company_card.find(class_="public-DraftStyleDefault-block")
        company_social = company_card.find(
            class_="AboutCompanySectionsc__WebsiteContainer-sc-7g2mk6-8 gMTaJJ"
        ).find_all(class_="AboutCompanySectionsc__Website-sc-7g2mk6-9")
        social_list = [social.find("a").get("href") for social in company_social]
        company_address = company_card.find(
            class_="AboutCompanySectionsc__AddressWrapper-sc-7g2mk6-14"
        )
        job_page_dict["job_type"] = job_type.text.strip()
        try:
            job_page_dict["benefit_list"] = benefit_list
        except:
            pass
        job_page_dict["skill_list"] = skill_list
        job_page_dict["job_desc"] = job_desc
        job_page_dict["company_size"] = company_size if company_size else None
        job_page_dict["company_desc"] = (
            company_desc.text.strip() if company_desc else None
        )
        job_page_dict["company_social_list"] = social_list
        job_page_dict["company_address"] = (
            company_address.find(
                class_="AboutCompanySectionsc__AddressHeader-sc-7g2mk6-13"
            ).next_sibling.strip()
            if company_address
            else None
        )
        return job_page_dict

    def scrape(self, browser):
        if browser == "edge":
            options = EdgeOptions()
            options.add_experimental_option("excludeSwitches", ["enable-logging"])
            driver = Edge(
                service=e_service(EdgeChromiumDriverManager().install()),
                options=options,
            )
        elif browser == "chrome":
            options = ChromeOptions()
            options.add_experimental_option("excludeSwitches", ["enable-logging"])
            driver = Chrome(
                serivce=c_service(ChromeDriverManager().install()), options=options
            )
        elif browser == "firefox":
            options = FirefoxOptions()
            options.add_experimental_option("excludeSwitches", ["enable-logging"])
            driver = Firefox(
                service=f_service(DriverManager().install()), options=options
            )
        elif browser == "safari":
            driver = Safari()
        else:
            raise ValueError(f"Browser unsupported: {browser}")
        url = self.generate_url()
        page = self.get_page(driver, url)
        self.handle_infinite_scroll(page)
        job_list = self.get_all_jobs(page)
        n = len(job_list)
        list_of_jobs = []
        print("Getting job details...")
        for i, job in tqdm(enumerate(job_list), total=n):
            job_detail = self.get_job_details(i, job)
            list_of_jobs.append(job_detail)
        driver.close()
        print("Getting more detailed info about the job...")
        for job in tqdm(list_of_jobs, total=n):
            job_page = self.get_job_pages(job["url"])
            job.update(job_page)
        return list_of_jobs

    def save_output(self, list_of_jobs, output_path):
        path = ".".join(output_path.split(".")[:-1])
        ext = output_path.split(".")[-1]
        if ext == "csv":
            pd.DataFrame(list_of_jobs).to_csv(f"{path}.{ext}", index=False)
        elif ext in ["xlsx", "xls"]:
            pd.DataFrame(list_of_jobs).to_excel(f"{path}.{ext}", index=False)
        elif ext == "json":
            pd.DataFrame(list_of_jobs).to_json(f"{path}.{ext}", orient="index")
        else:
            return "Unknown output type"
        return f"Result saved to: {path}.{ext}"
