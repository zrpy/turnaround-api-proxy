import time
import random

class Solver:
    async def __init__(self, playwright, proxy="", headless=True):
        self.playwright = playwright
        self.proxy = proxy
        self.headless = headless

        await self.start_browser(self.playwright)
            
    async def terminate(self):
        await self.browser.close()

    def build_page_data(self):
        # this builds a custom page with the sitekey so we do not have to load the actual page, taking less bandwidth
        with open("utils/page.html") as f:
            self.page_data = f.read()
        stub = f"<div class=\"cf-turnstile\" data-sitekey=\"{self.sitekey}\"></div>"
        self.page_data = self.page_data.replace("<!-- cf turnstile -->", stub)

    def get_mouse_path(self, x1, y1, x2, y2):
        # calculate the path to x2 and y2 from x1 and y1
        path = []
        x = x1
        y = y1
        while abs(x - x2) > 3 or abs(y - y2) > 3:
            diff = abs(x - x2) + abs(y - y2)
            speed = random.randint(1, 2)
            if diff < 20:
                speed = random.randint(1, 3)
            else:
                speed *= diff / 45

            if abs(x - x2) > 3:
                if x < x2:
                    x += speed
                elif x > x2:
                    x -= speed
            if abs(y - y2) > 3:
                if y < y2:
                    y += speed
                elif y > y2:
                    y -= speed
            path.append((x, y))

        return path

    async def move_to(self, x, y):
        for path in self.get_mouse_path(self.current_x, self.current_y, x, y):
            await self.page.mouse.move(path[0], path[1])
            if random.randint(0, 100) > 15:
                time.sleep(random.randint(1, 5) / random.randint(400, 600))

    async def solve_invisible(self):
        iterations = 0

        while iterations < 10:
            self.random_x = random.randint(0, self.window_width)
            self.random_y = random.randint(0, self.window_height)
            iterations += 1

            self.move_to(self.random_x, self.random_y)
            self.current_x = self.random_x
            self.current_y = self.random_y
            elem = await self.page.query_selector("[name=cf-turnstile-response]")
            if await  elem:
                if await elem.get_attribute("value"):
                    return await elem.get_attribute("value")
            time.sleep(random.randint(2, 5) / random.randint(400, 600))
        return "failed"
            

    async def solve_visible(self):
     
        iframe = await self.page.query_selector("iframe")
        while not iframe:
            iframe = await self.page.query_selector("iframe")
            time.sleep(0.1)
        while not iframe.bounding_box():
            time.sleep(0.1)

        x = iframe.bounding_box()["x"] + random.randint(5, 12)
        y = iframe.bounding_box()["y"] + random.randint(5, 12)
        self.move_to(x, y)
        self.current_x = x
        self.current_y = y
        framepage = await iframe.content_frame()
        checkbox = await framepage.query_selector("input")

        while not checkbox:
            checkbox = await framepage.query_selector("input")
            time.sleep(0.1)

        width = checkbox.bounding_box()["width"]
        height = checkbox.bounding_box()["height"]

        x = checkbox.bounding_box()["x"] + width / 5 + random.randint(int(width / 5), int(width - width / 5))
        y = checkbox.bounding_box()["y"] + height / 5 + random.randint(int(height / 5), int(height - height / 5))

        await self.move_to(x, y)

        self.current_x = x
        self.current_y = y
        

        time.sleep(random.randint(1, 5) / random.randint(400, 600))
        await self.page.mouse.click(x, y)

        iterations = 0

        while iterations < 10:
            self.random_x = random.randint(0, self.window_width)
            self.random_y = random.randint(0, self.window_height)
            iterations += 1

            self.move_to(self.random_x, self.random_y)
            self.current_x = self.random_x
            self.current_y = self.random_y
            elem = await self.page.query_selector("[name=cf-turnstile-response]")
            if elem:
                if await elem.get_attribute("value"):
                    return await elem.get_attribute("value")
            time.sleep(random.randint(2, 5) / random.randint(400, 600))
        return "failed"


    
    async def solve(self, url, sitekey, invisible=False):
        self.url = url + "/" if not url.endswith("/") else url
        self.sitekey = sitekey
        self.invisible = invisible
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

        self.build_page_data()
        
        await self.page.route(self.url, lambda route: route.fulfill(body=self.page_data, status=200))
        await self.page.goto(self.url)
        output = "failed"
        self.current_x = 0
        self.current_y = 0

        self.window_width = await self.page.evaluate("window.innerWidth")
        self.window_height = await self.page.evaluate("window.innerHeight")
        if self.invisible:
            output = await self.solve_invisible()
        else:
            output = await self.solve_visible()
        
        await self.context.close()
        return output

    async def start_browser(self, playwright):

        if self.proxy:
            self.browser = await playwright.firefox.launch(headless=self.headless, proxy={
                "server": "http://" + self.proxy.split("@")[1],
                "username": self.proxy.split("@")[0].split(":")[0],
                "password": self.proxy.split("@")[0].split(":")[1]
            })
        else:
            self.browser = await playwright.firefox.launch(headless=self.headless)

