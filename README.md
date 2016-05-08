# scraper

REQUIREMENTS TO RUN THIS PROGRAM ARE IN requirements.txt WHICH IS INCLUDED IN THIS REPO

This program scrapes grailed every 2 minutes to look for things you want to buy. You can turn it off when you leave the house/go to sleep and it will look at all the listings that were posted since it was last run when you start it up again. it does NOT look at all of the listings that were posted BEFORE you FIRST ran the program.

You can change the things that you are looking for by editing the settings.json file. searchRules maps to a list of rules. Each rule has the following attributes:

- andTerms: regular expressions that must all appear in the listing description or title.
- orTerms: regular expressions, at least one of which must appear in the listing description or title.
- allowedDesigners: regular expressions, at least one of which must appear in the designer's name

Any matches that are found are logged in the log.txt text file. It includes the pretty URL of the grailed listing. If you want to remove an item from log.txt (and you don't want it to be picked up by the scraper again), add " idontwant" to the end of that line and then save the file.

I plan to extend the search options so that you can stipulate price ranges, etc. Also the alert tone is pretty annoying.

8)))))
