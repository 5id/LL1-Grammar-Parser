#LL(1) Parser in Python
##Introduction
My 2nd Year Formal Languages Assignment to create a LL(1) parser that accepts or rejects strings based on their conformance. 
Involved implementing custom error recovery functionality in the event of bad input.
##Error Recovery
Error recovery consisted of a number of actions, ranging from harmless to purely destructive.
###Spell Checking
It used the lookahead symbols to try and auto-correct any unidentified symbols.
###Duplicates
It removed any consecutive duplicate tokens
###Synchronisation
If an error was thrown, and there is a token on the stack that is the same as the current input, the parser pops the stack until it synchronises its input with the stack
###Shortcutting
If every other attempt fails, it will attempt to add a single terminal production rule from the PREDICT set if one exists. A classic use case of this is for a missing semicolon.
###Extended Error Recovery (Pants on Fire Mode)
####Last-ditch
Searches through current stack and checks if they have any predictions that could match the current token. If they do, pop the stack to this non-terminal.
####Consume Tokens
If the stack only has one production rule left on the stack, it tries to continue parsing by consuming input tokens until it gets one matching the prediction set of the current node.
####Popping the Stack
If it cannot move off the current non-terminal, it pops it
####Inserting Tokens
If the current top of the stack is a terminal, it inserts this terminal to force continuation of Parsing

##To Run
To run code, simply type `python main.py <filename>`
Enjoy!
