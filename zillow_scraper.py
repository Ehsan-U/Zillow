import csv
import time
from scrapy.selector import Selector
from playwright.sync_api import sync_playwright
from traceback import print_exc
import logging
import coloredlogs
import random


""" Zillow """
class Zillow_Scraper():
    logger = logging.getLogger("Zillow Scraper")
    coloredlogs.install(level='DEBUG', logger=logger)
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'host': 'www.zillow.com',
    }
    sleep_range = [1.0 ,5.0]
    previous_agent = ''


    def init_writer(self):
        file = open("Output.csv", 'w')
        writer = csv.writer(file)
        writer.writerow(["Name", 'Phone', 'Reviews', 'License', 'Company'])
        return file, writer


    def init_playwright(self):
        play = sync_playwright().start()
        browser = play.firefox.launch(headless=False)
        page = browser.new_page()
        return play, page


    def sleep(self):
        start = self.sleep_range[0]
        end = self.sleep_range[-1]
        time.sleep(random.uniform(start, end))


    def is_lastPage(self, result):
        current_agent = result[0][0]
        if current_agent == self.previous_agent:
            return True
        else:
            self.previous_agent = current_agent
            return None


    def random_move(self, page):
        for i in range(5):
            x = random.randint(0, 800)
            y = random.randint(0, 600)
            page.mouse.move(x, y)

    def parse(self, response):
        sel = Selector(text=response)
        result = []
        for agent in sel.xpath("//tbody[contains(@class, 'StyledTableBody')]/tr"):
            name = agent.xpath(".//span[contains(text(),'phone')]/parent::div/preceding-sibling::a/text()").get()
            phone = agent.xpath(".//span[contains(text(),'phone')]/parent::div/text()").get()
            reviews = agent.xpath(".//span[contains(text(),'phone')]/parent::div/following-sibling::a/text()").get()
            agent_license = agent.xpath(".//div[contains(text(), 'Agent')]/text()[2]").get()
            company = agent.xpath(".//span[contains(text(),'phone')]/parent::div//following-sibling::div[1]/text()").get()
            self.logger.info(f" [+] Name: {name}, Phone: {phone}, Reviews: {reviews}, License: {agent_license}, Company: {company}")
            result.append((name, phone, reviews, agent_license, company))
        return result


    def get_data(self, page, city, writer):
        page_no = 1
        city = city.lower().replace(' ','-')
        page.route("**/*", lambda route: route.abort() if route.request.resource_type == "image"  else route.continue_())
        while True:
            page.goto(f"https://www.zillow.com/professionals/real-estate-agent-reviews/{city}/?page={page_no}")
            page.wait_for_selector("//div[@id='__next']")
            self.sleep()
            self.random_move(page)
            result = self.parse(page.content())
            if self.is_lastPage(result):
                break
            else:
                writer.writerow(result)
                page_no += 1
                continue


    def main(self):
        city = 'New York NY'
        file, writer = self.init_writer()
        play, page = self.init_playwright()
        try:
            self.get_data(page, city, writer)
        except Exception:
            print_exc()
            input("enter:")
        else:
            play.stop()
            file.close()

z = Zillow_Scraper()
z.main()