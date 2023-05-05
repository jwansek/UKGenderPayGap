import database
import urllib.parse
import flask
import json
import os

app = flask.Flask(__name__)

if not os.path.exists(".docker"):
    import dotenv
    dotenv.load_dotenv(dotenv_path = "db.env")
    host = "srv.home"
else:
    host = "db" 

@app.route("/")
def serve_index():
    with open("charts.json", "r") as f:
        charts = json.load(f)

    return flask.render_template(
        "index.html.j2",
        title = "UK Gender Pay Gap",
        charts = charts["index"]
    )

@app.route("/search_click", methods = ["POST"])
def search_redirect():
    return flask.redirect("/search?s=%s" % urllib.parse.quote_plus(dict(flask.request.form)["search"]))

@app.route("/search")
def search():
    with database.PayGapDatabase(host = host) as db:
        search_text = flask.request.args.get("s")
        companies = db.search_company(search_text)
        if len(companies) == 1:
            return flask.redirect("/company/%s" % companies[0][1])

        return flask.render_template(
            "search.html.j2",
            title = "Search",
            companies = companies
        )

if __name__ == "__main__":
    app.run("0.0.0.0", port = 5005, debug = True)