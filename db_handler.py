from flask import Flask, render_template, g
import sqlite3

app = Flask(__name__)
DATABASE = "crawler_data.db"

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/directories")
def directories():
    db = get_db()
    data = db.execute("SELECT * FROM directories").fetchall()
    return render_template("data.html", title="Directories", data=data, columns=["Domain", "Directory"])

@app.route("/files")
def files():
    db = get_db()
    data = db.execute("SELECT * FROM files").fetchall()
    return render_template("data.html", title="Files", data=data, columns=["Domain", "URL", "Type"])

@app.route("/links")
def links():
    db = get_db()
    data = db.execute("SELECT * FROM links").fetchall()
    return render_template("data.html", title="Links", data=data, columns=["Domain", "URL"])

@app.route("/emails")
def emails():
    db = get_db()
    data = db.execute("SELECT * FROM emails").fetchall()
    return render_template("data.html", title="Emails", data=data, columns=["Domain", "Email"])

@app.route("/cookies")
def cookies():
    db = get_db()
    data = db.execute("SELECT * FROM cookies").fetchall()
    return render_template("data.html", title="Cookies", data=data, columns=["Domain", "URL", "Cookies"])

@app.route("/ip_addresses")
def ip_addresses():
    db = get_db()
    data = db.execute("SELECT * FROM ip_addresses").fetchall()
    return render_template("data.html", title="IP Addresses", data=data, columns=["Domain", "IP Address"])

@app.route("/api_endpoints")
def api_endpoints():
    db = get_db()
    data = db.execute("SELECT * FROM api_endpoints").fetchall()
    return render_template("data.html", title="API Endpoints", data=data, columns=["Domain", "URL", "Response Type"])

# Additional Routes for New Features
@app.route("/phone_numbers")
def phone_numbers():
    db = get_db()
    data = db.execute("SELECT * FROM phone_numbers").fetchall()
    return render_template("data.html", title="Phone Numbers", data=data, columns=["Domain", "Phone Number"])

@app.route("/physical_addresses")
def physical_addresses():
    db = get_db()
    data = db.execute("SELECT * FROM physical_addresses").fetchall()
    return render_template("data.html", title="Physical Addresses", data=data, columns=["Domain", "Address"])

@app.route("/social_media_urls")
def social_media_urls():
    db = get_db()
    data = db.execute("SELECT * FROM social_media_urls").fetchall()
    return render_template("data.html", title="Social Media URLs", data=data, columns=["Domain", "URL"])

@app.route("/social_media_handles")
def social_media_handles():
    db = get_db()
    data = db.execute("SELECT * FROM social_media_handles").fetchall()
    return render_template("data.html", title="Social Media Handles", data=data, columns=["Domain", "Handle"])

@app.route("/ga_tracking_ids")
def ga_tracking_ids():
    db = get_db()
    data = db.execute("SELECT * FROM ga_tracking_ids").fetchall()
    return render_template("data.html", title="Google Analytics Tracking IDs", data=data, columns=["Domain", "Tracking ID"])

if __name__ == "__main__":
    app.run(debug=True)
