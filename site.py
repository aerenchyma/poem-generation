# from bottle import route, run, get, post, request, error, template, static_file
from poetry import Poem, generate_poetry_corpus_lines
import os, json
from flask import Flask, render_template, url_for, redirect, session, flash, request
from flask_wtf import FlaskForm # todo install, pipfile etc
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate# , MigrateCommand

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
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or "postgresql://localhost/corpus_data"
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

def db_setup(): # TODO: redo so that we don't have to do the whole lines thing in generating a poem...
    """Assuming db has been created with CorpusLine model, 
    fill CorpusLine table with lines from cited corpus"""
    all_lines = generate_poetry_corpus_lines()
    for l in all_lines:
        # Make the dictionary a string
        l = json.dumps(l) # lol ugh
        item = CorpusLine(line=l)
        session.add(item)
        # session.commit() 
    session.commit() # TODO: is that too much to add at once? prob fine, check


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
        # print("validated")
        word = form.seed_word.data
        # word = request.get("seed_word")
        print(word, "!got")
        # get lines from db
        lines = CorpusLine.query.all()
        # generate poem and store
        p = Poem(seed_word=word,lines_source=lines)
        # get site-rep of poem, awk but i'm lazy
        poem_rep = p.poem_site_rep()
        # render poem
        return render_template('poem.html',poem_text=poem_rep, form=form)
        # TODO? save poem and whatever (later)
    else:
        return render_template('home.html',form=form) 



####### fully unflasked

# @post('/') # https://buxty.com/b/2013/12/jinja2-templates-and-bottle/
# def generate_poem():
#     """Post and generate poem."""
#     source_word = request.forms.get('source_word')
#     # TODO deal with input lines from db or st
#     p = Poem(source_word)
#     p.generate_poem()
#     info = {'poem_text':p.full_poem_list, 'poem_title':p.title}
#     return template('templates/poem.html', info)

# @app.route('')


# Error handling

# TODO convert to flask
# @error(500)
# def error500(error):
#     return template('templates/500.html')


# Main

if __name__ == '__main__':
    db.create_all() # TODO check ok
    # If the created database is empty, then fill it with the lines stuff
    if not CorpusLine.query.all(): # assuming no contents is falsey, TODO check
        db_setup()

    if app.config['HEROKU_ON']:
        app.debug = False
        # run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000))) # TODO ensure right for flask
        app.run()
    else:
        app.debug = True 
        # run(host='localhost', port=8080, debug=True) # TODO ensure right for Flask
        app.run()



####

# TODO: 
# convert to flask, ex https://github.com/SI508-F18/Songs-App-Class-Example/blob/master/main_app.py
# set up for heroku but on flask, eg instrs https://paper.dropbox.com/doc/SI364-Discussion-Section-12-March-26-27-Flask-App-Deployment-on-Heroku--BJwS8cvj~~NgLY2P4NUtpV_VAg-ISMz9JOz4mgwHmg8mbLRJ

# make some edits:

# open corpus and store in db to create all (hmm)
# use db to access data? (TBD)
# tbd on using db to permalink (??? careful re: permalink)

# host on heroku w flask (see instrs above)