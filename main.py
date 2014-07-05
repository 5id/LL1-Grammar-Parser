from collections import defaultdict
from difflib import get_close_matches
import fileinput

EPSILON = "EPSILON"
END = "$"
START = "P"
PEEK = -1



def check_spelling(word, possible):
    """
    Returns closest matching word among a list of possible, if it is within the cutoff
    """
    return (get_close_matches(word.lower(), possible, 1, cutoff=0.8) or [None])[0]


class ErrorChecker:

    def __init__(self):
        """
        Initialises the checker
        """
        self.read_table()
        self.get_tokens()
        self.stack = [END, START]
        self.index = 0
        self.errqueue = []
        self.errors = 0
        self.recovering = False
        self.string = []

    def get_token(self):
        """
        Returns the current token
        """
        return self.tokens[self.index]

    def increment(self):
        """
        'Consumes' a token
        """
        self.index += 1

    def get_rule(self, non_term, token):
        """
        Gets the rule for the specified non_terminal and token
        """
        return self.rules[self.predict[non_term][token]]

    def get_spacing(self):
        """
        Helper method to space output properly
        """
        return " " * (40-len(self.string))

    def print_stack(self):
        """
        Prints the current stack
        """
        print ' '.join(self.string), self.get_spacing(), " ".join(self.stack)

    def token_insert(self, value):
        """
        Inserts a token of value at the current position
        """
        self.tokens.insert(self.index, value)

    def predict_stack(self, index=PEEK):
        """
        Returns the stack's prediction values
        """
        return self.predict[self.stack[index]].keys()

    def has_input(self):
        """
        Check if there are still tokens to consume
        """
        return (self.index < len(self.tokens))

    def can_parse(self):
        """
        Stack and tokens still exist
        """
        return self.stack and self.has_input()

    def not_empty(self):
        """
        Stack is not almost empty
        """
        return self.stack[PEEK] != END

    def error_fixed(self):
        """
        Increments if error has just been fixed from error recovering
        """
        if self.recovering:
            self.recovering = False
            self.errors += 1

    def flush_errqueue(self):
        """
        Only prints the first error found
        """
        if self.errqueue and not self.recovering:
            print self.errqueue[PEEK]
            self.errqueue = []

    def run(self):
        """
        Parses the tokens
        """
        while self.can_parse():
            item = self.stack[PEEK]
            token = self.get_token()
            # if token is a terminal
            if item in self.terminals and item == token or item is END:
                self.error_fixed()
                removed = self.stack.pop()
                # Prevent's duplicate $
                if self.stack:
                    self.string.append(removed)
                self.increment()
                self.print_stack()
                # Repairs stack for second parse.
                # Continues until input is empty
                if not self.stack and self.has_input():
                    self.stack = [END, START]
            # if token is a non-terminal
            elif item in self.non_terminals and token in self.predict[item]:
                self.error_fixed()
                self.stack.pop()
                rule = self.get_rule(item, token)
                for r in reversed(rule):
                    if r != EPSILON:
                        self.stack.append(r)
                self.print_stack()
            # if neither or it doesn't match, try and conduct error recovery
            else:
                self.error()
                if not self.recovering:
                    self.errors += 1
            self.flush_errqueue()
        # Handles finishing errors
        self.error_fixed()
        # Prints appropriate line
        if self.errors > 0:
            print "Rejected - (%d Errors Found)" % self.errors
        else:
            print "Accepted"

    def error(self):
        """
        Error Recovery utilising a number of methods
        """
        tok = self.get_token()
        if tok is not END:
            # Try and spellcheck
            corrected = check_spelling(tok, self.predict_stack())
            if corrected and corrected is not tok:
                print "Spelling mistake: %s corrected to %s" % (tok, corrected)
                self.tokens[self.index] = corrected
                self.recovering = False
                return
            elif tok not in self.terminals:
                # Remove unfixable token
                invalid = self.tokens.pop(self.index)
                print "Removed invalid token: %s" % invalid
                self.recovering = False
                return

        # Handle duplicates
        if self.string and self.not_empty():
            if self.string[PEEK] == self.get_token():
                print "Extra %s found. Removed." % self.tokens.pop(self.index)
                return
            if self.string[PEEK] == self.stack[PEEK]:
                print "Extra %s found. Removed." % self.stack.pop()
                return


        # Sees if next token appears in stack, pops to syncronise to it
        if self.get_token() in self.stack:
            while self.stack[PEEK] != self.get_token():
                self.stack.pop()
            print "Mismatched string, syncronised with expected: %s" % self.get_token()
            return

        # Sees if there's a shortuct in input.
        # (A production rule with a single concrete terminal)
        if self.stack[PEEK] in self.shortcut and self.stack[PEEK] not in self.terminals:
            self.token_insert(self.shortcut[self.stack[PEEK]])
            self.errqueue.append("Grammar expected %s" % (self.get_token()))
            self.recovering = False
            return

        # If all the other rules failed
        if self.recovering:
            for i in range(1, len(self.stack)):
                if self.get_token() in self.predict_stack(-i):
                    [self.stack.pop() for j in range(i)]
                    return

            output = []
            # If the stack is close to end, consume tokens rather than the stack
            if len(self.stack) <= 2:
                while self.index < len(self.tokens)-1:
                    if self.get_token() in self.predict_stack():
                        print "Consumed isolated string: %s" % ' '.join(output)
                        self.recovering = False
                        return
                    output.append(self.get_token())
                    self.increment()
                print "Consumed isolated string: %s" % ' '.join(output)
                self.recovering = False
            # Try to escape loop by popping stack
            if not self.stack[PEEK] in self.terminals:
                self.errqueue.append("Couldn't find expected %s" % '/'.join(self.predict_stack()))
                self.stack.pop()
            else:
                    # If stack top is terminal, insert it
                    print "Expecting %s instead of %s" % (self.stack[PEEK], self.get_token())
                    self.tokens[self.index] = self.stack[PEEK]
            return

        self.recovering = True

    def read_table(self):
        """
        Read in the definition table of the rules
        """
        # format value[node][lookahead] = node
        self.non_terminals = set()
        self.terminals = set()
        self.rules = defaultdict(list)
        self.predict = defaultdict(defaultdict)
        self.shortcut = {}
        blacklist = set()
        with open("table.in") as fp:
            for line in fp:
                num, rule, predictions = line.strip().split("|")
                nt, prod = rule.split("->")
                prods = prod.split()
                self.rules[num] = prods
                self.non_terminals.add(nt)
                self.terminals.discard(nt)
                # Get non-terminals from rules
                for term in prods:
                    if term not in self.non_terminals:
                        self.terminals.add(term)
                preds = predictions.split(',')
                for term in preds:
                    assert term not in self.predict[nt]
                    self.predict[nt][term] = num
                if nt in predictions:
                    blacklist.add(nt)
                    self.shortcut.pop(nt, None)
                if len(preds) == 1 and nt not in blacklist:
                    self.shortcut[nt] = predictions

    def get_tokens(self):
        """
        Get tokens from the given file
        """
        self.tokens = ' '.join(
            ' '.join(line.strip().split()) for line in fileinput.input()
        ).split()
        self.tokens.append(END)

app = ErrorChecker()
app.run()
