Every crawler should write its ID to the database, returning that ID to keep saved.

Each crawler should load about 10,000 links from the database at a time, and should update each row with a claim ID and a claim timestamp.
Upon loading the links, each link's domain should have a robots.txt file loaded from the database. The database should return a bool representing if the domain *has* a robots.txt file. If not, don't check robots.txt. If so, then get that from the database.
However, the database should also store a timestamp as for when the robots.txt file was last checked, and perhaps a hash (or mtime) to determine if changes have been made. If the timestamp is more than, say, a day old, then the spider (before spidering any links), should get the robots.txt file (if exists), store it in a local dictionary, and send it on to the database to be stored, with an updated checked_timestamp or something.

Some additional parsing might be possible, say to remove comments from the stored versions of robots.txt, to reduce the size.

Every robots.txt file should be parsed by a spider in progress – the spider should balance between grabbing a diverse array of links to spider, and grabbing many of the same domain: multiple links from the same domain require just one robots.txt, but different domains allow the spider to switch between them, to avoid spidering any one website too intensely. So, the spider should always interlace domain links where possible, and perhaps record last_downloaded_timestamps for each domain to do something like only downloading from one website every 300 ms.

Once a spider gets around to downloading a link, it should first check the content type. If the type is acceptable (e.g. HTML), then the web page should be downloaded. First, the spider should record all links found, and write them to the links_queue table. Then, the spider should write the pure page content to the database, and also write the parsed text content to the text search table. The original link in the queue table should be deleted, and the crawler ID table should have a timestamp updated.

Then, the spider should repeat.
