# -*- coding: utf-8 -*-
import scrapy
import json
import csv

class E27UrlSpiderSpider(scrapy.Spider):
    name = 'e27_url_spider'
    allowed_domains = ['e27.co']
    start_urls = ['https://e27.co/startups']

    def parse(self, response):
        for page_number in range(0, 32500, 10):
            url = 'https://e27.co/api/startups/?all_fundraising=&pro=0&tab_name=recentlyupdated&start={}&length=10'.format(page_number)
            yield scrapy.FormRequest(
                url=url,
                callback=self.parse_links
            )

    def parse_links(self, response):
        i = {}
        data_links = json.loads(response.body.decode('utf-8')) # decode for python 3.5 and lower
        number_startups_on_page = len(data_links['data']['list'])
        for index in range(number_startups_on_page):
            link = 'https://e27.co/startups/{}/'.format(data_links['data']['list'][index]['slug'])
            i['profile_url'] = link

            # or can use - scrapy crawl e27_url_spider -o Result_urls.csv -t csv
            with open('Result_urls.csv', 'a') as f:
                for key in i.keys():
                    f.write("%s,%s\n"%(key,i[key]))

            yield i