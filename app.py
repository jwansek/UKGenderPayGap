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
    return flask.render_template(
        "index.html.j2",
        title = "UK Gender Pay Gap",
        charts = get_charts()["index"]
    )

def get_charts():
    with open("charts.json", "r") as f:
        return json.load(f)

@app.route("/api/charts.json")
def serve_charts():
    return flask.jsonify(get_charts())


@app.route("/search_click", methods = ["POST"])
def search_redirect():
    return flask.redirect("/search?s=%s" % urllib.parse.quote_plus(dict(flask.request.form)["search"]))

@app.route("/plot/<name>/apply_click", methods = ["POST"])
def apply_redirect(name):
    new_args = {}
    for k, v in flask.request.form.items():
        if v != "No filter":
            new_args[k] = v

    # print("/" + "/".join(flask.request.full_path.split("/")[1:-1]) + "?" + urllib.parse.urlencode(new_args))
    return flask.redirect("/" + "/".join(flask.request.full_path.split("/")[1:-1]) + "?" + urllib.parse.urlencode(new_args))

@app.route("/api/years")
def api_get_years():
    pay_type = flask.request.args.get("Pay Type")
    sic_type = flask.request.args.get("SIC Type")
    employer_type = flask.request.args.get("Employer Type")
    employer_size = flask.request.args.get("Employer Size")
    # print("sic_type", sic_type)
    # print("employer_type", employer_type)
    # print("employer_size", employer_size)
    if pay_type is None or pay_type.lower() not in {'hourly', 'bonuses'}:
        return flask.abort(400, "The key `pay type` must be equal to 'hourly' or 'bonuses'")
    with database.PayGapDatabase(host = host) as db:
        return flask.jsonify(db.get_pay_by_year(pay_type, sic_section_name = sic_type, employer_size = employer_size, employer_type = employer_type))

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

def get_chart_elem(url):
    for i in get_charts()["index"]:
        print(i["url"], url)
        # if i["url"] == url:
        #     return i
        if url.startswith(i["url"]):
            return i

@app.route("/plot/<name>")
def serve_large_plot(name):
    with database.PayGapDatabase(host = host) as db:
        # print(flask.request.full_path)
        elem = get_chart_elem(flask.request.full_path)
        filters = elem["filters"]
        for k, v in filters.items():
            if v == "<SICType>":
                filters[k] = {"options": db.get_sic_sections()}
            if v == "<CompanyType>":
                filters[k] = {"options": db.get_company_types()}
            if v == "<CompanySize>":
                 filters[k] = {"options": db.get_company_sizes()}

    elem["url"] = flask.request.full_path
    # print("elem", elem)
    current_filters = dict(flask.request.args)
    # print("current_filters", current_filters)
    return flask.render_template(
        "plot.html.j2",
        title = elem["title"],
        elem = elem,
        alt = "Lorem ipsum.",
        filters = filters,
        current_filters = current_filters,
        len = len
    )

if __name__ == "__main__":
    app.run("0.0.0.0", port = 5005, debug = True)