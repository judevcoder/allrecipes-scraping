import re
import scrapy

is_empty = lambda x, y=None: x[0] if x else y

class AllrecipesItem(scrapy.Item):
    # define the fields for your item here like:
    Title = scrapy.Field()
    Ingredients = scrapy.Field()
    Categories = scrapy.Field()
    Preptime = scrapy.Field()
    Step = scrapy.Field()
    Review_count = scrapy.Field()
    Average_rating = scrapy.Field()
    Nutrition = scrapy.Field()

class AllrecipesProductsSpider(scrapy.Spider):

    name = 'allrecipes'
    allowed_domains = ["allrecipes.com"]

    start_urls = ['http://allrecipes.com/recipes/739/healthy-recipes/diabetic/']
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/41.0.2228.0 Safari/537.36', }

    def __init__(self, *args, **kwargs):
        super(AllrecipesProductsSpider, self).__init__(site_name=self.allowed_domains[0], *args, **kwargs)
        self.current_page = 0

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0], callback=self.parse_pages, headers=self.headers)

    def parse_pages(self, response):
        # self.current_page += 1
        last_pagenum = 30
        page_links = []

        for page_num in range(1, int(last_pagenum)):
            next_page_link = 'http://allrecipes.com/recipes/739/healthy-recipes/diabetic/?page={page_num}'
            page_links.append(next_page_link)
        for link in page_links:
            yield scrapy.Request(url=link, callback=self.parse_links, dont_filter=True)

    def parse_links(self, response):
        product_links = []
        href_links = []
        if response.body:
            href_links = list(set(response.xpath("//article[@class='grid-col--fixed-tiles']//a/@href").extract()))
        if href_links:
            for href in href_links:
                if 'recipe' in href:
                    product_links.append('http://allrecipes.com' + href)
        if product_links:
            for product_link in product_links:
                yield scrapy.Request(url=product_link, callback=self.parse_product, headers=self.headers, dont_filter=True)
        return

    def parse_product(self, response):
        product = AllrecipesItem()

        # Parse review_count
        review_count = response.xpath("//a[contains(@class, 'read--reviews')]//span[@class='review-count']/text()").extract()
        if review_count:
            review_count = int(re.search('\d+', review_count[0]).group())

        # Parse average_rating
        average_rating = response.xpath(
            "//section[contains(@class, 'recipe-summary')]//div[@class='rating-stars']/@data-ratingstars").extract()
        if average_rating:
            average_rating = float(average_rating[0])

        # Parse title
        title = response.xpath("//h1[@itemprop='name']/text()").extract()[0]

        # Parse ingredients
        ingredients = response.xpath(
        "//ul[contains(@class, 'list-ingredients')]//li//span[@itemprop='ingredients']/text()").extract()

        if ingredients:
            ingredients = len(ingredients)

        # Parse categories
        categories = response.xpath("//ul[contains(@class, 'breadcrumbs')]//li//span[@class='toggle-similar__title']/text()").extract()

        # Parse preptime
        preptime = response.xpath("//ul[@class='prepTime']//li//span[@class='prepTime__item--time']/text()").extract()
        if preptime:
            preptime = int(re.search('\d+', preptime[2]).group())

        # Parse step
        step = response.xpath(
            "//li[contains(@class, 'step')]//span[@class='recipe-directions__list--item']/text()").extract()

        # Parse nutrition_information

        calories = response.xpath("//div[@class='recipe-nutrition__form']//ul[@class='nutrientLine']//li[@itemprop='calories']/span/text()").extract()[0]
        fat = response.xpath("//div[@class='recipe-nutrition__form']//ul[@class='nutrientLine']//li[@itemprop='fatContent']/span/text()").extract()[0]
        carbohydrateContent = response.xpath("//div[@class='recipe-nutrition__form']//ul[@class='nutrientLine']//li[@itemprop='carbohydrateContent']/span/text()").extract()[0]
        proteinContent = response.xpath("//div[@class='recipe-nutrition__form']//ul[@class='nutrientLine']//li[@itemprop='proteinContent']/span/text()").extract()[0]
        cholesterolContent = response.xpath("//div[@class='recipe-nutrition__form']//ul[@class='nutrientLine']//li[@itemprop='cholesterolContent']/span/text()").extract()[0]
        sodiumContent = response.xpath("//div[@class='recipe-nutrition__form']//ul[@class='nutrientLine']//li[@itemprop='sodiumContent']/span/text()").extract()[0]

        nutrition=[]
        nutrition_info = {
            'Calories': calories,
            'Fat': fat,
            'CarbohydrateContent': carbohydrateContent,
            'ProteinContent': proteinContent,
            'CholesterolContent': cholesterolContent,
            'SodiumContent': sodiumContent
        }

        nutrition.append(nutrition_info)

        if review_count > 2 and average_rating > 4:
            product['Title'] = title
            product['Average_rating'] = average_rating
            product['Review_count'] = review_count
            product['Categories'] = categories
            product['Step'] = step
            product['Nutrition'] = nutrition

            if ingredients < 6 and preptime < 60:
                product['Ingredients'] = ingredients
                product['Preptime'] = preptime

        return product

    def _clean_text(self, text):
        text = text.replace("\n", " ").replace("\t", " ").replace("\r", " ")
        text = re.sub("&nbsp;", " ", text).strip()

        return re.sub(r'\s+', ' ', text)