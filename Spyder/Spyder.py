# Generate ID + write to database

# Load links from database
# Update link rows with claim

# Load robots.txt
    # If robots.txt is out of date, get the new version
        # If different, send to the database with timestamp
    # If robots.txt is not in the database, then add all the sitemap links to the link_queue table
    # Add robots.txt parser to parser dictionary

# Sort in-process links list
# Record download timestamps for each domain

# Iterate through links list and download if robots.txt applies, with 300 ms grace?
# Get links from the page, and append them to the link_queue table
# Write raw site content and text search to the database
# Delete rows from link_queue
# Update the crawler ID's last indexed time
