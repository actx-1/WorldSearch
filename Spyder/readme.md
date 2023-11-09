# Spyder
*(web crawler/spider) – temporary implementation*

The purpose of the crawler is to proactively index web pages (web-accessible resources) by inserting rows into the relevant search engine database.
Any number of crawlers can exist at any given time (provided database connections permit). In future, an authenticated HTTP API for crawlers may offer improvements.

*the following is a temporary implementation plan:*
Each crawler connects to the database, and selects `n` unclaimed web resource links from the table. Each selected resource link is then “claimed” by updating the row with a crawler ID and a timestamp (can pass on row concurrency issue). For a defined amount of time (perhaps an hour), the crawler is free to index its claimed links, deleting each atomically as the search vectors and other relevant rows are added to the database.
After the defined amount of time has elapsed (according to the claim timestamp), a background job should clear indexing claims on links, to prevent resources becoming unindexable due to a crashed crawler.

When a crawler indexes a suitable web resource (text resources currently), it should store the current resource's content in the database, and then parse the document to remove all code tags (etc with HTML). Then, it should replace punctuation with spaces, and possibly provide spelling corrections and language detection (in future). The parsed text should be inserted into a text search table.
Any links encountered should be appended to the link page if they do not exist in the websites page.


To be completed...
