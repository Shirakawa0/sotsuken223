from flask import Flask, render_template
import random, string

app = Flask(__name__)
app.secret_key = "".join(random.choices(string.ascii_letters, k=256))

@app.route("/u_login")
def u_login_page():
    return render_template("u_login.html")

@app.route("/signup2")
def signup2_page():
    return render_template("signup_2.html")

@app.route("/signup")
def signup_page():
    return render_template("signup.html")

@app.route("/aaa")
def aaa_page():
    return render_template("aaa_2.html")


@app.route("/test")
def test():
    return

if __name__ == "__main__":
    app.run(debug=True)