# -*- coding: utf-8 -*-
import scrapy
from startus.items import StartusItem
import json
import calendar
import datetime
from lxml import html
from urllib.request import urlopen
import requests
import urllib.request
import csv
import pandas as pd
from random import randrange


class E27SpiderSpider(scrapy.Spider):
    name = 'e27_spider'
    allowed_domains = ['e27.co']
    start_urls = ['https://e27.co/startups']

    custom_settings = {
        'FEED_EXPORT_FIELDS': ['company_name', 'profile_url', 'company_website_url', 'location', 'tags',
            'founding_date', 'founders', 'employee_range', 'urls', 'emails', 'phones', 'description_short', 'description'
        ]
    }

    def parse(self, response):
        url_index_lst = []
        while len(url_index_lst) != 251:
            index = randrange(32415)
            url_index_lst.append(index) if index not in url_index_lst else ''

        for url_index in url_index_lst:
            url_profile = pd.read_csv('Result_urls.csv', skiprows=url_index, nrows=1).columns.tolist()[0]
            slug = url_profile.replace('https://e27.co/startups/', '').replace('/', '')
            url_json = 'https://e27.co/api/startups/get/?slug={}&data_type=general&get_badge=true'.format(slug)
            yield scrapy.FormRequest(
                url=url_json,
                callback=self.parse_item
            )

    def parse_item(self, response):
        i = StartusItem()
        data = json.loads(response.body.decode('utf-8')) # decode for python 3.5 and lower

        i['company_name'] = data['data']['name'] if 'name' in data['data'] else ''
        i['profile_url'] = 'https://e27.co/startups/{}/'.format(data['data']['slug'] if 'slug' in data['data'] else 'no_link')
        i['company_website_url'] = data['data']['metas']['website'] if 'website' in data['data']['metas'] else ''

        number_of_locations = len(data['data']['location'])
        locations = []
        for location_index in range(number_of_locations):
            location = data['data']['location'][location_index]['text']
            locations.append(location)
        i['location'] = ', '.join(locations)
        try:
            i['tags'] = ', '.join(json.loads(data['data']['market'])[0] if 'market' in data['data'] else '')
        except TypeError:
            i['tags'] = ''
        try:
            day = 1
            month_number = data['data']['metas']['found_month'] if 'found_month' in data['data']['metas'] else ''
            found_year = data['data']['metas']['found_year'] if 'found_year' in data['data']['metas'] else ''
            i['founding_date'] = str(datetime.date(int(found_year), int(month_number), day)) if found_year != '' and month_number != '' else '{}'.format(found_year)
        except ValueError:
            i['founding_date'] = ''

        i['emails'] = data['data']['metas']['email'] if 'email' in data['data']['metas'] else ''

        urls = []
        linkedin = data['data']['metas']['linkedin'] if 'linkedin' in data['data']['metas'] else ''
        tw = data['data']['metas']['twitter'] if 'twitter' in data['data']['metas'] else ''
        twitter = 'https://twitter.com/{}'.format(tw) if len(tw)>1 else ''
        facebook = data['data']['metas']['facebook'] if 'facebook' in data['data']['metas'] else ''
        urls.append(linkedin) if len(linkedin)>1 else ''
        urls.append(twitter) if len(twitter)>1 else ''
        urls.append(facebook) if len(facebook)>1 else ''
        i['urls'] = ', '.join(urls)
        i['description_short'] = data['data']['metas']['short_description'] if 'short_description' in data['data']['metas'] else ''
        i['description'] = data['data']['metas']['description'] if 'description' in data['data']['metas'] else ''
        i['phones'] = data['data']['metas']['phone'] if 'phone' in data['data']['metas'] else ''
        i['employee_range'] = data['data']['metas']['employee'] if 'employee' in data['data']['metas'] else ''

        id_startup = data['data']['id'] if 'id' in data['data'] else ''
        yield scrapy.FormRequest(
            url='https://e27.co/api/site_user_startups/site_users/?startup_id={}'.format(id_startup),
            callback=self.parse_team,
            meta = {
            'i': i,
            })

    def parse_team(self, response):
        i = response.meta['i']
        data_team = json.loads(response.body.decode('utf-8')) # decode for python 3.5 and lower
        
        number_of_team = len(data_team['data']['site_users']) if 'site_users' in data_team['data'] else ''
        team_slug_lst = []
        founders = []
        for index in range(number_of_team):
            team_slug_lst.append(data_team['data']['site_users'][index]['url'].split('/')[-1]) if 'url' in data_team['data']['site_users'][index] else ''
        for slug in team_slug_lst:
            hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'}
            url = 'https://e27.co/{}/?json'.format(slug)
            request = urllib.request.Request(url, headers=hdr)
            response = urllib.request.urlopen(request)
            worker_page_data = response.read().decode('utf-8') # decode for python 3.5 and lower

            data_page = html.fromstring(worker_page_data)
            usertitle_name = ''.join([x.strip() for x in data_page.xpath('//*[@class="profile-usertitle-name"]//text()') if x.strip() != '']).replace('ø', 'o')

            # search for founders among the team
            # check in resume
            categories_of_resume_lst = data_page.xpath('//*[@class="col-md-9"]')
            for category in categories_of_resume_lst:
                resume = ', '.join([x.strip() for x in category.xpath('.//text()') if x.strip() != ''])
                if 'founder' in resume.lower() and i['company_name'].lower() in resume.lower():
                    founders.append(usertitle_name) if usertitle_name not in founders else ''

            # check in bio
            bio = ''.join([x.strip() for x in data_page.xpath('//*[@class="profile-desc-text"]//text()') if x.strip() != ''])
            bio_by_sentence = bio.split('.')
            for sentence in bio_by_sentence:
                if 'founder' in sentence.lower() and i['company_name'].lower() in sentence.lower() and usertitle_name.lower() in sentence.lower():
                    founders.append(usertitle_name) if usertitle_name not in founders else '' 

            # check in profile title
            profile_title = ''.join([x.strip() for x in data_page.xpath('//*[@class="profile-usertitle-job"]//text()') if x.strip() != ''])
            if 'founder' in profile_title.lower():
                founders.append(usertitle_name) if usertitle_name not in founders else ''
        i['founders'] = ', '.join(founders)

        # or can use - scrapy crawl e27_url_spider -o data.csv -t csv
        with open('Result_data.csv', 'a') as f:
            w = csv.DictWriter(f, i.keys())
            if f.tell() == 0:
                w.writeheader()
            w.writerow(i)        

        yield i