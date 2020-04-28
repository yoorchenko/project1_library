from flask import Flask, render_template, request, session, redirect, url_for, jsonify, abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import os
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"
engine = create_engine("postgres://bvxeiqwrisgnhi:7e05d17ad0f586681c5a8fe60a9ca6c79edbeadaaca0e7ff303a5eb1cd2f358a@ec2-54-228-250-82.eu-west-1.compute.amazonaws.com:5432/d5ehk879u4m6ut")
db = scoped_session(sessionmaker(bind=engine))

#app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = 'filesystem'
Session(app)



KEY = "St1qqMHasj3HJ9ArKwuA"

@app.route("/", methods = ["POST", "GET"])
def index():
    if not session.get("log"):
        session["log"] = False
    if session["log"] == True:
        if request.method == "POST":
            searchparam = request.form.get("searchparam")
            query = request.form.get("query")
            #print('a'+query+'a')
            if searchparam and query:
                query = f"%{query}%"
                results = db.execute(f"SELECT * FROM books WHERE {searchparam} LIKE :query", {"query":query, "searchparam":searchparam}).fetchall()
                if results:
                    return render_template("test_result.html", results=results)
                else:
                    return render_template("error.html", message="No Results!")
            else:
                return render_template("error.html", message="Submit The Form")

        return render_template("test_homepage.html")
    else:
        return redirect(url_for('login'))


@app.route("/detail/<int:id>", methods = ["POST", "GET"])
def detail(id):

    if session["log"] == False:
        return "Please, log in!"

    if request.method == "POST":
        new_review = request.form.get("newreview")
        rating = request.form.get("rate")
        rating = int(rating)
        if new_review:
            db.execute("INSERT INTO reviews(text, rating, book_id, user_id) VALUES(:text, :rating, :book_id, :user_id)", {"text":new_review, "rating":rating, "book_id":id, "user_id":session["id"]})
            db.commit()

    reviewed=True
    if db.execute("SELECT * FROM reviews WHERE user_id=:user_id AND book_id=:id", {"user_id":session["id"], "id":id}).fetchone() is None:
        reviewed=False
        print(db.execute("SELECT * FROM reviews WHERE user_id=:user_id", {"user_id":session["id"]}).fetchone())
    book = db.execute("SELECT * FROM books WHERE id=:id", {"id":id}).fetchone()
    try:
        result = requests.get("https://www.goodreads.com/book/review_counts.json", {"key": KEY, "isbns": book.isbn})
        result = result.json()
        average_rating = result["books"][0]["average_rating"]
        reviews_count = result["books"][0]["reviews_count"]
    except:
        average_rating = 0
        reviews_count = 0
    reviews = db.execute("SELECT * FROM books JOIN reviews ON books.id=book_id JOIN users ON users.id=user_id WHERE books.id=:id;", {"id":book.id}).fetchall()
    #return render_template("detail.html", book=book, reviews=reviews, reviewed=reviewed, average_rating=average_rating, reviews_count=reviews_count)
    return render_template("test_book.html", book=book, average_rating=average_rating, reviews_count=reviews_count, reviews=reviews, reviewed=reviewed)



@app.route("/signup", methods = ["POST", "GET"])
def signup():

    if request.method == "GET":
        return render_template("register.html")

    elif request.method == "POST":
        login = request.form.get("login")
        password = request.form.get("password")
        password2 = request.form.get("password2")
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")

        if (login and password and firstname and lastname and password==password2 and len(password)>7):
            try:
                db.execute("INSERT INTO users(login, password, firstname, lastname) VALUES(:login, :password, :firstname, :lastname)",
                           {"login":login, "password":password, "firstname":firstname, "lastname":lastname})
                db.commit()
            except:
                return render_template("register.html", wrong=True)

            return redirect(url_for('login'))

    return render_template("register.html", wrong=True)


@app.route("/login", methods = ["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("login1.html", session=session)

    if request.method == "POST":
        login = request.form.get("login")
        password = request.form.get("password")

        if (login and password):
            user = db.execute("SELECT * FROM users WHERE login=:login AND password=:password", {"login":login, "password": password}).fetchone()

            if user:
                session["log"] = True
                session["id"] = user.id
                session["firstname"] = user.firstname
                session["lastname"] = user.lastname
                return redirect(url_for('index'))

            session["log"] = False
        return render_template("login1.html", wrong=True)

@app.route("/logout")
def logout():
    session["log"] = False
    session["firstname"] = None
    session["lastname"] = None
    return redirect(url_for('index'))


@app.route("/api/<isbn>")
def api(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn":isbn}).fetchone()
    if book:
        try:
            result = requests.get("https://www.goodreads.com/book/review_counts.json", {"key": KEY, "isbns": isbn})
            result = result.json()
            average_rating = result["books"][0]["average_rating"]
            reviews_count = result["books"][0]["reviews_count"]
        except:
            average_rating = 0
            reviews_count = 0
        return jsonify({
            "title":book.title,
            "author":book.author,
            "year":book.year,
            "review_count":reviews_count,
            "average_rating":average_rating
        })
    else:
        abort(404)

#url("/static/img/test_result.jpg");