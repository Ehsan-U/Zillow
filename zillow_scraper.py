import time
from scrapy.selector import Selector
from playwright.sync_api import sync_playwright
from traceback import print_exc
import logging
import coloredlogs
import random
from sqlalchemy import create_engine, Column, String, Integer, CHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import warnings
logging.disable(logging.WARNING)
warnings.filterwarnings("ignore")
Base = declarative_base()



""" Zillow """
class Zillow_Scraper():

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'host': 'www.zillow.com',
    }
    sleep_range = [1.0 ,5.0]
    previous_agent = ''
    ID = 1


    def init_playwright(self):
        play = sync_playwright().start()
        browser = play.firefox.launch(headless=False)
        page = browser.new_page()
        return play, page

    def init_DB(self):
        engine = create_engine("sqlite:///mydb.db", echo=True)
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        return session

    def clean(self, text):
        if text:
            return text.strip()
        else:
            return ''

    def save_to_db(self, db, results):
        for result in results:
            name = self.clean(result[0])
            phone = self.clean(result[1])
            reviews = self.clean(result[2])
            agent_license = self.clean(result[3])
            company = self.clean(result[4])
            agent = Agent(self.ID, name, phone, reviews, agent_license, company)
            db.add(agent)
            db.commit()
            self.ID +=1

    def sleep(self):
        start = self.sleep_range[0]
        end = self.sleep_range[-1]
        time.sleep(random.uniform(start, end))


    def is_lastPage(self, results):
        current_agent = results[0][0]
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
        results = []
        for agent in sel.xpath("//tbody[contains(@class, 'StyledTableBody')]/tr"):
            name = agent.xpath(".//span[contains(text(),'phone')]/parent::div/preceding-sibling::a/text()").get()
            phone = agent.xpath(".//span[contains(text(),'phone')]/parent::div/text()").get()
            reviews = agent.xpath(".//span[contains(text(),'phone')]/parent::div/following-sibling::a/text()").get()
            agent_license = agent.xpath(".//div[contains(text(), 'Agent')]/text()[2]").get()
            company = agent.xpath(".//span[contains(text(),'phone')]/parent::div//following-sibling::div[1]/text()").get()
            print(f" [+] Name: {name}, Phone: {phone}, Reviews: {reviews}, License: {agent_license}, Company: {company}")
            results.append((name, phone, reviews, agent_license, company))
        return results


    def get_data(self, page, city, db):
        page_no = 1
        city = city.lower().replace(' ','-')
        page.route("**/*", lambda route: route.abort() if route.request.resource_type == "image"  else route.continue_())
        while True:
            page.goto(f"https://www.zillow.com/professionals/real-estate-agent-reviews/{city}/?page={page_no}")
            page.wait_for_selector("//div[@id='__next']")
            self.sleep()
            self.random_move(page)
            results = self.parse(page.content())
            if self.is_lastPage(results):
                break
            else:
                self.save_to_db(db, results)
                page_no += 1
                continue


    def main(self):
        city = 'New York NY'
        play, page = self.init_playwright()
        db = self.init_DB()
        try:
            self.get_data(page, city, db)
        except Exception:
            print_exc()
            input("enter:")
        else:
            play.stop()




""" SQLAlchemy """

class Agent(Base):
    __tablename__ = "Agents"

    id_ = Column("ID", Integer, primary_key=True)
    name = Column("Name", String)
    phone = Column("Phone", String)
    reviews = Column("Reviews", String)
    license = Column("License", String)
    company = Column("Company", String)

    def __init__(self, id_, name, phone, reviews, license, company):
        self.id = id_
        self.name = name
        self.phone = phone
        self.reviews = reviews
        self.license = license
        self.company = company

    # object representation
    def __repr__(self):
        return f"{self.id_} {self.name} {self.phone} {self.reviews} {self.license} {self.company}"



# scraper
z = Zillow_Scraper()
z.main()