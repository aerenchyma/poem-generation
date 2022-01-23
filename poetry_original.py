import gzip, json
import re
import random
import pronouncing
import markovify
from collections import defaultdict
from typing import List

## Helper functions (largely from aparrish's examples)

def generate_poetry_corpus_lines() -> List:
    """Returns a list of all lines from Gutenberg poetry corpus"""
    # TODO: do this quicker -- hm
    all_lines = []
    for line in gzip.open("gutenberg-poetry-v001.ndjson.gz"):
        all_lines.append(json.loads(line.strip()))
    return all_lines

#####

class Poem:
    def __init__(self, seed_word, min_line_len=32, max_line_len=48):
        max_line_choices = [48, 65, 80, 120]
        self.all_lines = generate_poetry_corpus_lines()
        self.by_rhyming_part = self.generate_rhyming_part_defaultdict(min_line_len,random.choice(max_line_choices))
        # Set up ability to seed by word, TODO neaten
        self.seed_word = seed_word.lower()
        phones = pronouncing.phones_for_word(self.seed_word)[0]
        self.rhyming_part_for_word = pronouncing.rhyming_part(phones)
        # self.min_line_len = min_line_len
        # self.max_line_len = max_line_len

    def generate_rhyming_part_defaultdict(self, min_len, max_len) -> defaultdict:
        """Returns a default dict structure of 
        keys: Rhyming parts (strs)
        values: defaultdicts,
        of words corresponding to that rhyming part (strs)
        : lists of lines that end with those words (lists of strs)
        Code borrowed directly from Allison Parrish's examples."""
        by_rhyming_part = defaultdict(lambda: defaultdict(list))
        for line in self.all_lines:
            text = line['s']
            # Uniform lengths original: if not(32 < len(text) < 48)
            if not(min_len < len(text) < max_len): # only use lines of uniform lengths
                continue
            match = re.search(r'(\b\w+\b)\W*$', text)
            if match:
                last_word = match.group()
                pronunciations = pronouncing.phones_for_word(last_word)
                if len(pronunciations) > 0:
                    rhyming_part = pronouncing.rhyming_part(pronunciations[0])
                    # group by rhyming phones (for rhymes) and words (to avoid duplicate words)
                    by_rhyming_part[rhyming_part][last_word.lower()].append(text)
        return by_rhyming_part

    def get_random_line(self) -> str:
        """Returns a random line from the poetry corpus"""
        lines = [line['s'] for line in self.all_lines]
        return random.choice(lines) # For example, a string: "And his nerves thrilled like throbbing violins"

    def handle_line_punctuation(self, line, title=False):
        """Handles line-end punctuation for some fun verse finality"""
        replace_set = ",:;'\""
        maintain_set = "-!?."
        if not title:
            if line[-1] in replace_set:
                return line[:-1] + "."
            elif line[-1] in maintain_set:
                return line
            else:
                return line + "."
        else:
            fixed = ""
            for ch in line:
                if ch in replace_set or ch in maintain_set:
                    continue
                else:
                    fixed += ch
            return fixed
            # if line[-1].isalpha():
            #     return line.replace('"','').replace("'","")
            # else:
            #     return line[:-1].replace('"','').replace("'","")
        
    def generate_title(self):
        stopwords = ["a","an","the","or","as","of","at","the"] # stopwords that I care about here
        lines_with_the = [line['s'] for line in self.all_lines if re.search(r"\bthe\b", line['s'], re.I)]
        title = self.handle_line_punctuation(random.choice(lines_with_the), title=True)
        title_list = title.split()
        if title_list[-2] in stopwords and title_list[-1] in stopwords:
            self.title = " ".join(title_list[:-2])
        elif title_list[-1] in stopwords:
            self.title = " ".join(title_list[:-1])
        else:
            self.title = title
        return self.title

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
            random_line = self.get_random_line()
            stanza_list.append(self.handle_line_punctuation(random_line))

        # But if there aren't, 
        else:
            # two random couplets; # TODO: decide if there's a more creative thing here
            # followed by a random line with the word in it
            lines_with_word = [line['s'] for line in self.all_lines if re.search(fr"\b{self.seed_word}\b", line['s'], re.I)]
            rhyme_groups = [group for group in self.by_rhyming_part.values() if len(group) >= 2]
            # Use Allison's example of grabbing some couplets to grab 2
            for i in range(2):
                group = random.choice(rhyme_groups)
                words = random.sample(list(group.keys()), 2)
                stanza_list.append(random.choice(group[words[0]]))
                stanza_list.append(random.choice(group[words[1]]))
            # Then append a random line with the seed word
            stanza_list.append(self.handle_line_punctuation(random.choice(lines_with_word)))

        return stanza_list

    def generate_poem(self):

        # TODO clean up all the silly additional newline char concats
        # And maybe add addl checks/options/randomness
        self.generate_title() # For now
    
        self.full_poem = ""

        # Now: controlling len of stanza and such, but always doing 3
        # TODO: input to control how many stanzas, or some element of randomness?
        self.full_poem += "\n".join(self.generate_stanza())
        self.full_poem += "\n\n"
        self.full_poem += "\n".join(self.generate_stanza())
        self.full_poem += "\n\n"
        self.full_poem += "\n".join(self.generate_stanza())
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
    p = Poem("genius")
    print(p.__str__())