# u-of-courses parser

## Overview
### This is the course evaluations parser for the **u-of-courses** site.

The purpose of this code is to download and process course evaluations containing feedback submitted by UChicago students over the years. The most relevant data is extracted and sent to the site backend, where it is persisted into the database.

## Running this code
`pip install -r ./requirements.txt`

The rest is up to you. If you'd like to improve u-of-courses, please reach out to me through the contact page on the site.

## Subprojects
### downloader
Downloads all the evaluations from the UChicago course feedback site.
Uses selenium and reads CNET ID from `.env` file.
Downloads page assets too, as images contain some of the desired data.

### eval_parser
Iterates over each evaluation and extracts the following data points:
- Course name/title
- Course number, ex. HUMA 12300
- Quarter
- Year
- Section number
- Instructor name(s)
- Sentiment score for comments
- Each word and its frequency within the document
- The number of hours worked, if present
- Various instructor ratings

This project also sends all words and their count to the `word_frequency_api` project, which must be running for the eval parser to work.

Once each evaluation has been processed, the data is serialized to JSON and saved temporarily.

### word_frequency_api
This is a very barebones FastAPI API that takes in a list of words and their frequencies and tracks all words and their counts in an SQLite database.

## TODOs
- [ ] Extract top words using TF-IDF
- [ ] Add unit testing
- [ ] Improve logical organization of code
- [ ] Make top words DB reusable