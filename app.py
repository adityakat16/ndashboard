import subprocess
import os

# Install Chrome and Chromedriver
subprocess.run("apt-get update", shell=True)
subprocess.run("apt-get install -y wget unzip curl gnupg", shell=True)
subprocess.run("wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb", shell=True)
subprocess.run("apt install -y ./google-chrome-stable_current_amd64.deb", shell=True)
subprocess.run("rm google-chrome-stable_current_amd64.deb", shell=True)

# Get Chrome version and match chromedriver
chrome_version = subprocess.check_output("google-chrome --version", shell=True).decode()
chrome_version_main = ".".join(chrome_version.strip().split(" ")[-1].split(".")[:3])
chromedriver_version = subprocess.check_output(f"curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{chrome_version_main}", shell=True).decode().strip()
subprocess.run(f"wget -O chromedriver.zip https://chromedriver.storage.googleapis.com/{chromedriver_version}/chromedriver_linux64.zip", shell=True)
subprocess.run("unzip chromedriver.zip", shell=True)
subprocess.run("mv chromedriver /usr/local/bin/chromedriver", shell=True)
subprocess.run("chmod +x /usr/local/bin/chromedriver", shell=True)
subprocess.run("rm chromedriver.zip", shell=True)

print("✅ Chrome & Chromedriver setup done!")

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
