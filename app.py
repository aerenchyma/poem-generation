# import poetry_original
import os, json
from flask import Flask, render_template, url_for, redirect, session, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
import random
from sqlalchemy import func

# Poem-specific imports
import gzip, json
import re
import pronouncing
from collections import defaultdict
from typing import List

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

uri = os.environ.get("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://")
app.config['SQLALCHEMY_DATABASE_URI'] = uri or "postgresql://localhost/poetry_data"
# app.config['SQLALCHEMY_DATABASE_URI'] = uri
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

# TODO: store the words that are searched? maybe maybe not

# Set up database if necessary
# def db_setup_lines():
#     """Assuming db has been created with CorpusLine model,
#     and a poetry_corpus_text.txt file exists, 
#     fill CorpusLine table with lines from cited corpus"""
#     f = open("poetry_corpus_text.txt",'r')
#     lines = f.readlines()
#     f.close()
#     for l in lines:
#         item = CorpusLine(line=l)
#         session.add(item)
#     session.commit()

### Support code for poem creation

def random_line_from_db(model):
    """Expects model to have element line -> a string"""
    r_line = model.query.order_by(func.random()).first()
    return r_line

#####
# TODO handle in site
# TODO trace back what happens and account for it
class Poem:
    max_line_choices = [48, 65, 80, 120]
    def __init__(self, seed_word, lines, min_line_len=32, num_lines_sample=25000):
        # self.generate_all_lines()
        self.all_lines = lines#random.sample(lines, num_lines_sample) # get lines list from database, then get random sample of them
        # random_line = random_line_from_db(CorpusLine) # debug
        # print(random_line) # debug
        self.by_rhyming_part = self.generate_rhyming_part_defaultdict(min_line_len,random.choice(self.max_line_choices))
        self.seed_word = seed_word.lower()
        phones = pronouncing.phones_for_word(self.seed_word)[0]
        self.rhyming_part_for_word = pronouncing.rhyming_part(phones)

    def select_relevant_lines(self):
        """Uses heuristics for which lines from corpus we'll need
        to filter lines for input
        TODO: do this in database and not in code?"""
        pass


    def generate_rhyming_part_defaultdict(self, min_len, max_len) -> defaultdict:
        """Returns a default dict structure of 
        keys: Rhyming parts (strs)
        values: defaultdicts,
        of words corresponding to that rhyming part (strs)
        : lists of lines that end with those words (lists of strs)
        Code borrowed directly from Allison Parrish's examples,
        edited a bit for silly website reasons."""
        by_rhyming_part = defaultdict(lambda: defaultdict(list))
        for l in iter(self.all_lines):
            line = l.line
            # Uniform lengths -- original: if not(32 < len(text) < 48)
            if not(min_len < len(line) < max_len): # only use lines of uniform lengths
                continue
            # if line.count(" ") >= 2:
            last_word = line.split()[-1].strip().rstrip()
            pronunciations = pronouncing.phones_for_word(last_word)
            if len(pronunciations) > 0:
                rhyming_part = pronouncing.rhyming_part(pronunciations[0])
                # group by rhyming phones (for rhymes) and words (to avoid duplicate words)
                by_rhyming_part[rhyming_part][last_word.lower()].append(line)
        return by_rhyming_part

    def get_random_line(self) -> str:
        """Returns a random line from the set of all lines"""
        item = random.choice(self.all_lines)
        return item.line
        # ri = random.randint(0,get_count(self.all_lines))
        # return self.all_lines.filter_by(id=ri)
        # For example, a string: "And his nerves thrilled like throbbing violins\n"

    def handle_line_punctuation(self, line, title=False): # Expect line to be a CorpusLine object
        """Handles line-end punctuation for some fun verse finality"""
        line = line.line
        replace_set = ",:;'\"}]{["
        maintain_set = "-!?."
        full_set = replace_set + maintain_set
        if not title:
            if line[-2] in replace_set:
                return line[:-2]+"\n"
            else:
                return line
        else: # if it is a title, replace interim punct and return without end punc
            fixed = line.replace(",","").replace(":","").replace(";","").replace("'","").replace('"','').replace("}","").replace("{","").replace("[","").replace("]","")
            # if fixed[-2] in full_set:
            #     return fixed[:-1]
            return fixed.strip()
        
    def generate_title(self):
        stopwords = ["a","an","the","or","as","of","at","the"] # stopwords that I care about here
        # lines_with_the = [line['s'] for line in self.all_lines if re.search(r"\bthe\b", line['s'], re.I)]
        lines_with_the = CorpusLine.query.filter(CorpusLine.line.contains("the"))#([line for line in self.all_lines if "the" in line.line]
        # print(lines_with_the[1].line)
        random_line_with_the = CorpusLine.query.filter(CorpusLine.line.contains("the")).order_by(func.random()).first()
        title = self.handle_line_punctuation(random_line_with_the, title=True)
        title_list = title.split()
        if title_list[-2] in stopwords and title_list[-1] in stopwords:
            self.title = " ".join(title_list[:-2])
        elif title_list[-1] in stopwords:
            self.title = " ".join(title_list[:-1])
        else:
            self.title = title
        return self.title[:-1] # Ensure there isn't a newline at end of title

    def generate_stanza(self):
        """Generates one poem stanza via complicated/silly rules"""
        # The stanza situation is a bit silly but who cares
        stanza_list = []

        # If there are at least 2 different words to rhyme from this word,
        if len(self.by_rhyming_part[self.rhyming_part_for_word].keys()) >= 2:
            rhyme_options_source = self.by_rhyming_part[self.rhyming_part_for_word]
            rhyming_options = list(rhyme_options_source.keys())
            random.shuffle(rhyming_options) # Don't always have the words that rhyme in the same order in each stanza
            if len(rhyming_options) > 5: # Don't have it do more than 5 rhymes, too many
                # TODO: some randomness in how many per stanza or something???
                rhyming_options = rhyming_options[:5] # Right now needs to be the same number, tbd
            for k in rhyming_options:
                stanza_list.append(random.choice(rhyme_options_source[k]))
            # Then follow with a (random) other line.
            random_line = random_line_from_db(CorpusLine) #self.get_random_line()
            stanza_list.append(self.handle_line_punctuation(random_line))

        # But if there aren't, 
        else:
            # two random couplets; # TODO: decide if there's a more creative thing here
            # followed by a random line with the word in it

            # ### in a world where we only use lines with word or subset of word, don't need this
            # lines_with_word = [line for line in self.all_lines if self.seed_word in line.line]
            lines_with_word = CorpusLine.query.filter(CorpusLine.line.contains(self.seed_word)) # if in app, same in gen_title, but this isn't now
            if lines_with_word == []: # If there aren't any, sure, choose basically any line
                lines_with_word = lines # Grab a list of half the lines that exist TODO more complicated?
            # ######
            # TODO: should do this filter in db, not here, if used
            
            rhyme_groups = [group for group in self.by_rhyming_part.values() if len(group) >= 2]
            # Use Allison's example of grabbing some couplets to grab 2
            for i in range(2):
                group = random.choice(rhyme_groups)
                words = random.sample(list(group.keys()), 2)
                stanza_list.append(random.choice(group[words[0]]))
                stanza_list.append(random.choice(group[words[1]]))
            # Then append a random line with the seed word
            stanza_list.append(self.handle_line_punctuation(random_line_from_db(CorpusLine)))
            # stanza_list.append(self.handle_line_punctuation(CorpusLine.query.filter(CorpusLine.line.contains(self.seed_word)).order_by(func.random()).first()))

        return stanza_list


    def generate_poem(self):

        # TODO clean up all the silly additional newline char concats
        # And maybe add addl checks/options/randomness
        self.generate_title() # For now
    
        self.full_poem = ""

        # Now: controlling len of stanza and such, but always doing 3
        # TODO: input to control how many stanzas, or some element of randomness?
        self.full_poem += "".join(self.generate_stanza())
        self.full_poem += "\n"
        self.full_poem += "".join(self.generate_stanza())
        self.full_poem += "\n"
        self.full_poem += "".join(self.generate_stanza())
        self.full_poem_list = self.full_poem.split("\n")
        return self.full_poem
        # return self.full_poem.split("\n") # debug

    def __str__(self):
        """Returns the string of the poem"""
        return self.generate_poem()

    def poem_site_rep(self):
        """Returns an html-formatted poem string.
        See site.py / self.generate_poem, self.generate_title"""
        self.generate_poem()
        poem_rep = self.full_poem.split("\n")
        self.site_rep_text = poem_rep # list of lines
        return self.site_rep_text
        # return f"<h2><i>{self.title}</i></h2><br><br>{poem_rep}<br><br><a href='/'>Try again</a>" # temp/test


### End support code from poetry_original

def create_poem(word, lines):
    """Use other tooling to create the poem object"""
    p = Poem(seed_word=word, lines=lines)
    return p


# Forms

class WordForm(FlaskForm):
    seed_word = StringField("Input a word to inspire the poem generator. No spaces or punctuation; unfortunately, it doesn't find those inspirational.", validators=[DataRequired()])
    submit = SubmitField("Create a poem")



# Routes

@app.route('/',methods=["GET","POST"])
def index():
    form = WordForm()
    if request.method == "POST":
        # get result from form
        word = form.seed_word.data
        logging.info(f"word input is {word}")
        lines = CorpusLine.query.order_by(func.random()).limit(200000)
        logging.info("lines acquired")
        # generate poem and store
        p = create_poem(word=word, lines=lines) # TODO make this a diff thread or background task?
        logging.info("created poem successfully")
        # get site-rep of poem, awk but i'm lazy
        poem_rep = p.poem_site_rep()
        poem_title = p.generate_title()
        logging.info("poem rep and title generated")
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
    app.debug = True # for now
    # run(host='localhost', port=8080, debug=True) # TODO ensure right for Flask
    app.run()


####

# TODO: 

# work on ensuring a poem can load online
# tbd on using db to permalink (??? careful re: permalink)

# host on heroku w flask (see instrs above)