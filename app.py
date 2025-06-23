from flask import Flask, render_template, request
from sele import run_scraper

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    if request.method == "POST":
        query = request.form.get("query", "")
        result = run_scraper(query)
    return render_template("index.html", data=result)

if __name__ == "__main__":
    app.run(debug=True)
