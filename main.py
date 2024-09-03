import playwright.sync_api
import flask
import json
import time
from utils import solver
app = flask.Flask(__name__)


@app.route("/")
async def index():
    return flask.redirect("https://github.com/zrpy/turnaround-api-proxy")

@app.route("/solve", methods=["POST"])
async def solve():
    json_data = flask.request.json
    sitekey = json_data["sitekey"]
    invisible = json_data["invisible"]
    url = json_data["url"]
    proxy = json_data.get("proxy","")
    async with playwright.async_api.async_playwright() as p:
        s = await solver.Solver(p,proxy=proxy,headless=True)
        token = await s.solve(url, sitekey, invisible)
        await s.terminate()
        return (await make_response(token))

async def make_response(captcha_key):
    if captcha_key == "failed":
        return flask.jsonify({"status": "error", "token": None})
    return flask.jsonify({"status": "success", "token": captcha_key})

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=443,threaded=True,debug=False)
