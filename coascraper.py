#!/usr/bin/env python
"""
A simple script to scrape data from Scopus and Google search results to fill out the NSF coascraper spreadsheet

Uses pybliometrics to pull data from Scopus (https://pybliometrics.readthedocs.io/en/stable/index.html)

You will need to obtain an Elsevier API key from here: https://dev.elsevier.com/apikey/manage. This is a 32 character
string.

And you will need to find out your Scopus Author ID. This is an 11 digit number, and is often listed on the left side of
your Orcid profile. You can also get it from the URL of your author page on Scopus.
"""

import datetime
import pandas as pd
import requests
import re
from googlesearch import search
from pybliometrics.scopus import AuthorRetrieval, ContentAffiliationRetrieval

# replace the 'x' with your values
API_KEY = 'a616165db7e72b99a0f77bcb0167efdd'
Author_id = '55786568600'

# How many googled pages to scrape looking for email addresses
num_url_search_email = 10

# today's date
today = datetime.datetime.now()

# prepare a dataframe to hold the results
data = pd.DataFrame(columns=['Name', 'Organizational Affiliation', 'Optional  (email, Department)', 'Last Active'])

# get my publications, and loop over them
Documents = Author = AuthorRetrieval(Author_id).get_documents()
for doc in Documents:

    # check whether the publication date is within the last 48 months
    coverDate = datetime.datetime.strptime(doc.coverDate, '%Y-%m-%d')
    if (today - coverDate).days <= 30 * 48:

        # get the ids of all the co-authors, and loop over them
        for id in doc.author_ids.split(';'):

            # check whether to add this author to the dataset
            if (id != Author_id) and ((id not in data.index) or (data['Last Active'].loc[id] < coverDate)):

                # get their info from scopus
                CoAuthor = AuthorRetrieval(id)
                print(CoAuthor)
                affiliation = ContentAffiliationRetrieval(CoAuthor.affiliation_current)

                # google them
                google_results = search(
                    ' '.join([CoAuthor.given_name, CoAuthor.surname, affiliation.org_domain]))

                # scrape the results, looking for their email address
                email_list = []
                for tryurl in range(num_url_search_email):
                    html = requests.get(next(google_results)).text
                    # this uses regex to find something like an email address
                    email_list += re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}", html)
                # keep only those that contain the first three letters of the author's lastname
                email = ', '.join(list(set([e for e in email_list if CoAuthor.surname[:3].lower() in e.split('@')[0].lower()])))
                # if that is removing too many results, comment that line out and uncomment this one
                # email = ', '.join(list(set([e for e in email_list])))

                # add the results to the dataframe
                data = data.append(pd.DataFrame.from_dict({id: {
                                                         'Name': '{}, {}'.format(CoAuthor.surname, CoAuthor.given_name),
                                                         'Organizational Affiliation': '{}, {}'.format(affiliation.org_domain, affiliation.affiliation_name),
                                                         'Optional  (email, Department)': email,
                                                         'Last Active': coverDate
                                                         }}, orient='index'))

# output the results as an excel file
data.to_excel('coascraper.xlsx')

