# -*- coding: utf-8 -*-
"""
created by xhijack@gmail.com
updated: August 5 2017
"""
from __future__ import unicode_literals
import scrapy
import json

from scrapy import Request

from scraptop.helpers import string2integer
from scraptop.items import Product

DOMAIN = 'ace.tokopedia.com'
SEARCH_URL = 'https://{domain}/search/v2.6/product?shop_id={shop_id}&ob=11&rows=20&start={start}&' \
             'full_domain=www.tokopedia.com&scheme=https&device=desktop&source=shop_product'

CATEGORY_URL = 'https://ace.tokopedia.com/search/product/v3?full_domain=www.tokopedia.com&' \
               'scheme=https&device=desktop&source=directory&page=1&image_size=200&rows=75&sc={sc}' \
               '&start={start}&ob=23'


class TokopediaSpider(scrapy.Spider):
    name = "tokopedia"
    allowed_domains = ["tokopedia.com"]
    # start_urls = [SEARCH_URL.format(domain=DOMAIN, shop_id=24, start=0)]

    def __init__(self, id_=None, by=None):
        self.by = by
        self.id_ = id_
        # self.category_id = category_id
        # self.shop_id = shop_id

        if self.by == 'brand':
            self.start_urls = (SEARCH_URL.format(domain=DOMAIN, shop_id=id_, start=0),)
        elif self.by == 'category':
            self.start_urls = (CATEGORY_URL.format(sc=id_, start=0),)

    def parse(self, response):
        if self.by == 'brand':
            return self.parse_by_brand(response=response)
        elif self.by == 'category':
            return self.parse_by_categories(response=response)

    def parse_by_brand(self, response):
        items = json.loads(response.body)
        total_data = items['header']['total_data']
        total_pages = int(round(total_data / 20.0))

        for item in items['data']:
            product = Product()
            product['product_id'] = item['id']
            product['title'] = item['name']
            product['price'] = string2integer(item['price'])
            product['seller'] = item['shop']['name']
            product['link_url'] = item['uri']
            product['location'] = item['shop']['location']
            # product['image_urls'] = [item['image_uri_700']]

            request = Request(product['link_url'], callback=self.parse_detail)
            request.meta['product'] = product
            yield request

        for i in range(1, total_pages + 1):
            yield Request(SEARCH_URL.format(domain=DOMAIN, start=i*20, shop_id=self.id_), callback=self.parse_by_brand)

    def parse_detail(self, response):
        weight = response.xpath('//div[@class="tab-content product-content-container "]/div/div/div/dl/dd/text()').extract()[2]
        image_urls = response.xpath('//div[@class="jcarousel product-imagethumb-alt"]/ul/li/a/@href').extract()

        resps = response.xpath("//div[@id='breadcrumb-container']/ul/li/h2")
        categories = []
        for resp in resps:
            temp = resp.xpath('a/text()').extract()
            if temp != []: categories.append(temp[0].strip())

        response.meta['product']['weight'] = string2integer(weight)
        response.meta['product']['categories'] = ",".join(categories)
        response.meta['product']['image_urls'] = image_urls

        yield response.meta['product']

    def parse_by_categories(self, response):
        items = json.loads(response.body)
        total_data = items['header']['total_data']
        total_pages = int(round(total_data / 80.0))

        for item in items['data']['products']:
            product = Product()
            product['product_id'] = item['id']
            product['title'] = item['name']
            product['price'] = string2integer(item['price'])
            product['seller'] = item['shop']['name']
            product['link_url'] = item['url']
            product['location'] = item['shop']['location']
            product['image_urls'] = [item['image_url_700']]
            yield product

        for i in range(1, total_pages + 1):
            yield Request(CATEGORY_URL.format(start=i * 80, sc=self.id_), callback=self.parse_by_categories)



                # https://ace.tokopedia.com/search/product/v3?full_domain=www.tokopedia.com&scheme=https&device=desktop&source=directory&page=1&image_size=200&rows=75&sc=24&start=0&ob=23
# https://ace.tokopedia.com/search/product/v3?full_domain=www.tokopedia.com&scheme=https&device=desktop&source=directory&page=1&image_size=200&rows=75&sc=1536&start=0&ob=23
