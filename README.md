# coascraper

A simple python script for gathering the info for the NSF Collaborators and Other Affiliations Information form (https://www.nsf.gov/bfa/dias/policy/coa.jsp)

Uses pybliometrics to pull data from Scopus (https://pybliometrics.readthedocs.io/en/stable/index.html), and the google search api to find email addresses. Install these with:
```
pip install pybliometrics
pip install google
```

You will need to obtain an Elsevier API key from here: https://dev.elsevier.com/apikey/manage. This is a 32 character
string.

And you will need to find out your Scopus Author ID. This is an 11 digit number, and is often listed on the left side of
your Orcid profile. You can also get it from the URL of your author page on Scopus.

Edit the script to replace the 'x's on these two lines with your API key and Author ID:
```
API_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
Author_id = 'xxxxxxxxxxx'
```
Once edited, you can run the file from the command line with `python coascraper.py`

The results are saved in an excel file called `COA.xlsx`.
