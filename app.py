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


if __name__ == "__main__":
    app.run(debug=True)