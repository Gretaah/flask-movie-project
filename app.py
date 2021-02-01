import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, 
    url_for, abort, Blueprint, Response,)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm, SearchForm
from error_handlers import error_handlers
from movie_search import movie_search
from database import mongo
if os.path.exists("env.py"):
    import env

app = Flask(__name__)

# Blueprint for error_handlers.py
app.register_blueprint(error_handlers, url_prefix="/error/")

# Blueprint for the movie database 
app.register_blueprint(movie_search)

# Blueprint for the movie database
app.register_blueprint(database)

# Database access 
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

# Route for the base template
@app.route("/")
def base():
    return render_template("base.html")


# Route for home 
@app.route("/home")
def home():
    return render_template("home.html")



# Route for user registration
@app.route("/register", methods=["POST", "GET"])
def register():
    # Registration form from forms.py
    form = RegistrationForm()
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        # Warn if the user already exists
        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))
        # What to send to database 
        register = {
            "email": request.form.get("email").lower(),
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # Put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))
    
    return render_template("register.html", title="register", form=form)


# Route for user Login
@app.route("/login", methods=["POST", "GET"])
def login():
    # Login form from forms.py
    form = LoginForm()
    if request.method == "POST":
        # Check if the username exists in the database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        # Check if the email exists in the database
        existing_email = mongo.db.users.find_one(
            {"email": request.form.get("email")})

        if existing_user:
            # Check if the hashed password match
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect(url_for(
                            "profile", username=session["user"]))
            
            else:
                # Invalid username or password
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

    return render_template("login.html", title="login", form=form)


# Route for user profile 
@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"].capitalize()
    # Render user profile if there's a session cookie 
    if session["user"]:
        return render_template("profile.html", username=username, title="profile")
    # Otherwise redirect to login page
    return redirect(url_for("login"))


# User Logout
@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))



if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)

