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

with open(os.path.join(os.path.dirname(__file__), "static", "ukcounties.json"), "r") as f:
    UK_GEOJSON = json.load(f)

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
    res = dict(flask.request.form)
    for k, v in res.items():
        if k == "allyears":
            continue
        if k == "yearslider":
            with database.PayGapDatabase(host = host) as db:
                new_args["year"] = db.get_years()[int(v) - 1]
        elif v != "No filter":
            new_args[k] = v

    
    if "allyears" in res.keys():
        if res["allyears"] == "allyears":
            del new_args["year"]

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

@app.route("/api/sic_sec")
def api_get_sic_section_pay():
    pay_type = flask.request.args.get("Pay Type")
    year = flask.request.args.get("year")
    # print("year: '%s'" % year)
    if pay_type is None or pay_type.lower() not in {'hourly', 'bonuses'}:
        return flask.abort(400, "The key `pay type` must be equal to 'hourly' or 'bonuses'")
    with database.PayGapDatabase(host = host) as db:
        if year is not None:
            if year not in db.get_years():
                return flask.abort(400, "Unrecognised year '%s'. The year option must be in %s" % (year, ", ".join(db.get_years())))
        
        return flask.jsonify(db.get_pay_by_sic_section(pay_type, year))

@app.route("/api/heatmap")
def api_get_heatmap_data():
    # pay_type = flask.request.args.get("Pay Type")
    year = flask.request.args.get("year")
    # print("year: '%s'" % year)
    # if pay_type is None or pay_type.lower() not in {'hourly', 'bonuses'}:
    #     return flask.abort(400, "The key `pay type` must be equal to 'hourly' or 'bonuses'")
    with database.PayGapDatabase(host = host) as db:
        if year is not None:
            if year not in db.get_years():
                return flask.abort(400, "Unrecognised year '%s'. The year option must be in %s" % (year, ", ".join(db.get_years())))
        
        return flask.jsonify(db.get_heatmap_data("hourly", year))

@app.route("/api/getyears")
def api_get_year_options():
    with database.PayGapDatabase(host = host) as db:
        return flask.jsonify(db.get_years())

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
        # print(i["url"], url)
        # if i["url"] == url:
        #     return i
        if url.startswith(i["url"]):
            return i

def get_chart_elem_strict(url):
    for i in get_charts()["index"]:
        print(urllib.parse.urlsplit(i["url"]).path, urllib.parse.urlsplit(url).path)
        if urllib.parse.urlsplit(i["url"]).path == urllib.parse.urlsplit(url).path:
            return i

@app.route("/plot/<name>")
def serve_large_plot(name):
    with database.PayGapDatabase(host = host) as db:
        # print(flask.request.full_path)
        elem = get_chart_elem(flask.request.full_path)
        # if elem is None:
        #     elem = get_chart_elem_strict(flask.request.full_path)
        filters = elem["filters"]
        for k, v in filters.items():
            if v == "<SICType>":
                filters[k] = {"options": db.get_sic_sections()}
            if v == "<CompanyType>":
                filters[k] = {"options": db.get_company_types()}
            if v == "<CompanySize>":
                 filters[k] = {"options": db.get_company_sizes()}
            if v == "<Years>":
                filters[k] = {"yearslider": db.get_years()}

    elem["url"] = flask.request.full_path
    # print("elem", elem)
    current_filters = dict(flask.request.args)
    print("filters", filters)
    print("current_filters", current_filters)
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