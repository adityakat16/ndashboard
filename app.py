from flask import Flask, request, render_template
from scraper import get_stock_data

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    if request.method == "POST":
        code = request.form.get("code", "").upper()
        result = get_stock_data(code)
    return render_template("index.html", result=result)
