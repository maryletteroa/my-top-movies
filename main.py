from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, FloatField, StringField, IntegerField, PasswordField
from wtforms.validators import DataRequired
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("APP_SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/movies.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
Bootstrap(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer)
    description = db.Column(db.Text)
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String)
    img_url = db.Column(db.String)

class MovieForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

class EditForm(FlaskForm):
    rating = FloatField("Your Rating Out of 10 e.g. 7.5", validators=[DataRequired()])
    review = TextAreaField("Your Review")
    submit = SubmitField("Done")

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    login = SubmitField("Login")

db.create_all()

@app.route("/")
def home():
    movies = Movie.query.order_by(Movie.rating).all()
    for i, movie in enumerate(movies[::-1]):
        movie.ranking = i+1
    movies = Movie.query.order_by(Movie.ranking).all()
    return render_template("index.html", movies=movies)

@app.route("/edit/<id>", methods=["GET", "POST"])
def edit(id):
    form = EditForm()
    movie_to_update = Movie.query.get(id)
    if form.validate_on_submit():
        if request.method == "POST":
            movie_to_update.rating = form.rating.data
            movie_to_update.review = form.review.data
            db.session.commit()
            return redirect(url_for("home"))
    return render_template("edit.html", form=form, movie=movie_to_update)

@app.route("/delete")
def delete():
    id = request.args.get("id")
    movie_to_delete = Movie.query.get(id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/select", methods=["GET", "POST"])
def select():
    form = MovieForm()
    if form.validate_on_submit():
        if request.method == "POST":
            url = "https://api.themoviedb.org/3/search/movie"
            query = {
                "api_key": os.environ.get("TMDB_API"),
                "query": form.title.data
            }
            response = requests.get(url,params=query)
            response.raise_for_status()
            results = response.json()["results"]
            movies = [{"movie_id": result["id"], "title": result["title"], "date": result["release_date"]} \
                if "release_date" in result else {"movie_id": result["id"], "title": result["title"], "date": ""} \
                for result in results]
            return render_template("select.html", movies=movies)
    return render_template("add.html", form = form)

@app.route("/add")
def add():
    movie_id = request.args.get("movie_id")
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    query = {
        "api_key": os.environ.get("TMDB_API"),
    }
    response = requests.get(url,params=query)
    response.raise_for_status()
    movie_details = response.json()
    new_movie = Movie(
        title = movie_details["title"],
        year = movie_details["release_date"].split("_")[0],
        description = movie_details["overview"],
        img_url = f"https://image.tmdb.org/t/p/w500{movie_details['poster_path']}",
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit', id=new_movie.id))

if __name__ == '__main__':
    app.run(debug=True)
