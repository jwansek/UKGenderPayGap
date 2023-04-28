import database
import flask

app = flask.Flask(__name__)

@app.route("/")
def serve_index():
    return flask.render_template(
        "index.html.j2",
        title = "UK Gender Pay Gap"
    )

if __name__ == "__main__":
    app.run("0.0.0.0", port = 5005, debug = True)