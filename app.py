from flask import Flask, render_template, request
from sele import run_scraper

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    data = None
    if request.method == "POST":
        stock = request.form["stock"]
        data = run_scraper(stock)
    return render_template("result.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)
