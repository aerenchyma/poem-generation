import poetry_original
import os, json
from flask import Flask, render_template, url_for, redirect, session, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging

# TODO: add static file as necessary
# Static files CSS
# @route('/static/css/<filename:re:.*\.css>')
# def send_css(filename):
#     return static_file(filename, root='static/css')

# App config
app = Flask(__name__)
app.debug = True
app.use_reloader = True
# TODO set up safe config
app.static_folder = 'static'
app.config['SECRET_KEY'] = 'adgsdfsadfdflsdfsj'
app.config['HEROKU_ON'] = os.environ.get('HEROKU')

# TODO: configure db stuff / add safe config
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or "postgresql://localhost/poetry_data"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Set up db and debug stuff
db = SQLAlchemy(app)
migrate = Migrate(app) 
session = db.session 


# Models

class CorpusLine(db.Model):
    __tablename__ = "lines"
    id = db.Column(db.Integer, primary_key=True)
    line = db.Column(db.Text) # Text containing JSON objects, I am very lazy

# TODO; store/permalink the poems??? tbd

# Set up database if necessary

# def db_setup(): # TODO: redo so that we don't have to do the whole lines thing in generating a poem...
#     """Assuming db has been created with CorpusLine model, 
#     fill CorpusLine table with lines from cited corpus"""
#     all_lines = generate_poetry_corpus_lines()
#     for l in all_lines:
#         # Make the dictionary a string
#         l = json.dumps(l) # lol ugh
#         item = CorpusLine(line=l)
#         session.add(item)
#         # session.commit() 
#     session.commit() # TODO: is that too much to add at once? prob fine, check
def db_setup():
    """Assuming db has been created with CorpusLine model,
    and a poetry_corpus_text.txt file exists, 
    fill CorpusLine table with lines from cited corpus"""
    f = open("poetry_corpus_text.txt",'r')
    lines = f.readlines()
    f.close()
    for l in lines:
        item = CorpusLine(line=l)
        session.add(item)
    session.commit()

def create_poem(word, lines):
    p = poetry_original.Poem(seed_word=word, lines=lines)
    return p


# Forms

# just example lol
# class SongForm(FlaskForm):
#     song = StringField("What is the title of your favorite song?", validators=[Required()])
#     artist = StringField("What is the name of the artist who performs it?",validators=[Required()])
#     genre = StringField("What is the genre of that song?", validators
#         =[Required()])
#     album = StringField("What is the album this song is on?", validators
#         =[Required()])
#     rating = FloatField("What is your rating of this song?", validators = [Required()])
#     submit = SubmitField('Submit')

class WordForm(FlaskForm):
    seed_word = StringField("Input a word to inspire the poem generator. No spaces or punctuation; unfortunately, it doesn't find those inspirational.", validators=[DataRequired()])
    submit = SubmitField("Create a poem")



# Routes

# @get('/') 
# def poem():
#     """Home page, form to give the poem creator some inspiration."""
#     return template('templates/home.html')

@app.route('/',methods=["GET","POST"])
def index():
    form = WordForm()
    if request.method == "POST":
        # get result from form
        word = form.seed_word.data
        logging.warning("word input is", word)
        print("! print that word input is", word)
        lines = [x.line for x in CorpusLine.query.all()]
        # generate poem and store
        p = create_poem(word=word, lines=lines) # TODO make this a diff thread or background task?
        logging.warning("created poem successfully")
        print("! print that poem was created successfully")
        # get site-rep of poem, awk but i'm lazy
        poem_rep = p.poem_site_rep()
        logging.warning("poem rep:", poem_rep)
        poem_title = p.generate_title()
        # render poem
        return render_template('poem.html',poem_text=poem_rep, poem_title=poem_title, form=form)
        # TODO? save poem and whatever (later)
    else:
        return render_template('home.html',form=form) 



# Error handling

# TODO


# Main

if __name__ == '__main__':
    # db.create_all() # TODO check ok
    # If the created database is empty, then fill it with the lines stuff
    # if not CorpusLine.query.all(): # assuming no contents is falsey, TODO check
    #     db_setup() # This should only run locally, and then put db on server
    # else:
    #     print("Yes, there is content in the LINES table / CorpusLine model!")

    # if app.config['HEROKU_ON']: # TODO change this env var for any server
    #     app.debug = False
    #     # run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000))) # TODO ensure right for flask
    #     app.run()
    # else:
    app.debug = False # for now
    # run(host='localhost', port=8080, debug=True) # TODO ensure right for Flask
    app.run()


####

# TODO: 

# work on ensuring a poem can load online
# tbd on using db to permalink (??? careful re: permalink)

# host on heroku w flask (see instrs above)