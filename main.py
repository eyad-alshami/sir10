# mapIt.py - Launches a map in the browser using an adress from the command line or
import copy_reg
import types
import requests
import bs4
from multiprocessing import Pool
import time
import csv
import re
import datetime
import itertools


def _pickle_method(m):
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.func_name)
    else:
        return getattr, (m.im_self, m.im_func.func_name)


copy_reg.pickle(types.MethodType, _pickle_method)


TIME_STAMP = "%Y-%m-%dT%H:%M:%S"
NAME_REGEX = re.compile("(-+|\d+|\w+)+$")

class Mt_Spiders:
    def __init__(self):
        pass

    def open_web_page(self, url, show=False, save=False):
        """
        open a URL and show text if needed
        raises an exception if the response is not OK.

        :param url:
        string for URL wanted to be opened
        :param show:
        Boolean variable, set to True of you want to show the URL text
        :param save:
        Boolean variable, set to True of you want to save the URL text
        :return:
        the response object
        """
        res = requests.get(url)
        try:
            res.raise_for_status()  #
        except Exception as exc:
            print ('There was a problem: %s' % (exc))
        if show:
            print (res.text)
        if save:
            temp_file = open('tempfile.txt', 'wb')
            for chunk in res.iter_content(10000):
                temp_file.write(chunk)
            temp_file.close()
        return res

    def parse_webpage(self, res):
        """
        parse the response object and get text from it.
        :return:
        the bs4 object that represents the HTML tree.
        """
        html_ = bs4.BeautifulSoup(res.text, 'lxml')
        return html_

    def get_pages_urls(self, start=1, end=201):
        """
        generate the pages' names for the recent projects.
        :param start:
        the start number of pages.
        :param end:
        the end number of pages.
        :return:
        list of all pages' URLs.
        """
        start_url = 'https://www.kickstarter.com/discover/advanced?sort=newest&seed=2438578&page='
        return map(lambda i: start_url + str(i), range(start, end))

    def get_projects_urls_on_page(self, page_url):
        soup = self.parse_webpage(self.open_web_page(page_url))
        projects = soup.findAll('h6', class_='project-title')
        return map(lambda x: 'https://www.kickstarter.com' + x.a['href'], projects)

    def get_ID(self, url):
        result = re.compile('([0-9]+)').search(url)
        return result.group(1) if result is not None else None

    def get_date(self, date, launch_date= None):
        if launch_date is None:
            return datetime.datetime.strptime(re.compile('(\d+-\d+-\d+T\d+:\d+:\d+)').search(date).group(1), TIME_STAMP)
        else:
            d1 = datetime.datetime.strptime(re.compile('(\d+-\d+-\d+T\d+:\d+:\d+)').search(date).group(1), TIME_STAMP)
            return d1, int((d1 - launch_date).total_seconds())



    def get_soup(self, url):
        return self.parse_webpage(self.open_web_page(url))

    def get_data(self, project_url):
        # complete URL
        project = {}
        project_updates = project_url[:-11]+"/updates"
        project_url_ = project_url[:-11]+"/description"
        project["PROJECT_URL"] = project_url_
        project["UPDATE_URL"] = project_updates


        # name:
        project_name = NAME_REGEX.search(project_url_[:-12])
        if project_name is not None:
            project["NAME"] = project_name.group(0)
        else:
            project["NAME"] = "NONE"

        # Money
        money_soup = self.get_soup(project_url)
        money = money_soup.find('div', id='pledged')
        if money is not None:
            project["GOAL"] = int(money.attrs['data-goal'][:-2])
        else:
            project["GOAL"] = "None"

        # Launch Date
        date_soup = self.get_soup(project_updates)
        date = date_soup.find(name = "time", attrs={'data-format': 'LL'})
        if date is not None:
            project["LAUNCH_DATE"] = self.get_date(date.attrs['datetime'])
        else:
            project["LAUNCH_DATE"]="None"

        # Duration
        duration_soup = money_soup
        finish_date = duration_soup.find(name= "time", attrs={"class":"js-adjust-time","data-format":"llll z"})
        if finish_date is not None:
            project["FINISH_DATE"], project["DURATION"] = self.get_date(finish_date.attrs['datetime'], project["LAUNCH_DATE"])
        else:
            project["FINISH_DATE"]="None"
        return project


    def in_paralell(self, links, fn=None, threads=0):
        if threads <= 0:
            return map(fn, links)
        else:
            pool = Pool(threads)
            results = pool.map(fn, links)
            pool.close()
            pool.join()
            URLs = list(itertools.chain(*results))

            print "getting data"
            pool = Pool(threads)
            data = pool.map(self.get_data, URLs)
            pool.close()
            pool.join()

            return data


    def collect_projects(self):
    	with open("names.txt", r) as f:
    		for l in f:
    			print l
        return self.in_paralell(self.get_pages_urls(2, 50), self.get_projects_urls_on_page, 8)


if __name__ == '__main__':
    s = time.time()
    r = Mt_Spiders().collect_projects()
    print len(r)
    print "_______________******__________________"
    print ('It took:  ', time.time() - s)

    # s = time.time()
    # fieldsnames = ['UPDATE_URL', 'NAME', 'FINISH_DATE', 'PROJECT_URL', 'DURATION', 'LAUNCH_DATE', 'GOAL']
    # with open("projects.csv", "wb") as f:
    #     writer = csv.DictWriter(f, fieldnames=fieldsnames)
    #     writer.writeheader()
    #     for project in r:
    #         writer.writerow(project)
    #
    # print ('It took:  ', time.time() - s)
