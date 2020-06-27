# -*- coding: utf-8 -*-

import scrapy


class StartusItem(scrapy.Item):
    company_name = scrapy.Field()
    profile_url = scrapy.Field()
    company_website_url = scrapy.Field()
    location = scrapy.Field()
    tags = scrapy.Field()
    founding_date = scrapy.Field()
    founders = scrapy.Field()
    employee_range = scrapy.Field()
    urls = scrapy.Field()
    emails = scrapy.Field()
    phones = scrapy.Field()
    description_short = scrapy.Field()
    description = scrapy.Field()
