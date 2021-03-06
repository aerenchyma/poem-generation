import gzip, json
import re
import random
import pronouncing
from collections import defaultdict
from typing import List
from app import CorpusLine

## TODO: create a database with the corpus to put up on digitalocean
## TODO: in app, modify code and use db fxns to grab the lines? for online use 


## Helper functions

# def save_poetry_corpus_lines():
#     """Depends upon existence of gutenberg-poetry-v001.ndjson.gz,
#     writing this into a text file plainly speeds up db creation later"""
#     all_lines = []
#     for line in gzip.open("gutenberg-poetry-v001.ndjson.gz"):
#         all_lines.append(json.loads(line.strip()))
#     # json_obj = json.dumps(all_lines)
#     f = open("poetry_corpus_text.txt",'w')
#     # f.write(json_obj)
#     # f.close()
#     lines_text = [l["s"] for l in all_lines]
#     lines_text_full = "\n".join(lines_text)
#     f.write(lines_text_full)
#     f.close()

# def generate_poetry_corpus_lines() -> List:
#     """Returns a list of all lines from Gutenberg poetry corpus
#     Direct from the ndjson.gz file
#     Largely borrowed from Allison Parrish's examples"""
#     # TODO: do this quicker -- hm
#     all_lines = []
#     for line in gzip.open("gutenberg-poetry-v001.ndjson.gz"):
#         all_lines.append(json.loads(line.strip()))
#     return all_lines

def get_poetry_lines() -> List: # Can be what you input for lines in Poem input for local use
    """Assuming you have previously run save_poetry_corpus_lines to save file,
    and then commented it out again -- don't commit the huge txt file"""
    f =  open("poetry_corpus_text.txt",'r')
    lines = f.readlines()
    f.close()
    return lines

def get_count(q):
    count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    count = q.session.execute(count_q).scalar()
    return count

def random_line_from_db(model):
    """Expects model to have element line -> a string"""
    from sqlalchemy import func
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
        random_line = random_line_from_db(CorpusLine)
        print(random_line) # debug
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
        for l in self.all_lines:
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

    def handle_line_punctuation(self, line, title=False):
        """Handles line-end punctuation for some fun verse finality"""
        replace_set = ",:;'\""
        maintain_set = "-!?."
        full_set = replace_set + maintain_set
        if not title:
            if line.line[-2] in replace_set:
                return line.line[:-2]+"\n"
            else:
                return line.line
        else: # if it is a title, replace interim punct and return without end punc
            fixed = line.line.replace(",","").replace(":","").replace(";","").replace("'","").replace('"','')
            if fixed[-1] in full_set:
                return fixed[:-1]
            return fixed
        
    def generate_title(self):
        stopwords = ["a","an","the","or","as","of","at","the"] # stopwords that I care about here
        # lines_with_the = [line['s'] for line in self.all_lines if re.search(r"\bthe\b", line['s'], re.I)]
        lines_with_the = [line for line in self.all_lines if "the" in line.line]
        # print(lines_with_the[1].line)
        title = self.handle_line_punctuation(random.choice(lines_with_the), title=True)
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
            # # lines_with_word = CorpusLine.query.filter_by(self.seed_word in line) # if in app, same in gen_title, but this isn't now
            # if lines_with_word == []: # If there aren't any, sure, choose basically any line
            #     lines_with_word = random.sample(self.all_lines,len(self.all_lines)//2) # Grab a list of half the lines that exist TODO more complicated?
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
            stanza_list.append(self.handle_line_punctuation(random_line_from_db(CorpusLine)))#(self.get_random_line()))
            # ri = random.randint(0,get_count(self.all_lines))
            # stanza_list.append(self.handle_line_punctuation(self.all_lines.filter_by(id=ri)))
            # stanza_list.append(self.handle_line_punctuation(random.choice(self.all_lines))) # or lines_with_word instead of self.all_lines

        return stanza_list


    def generate_poem(self):

        # TODO clean up all the silly additional newline char concats
        # And maybe add addl checks/options/randomness
        self.generate_title() # For now
    
        self.full_poem = ""

        # Now: controlling len of stanza and such, but always doing 3
        # TODO: input to control how many stanzas, or some element of randomness?
        # self.full_poem += "\n".join(self.generate_stanza())
        # self.full_poem += "\n\n"
        # self.full_poem += "\n".join(self.generate_stanza())
        # self.full_poem += "\n\n"
        # self.full_poem += "\n".join(self.generate_stanza())
        # self.full_poem_list = self.full_poem.split("\n")
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



if __name__ == "__main__":
    # import time
    # start_time = time.time()
    # p = Poem("hi")
    # executionTime = (time.time() - start_time)
    # print('Execution time in seconds for poem 1: ' + str(executionTime))
    # print(p.__str__())

    # start_time_2 = time.time()
    # p = Poem("hi")
    # executionTime2 = (time.time() - start_time_2)
    # print('Execution time in seconds for poem 2: ' + str(executionTime2))
    # print(p.__str__())

    # start_time_3 = time.time()
    # p = Poem("hi")
    # executionTime3 = (time.time() - start_time_3)
    # print('Execution time in seconds for poem 3: ' + str(executionTime3))
    # print(p.__str__())

    ## Fun
    lines = get_poetry_lines() # get lines from local file, .gitignored
    # p = Poem("hi", lines=lines)
    # print("***",p.generate_title(),"***\n\n")
    # print(p.__str__())
    # p2 = Poem("hi", lines=lines)
    # print("***",p2.generate_title(),"***\n\n")
    # print(p2.__str__())

    p3 = Poem("girlfriend", lines=lines)#, num_lines_sample=len(lines))
    print("***",p3.generate_title(),"***\n\n")
    print(p3)

    p4 = Poem("hi", lines=lines)
    print("***",p4.generate_title(),"***\n\n")
    print(p4.__str__())

    p5 = Poem("orange", lines=lines)
    print("***",p5.generate_title(),"***\n\n")
    print(p5.__str__())

    pass
