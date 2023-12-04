import psycopg2
import json
import time
import urllib.robotparser
import requests
from bs4 import BeautifulSoup
import datetime

def open_db():
    try:
        with open("pg_creds.txt",'r') as f:
            creds = json.loads(f.read())
        db = psycopg2.connect("dbname='"+str(creds["dbname"])+"' user='"+str(creds["user"])+"' password='"+str(creds["password"])+"' host='"+str(creds["host"])+"' port='"+str(creds["port"])+"'")
        return db
    except FileNotFoundError:
        print("Missing credential file.")
    except Exception as e:
        print("Failure to connect to the database: "+str(e))
        return None

def say(content: str):
    print("["+str(datetime.datetime.now())+"] "+content)

def get_domain_name(link):
    return link.split("//")[1].split("/")[0]

def reverse_domain_name(domain_name):
    reversed_domain = ""
    for i,p in enumerate(reversed(domain_name.split("."))):
        if i != 0:
            reversed_domain += "."
        reversed_domain += p
    return reversed_domain

def download(url):
    response = requests.get(url,headers={'User-Agent': 'WSearch Spyder'})
    if response.status_code == 200:
        return response.headers,response.content
    else:
        print("Error getting file ("+str(url)+"): "+str(response.status_code))
        return None,None

def parse_robots_txt(file, user_agent):
    parser = urllib.robotparser.RobotFileParser()
    if isinstance(file, bytes):
        file = file.decode('utf-8')
    try:
        parser.parse(file.splitlines())
        # Extract sitemaps
        sitemaps = parser.site_maps()
        crawldelay = parser.crawl_delay(user_agent)
        requestrate = parser.request_rate(user_agent)
        return parser,{
            'sitemaps': sitemaps,
            'crawldelay': crawldelay,
            'request_rate': requestrate
        }
    except AttributeError:
        return parser,{
            'sitemaps': None,
            'crawldelay': None,
            'request_rate': None
        }


def convert_datetime_to_ts(string: str):
    return datetime.datetime.strptime(string,'%a, %d %b %Y %H:%M:%S GMT').timestamp()

start_time = int(time.time())

# Generate ID + write to database
db = open_db()
cursor = db.cursor()
cursor.execute("INSERT INTO spyders(created_ts,last_claim_ts) VALUES(%s,%s) RETURNING id;", [start_time,start_time])
spyder_id = cursor.fetchone()[0]
spyder_version = 1

user_agent = "WSearch Spyder"

strip_symbol_list = [",",".","(",")","\"","'",";",":","!","[","]","-","–","—","/","{","}","^","%","$","£","¢","¥","€","#","@"]

# Load links from database and update link rows with claim
claim_ts = int(time.time())
cursor.execute("WITH cte AS (SELECT * FROM link_queue WHERE claimant_id IS NULL LIMIT 100) UPDATE link_queue SET claimant_id=%s,claim_ts=%s FROM cte WHERE link_queue.id = cte.id RETURNING cte.id,cte.last_indexed_ts,cte.added_ts,cte.link;", [spyder_id,claim_ts])
queue = cursor.fetchall()
db.commit()
domains_list = {}
for website in queue:
    try:
        domains_list[get_domain_name(website[3])].append({"web_row": website})
    except KeyError:
        domains_list[get_domain_name(website[3])] = [{"web_row": website}]
del queue

# Load robots.txt
    # If robots.txt is out of date, get the new version
        # If different, send to the database with timestamp
    
    # Add robots.txt parser to parser dictionary
cursor = db.cursor()
for domain in domains_list:
    reversed_domain = reverse_domain_name(domain)
    cursor.execute("SELECT * FROM robotstxt WHERE reversed_hostname=%s", [reversed_domain])
    robots_row = cursor.fetchone()
    if robots_row == None:
        say("robots.txt does not exist in the database for "+str(reversed_domain)+". Scanning now...")
        # If robots.txt is not in the database, then add it and add all the sitemap links to the link_queue table
        robots_headers,robots_file = download("http://"+str(domain)+"/robots.txt")
        if robots_file == None:
            # No robots.txt
            cursor.execute("INSERT INTO robotstxt(reversed_hostname,mtime,last_mtime_check,content_size,content) VALUES(%s,%s,%s,%s,%s);", [reversed_domain,0,int(time.time()),0,None])
        else:
            try:
                try:
                    mtime_date = robots_headers["last-modified"]
                except KeyError:
                    mtime_date = robots_headers['Date']
                cursor.execute("INSERT INTO robotstxt(reversed_hostname,mtime,last_mtime_check,content_size,content) VALUES(%s,%s,%s,%s,%s);", [reversed_domain,int(convert_datetime_to_ts(mtime_date)),int(time.time()),len(robots_file),robots_file.decode('utf-8')])
            except Exception as e:
                print("Error when handling robots.txt ("+str(e)+"): "+str(reversed_domain)+". Headers available: "+str(robots_headers))
                
    else:
        say("robots.txt is in the database for "+str(reversed_domain)+". Determining if re-freshening is required...")
        # Robots file (or lack thereof) exists in the database -- check that it isn't too old, if so then check for an updated mtime
        # Could maybe make it more efficient by first only checking the robots.txt mtime instead of downloading the whole thing
        previous_mtime = robots_row[1]
        previous_check = robots_row[2]
        if time.time() - previous_check > 24*3600:
            say("robots.txt needs to be refreshened...")
            # Re-check server side
            robots_headers,robots_file = download("http://"+str(domain)+"/robots.txt")
            if robots_file == None:
                # No robots.txt
                cursor.execute("UPDATE robotstxt SET mtime=0,last_mtime_check=%s,content_size=0,content=%s WHERE reversed_hostname=%s", [int(time.time()),None,reversed_domain])
            else:
                # robots.txt exists
                mtime = int(convert_datetime_to_ts(robots_headers['last-modified']))
                if mtime != previous_mtime:
                    # robots.txt needs to be updated
                    try:
                        cursor.execute("UPDATE robotstxt SET mtime=%s,last_mtime_check=%s,content_size=%s,content=%s WHERE reversed_hostname=%s;", [mtime,int(time.time()),len(robots_file),robots_file.decode('utf-8'),reversed_domain])
                        cursor.execute("INSERT INTO robotstxt(reversed_hostname,mtime,last_mtime_check,content_size,content) VALUES(%s,%s,%s,%s,%s);", [reversed_domain,int(convert_datetime_to_ts(robots_headers["last-modified"])),int(time.time()),len(robots_file),robots_file.decode('utf-8')])
                    except Exception as e:
                        print("Error when handling robots.txt ("+str(e)+"): "+str(reversed_domain)+". Headers available: "+str(robots_headers))
        else:
            # Just go along with cached robots.txt
            say("robots.txt is new enough; no re-freshen is required.")
            robots_file = robots_row[4]
    say("Continuing robots.txt processing...")
    parser,access_data = parse_robots_txt(robots_file, user_agent)
    if access_data['sitemaps'] != None:
        for site in access_data['sitemaps']:
            print(site)
    for i,urldata in enumerate(domains_list[domain]):
        # Check each URL
        if robots_file == None:
            domains_list[domain][i]["can_access"] = True
        else:
            domains_list[domain][i]["can_access"] = parser.can_fetch(user_agent,domains_list[domain][i]["web_row"][3])
db.commit()

# Sort in-process links list at some point perhaps
# Record download timestamps for each domain

def round_robin_generator(data):
    # Create a dictionary to keep track of the index for each domain
    domain_indices = {domain: 0 for domain in data}

    # Calculate the total number of items to be yielded
    total_items = sum(len(urls) for urls in data.values())

    yielded_count = 0

    # Continue looping until all items are yielded
    while yielded_count < total_items:
        # Iterate through each domain
        for domain, items in data.items():
            # Get the current index for this domain
            index = domain_indices[domain]

            # Check if there are items available for this domain
            if index < len(items):
                # Yield the item at the current index
                yield items[index]

                # Update the index for this domain
                domain_indices[domain] = (index + 1) % len(items)

                # Increment the count of yielded items
                yielded_count += 1

def strip_symbols(text):
    translation_table = str.maketrans({key: ' ' for key in strip_symbol_list})
    return text.translate(translation_table)
def extract_text(html):
    try:
        soup = BeautifulSoup(html, 'lxml')

        # Extracting text from the title tag
        title_text = soup.title.string if soup.title else ''

        # Extracting visible text
        visible_text = ' '.join(soup.stripped_strings)

        # Extracting alt text from images
        alt_text = ' '.join(img['alt'] for img in soup.find_all('img', alt=True))

        # Combine all extracted text
        all_text = ' '.join(filter(None, [title_text, visible_text, alt_text]))

        return all_text
    except TypeError:
        return "None"

def extract_links(html):
    try:
        soup = BeautifulSoup(html, 'lxml')
        return [a.get('href') for a in soup.find_all('a', href = True)]
    except TypeError:
        return []

# Iterate through links list and download if robots.txt applies, with 300 ms grace?
url_generator = round_robin_generator(domains_list)

cursor = db.cursor()
for url in url_generator:
    link = url["web_row"][3]
    cursor.execute("SELECT mtime,last_indexed_ts,last_checked_ts,indexer_version FROM websources WHERE link=%s", [link])
    database_record = cursor.fetchone()
    if database_record == None:
        # Page is not yet in the database
        if url['can_access'] == True:
            say("Downloading: "+str(link))
            # Download here
            try:
                delete_queue_row = True
                headers, content = download(str(link))
                parsed_content = extract_text(content)
                content_links = extract_links(content)
                try:
                    mtime = convert_datetime_to_ts(headers['last-modified'])
                except KeyError:
                    # This happens for youtube.com -- figure out alternative methods of determining the modification time
                    mtime = 0
                except TypeError:
                    # This happens for https://uz.wikiversity.org/wiki/
                    mtime = 0
                last_indexed_ts = time.time()
                last_checked_ts = time.time()
                cursor.execute("INSERT INTO websources(reversed_hostname,link,mtime,last_indexed_ts,last_checked_ts,indexer_version,resource_content) VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id", [reverse_domain_name(get_domain_name(link)),link,mtime,int(time.time()),int(time.time()),int(spyder_version),str(content)])
                record_id = cursor.fetchone()
                cursor.execute("INSERT INTO websource_search(websource_id,part,text_search) VALUES(%s,%s,to_tsvector('english',%s))", [record_id,1,str(parsed_content)]) # Temporary implementation for 'part'
                for item in content_links:
                    # Iterate through parsed links to avoid writing ones for the same domain which we aren't allowed to download as per robots.txt?
                    # I'm not sure what to do with links like `/wiki/Encyclopedia` -- I suspect they are links to resources available through the web server? Ignore them for now most likely...
                    if item.startswith("http://") or item.startswith("https://"):
                        cursor.execute("INSERT INTO link_queue(last_indexed_ts,added_ts,link) VALUES(0,%s,%s) ON CONFLICT(link) DO NOTHING;", [int(time.time()),str(item)])
            except requests.exceptions.ConnectionError:
                delete_queue_row = False
        # Delete the link from the database
        if delete_queue_row == True:
            cursor.execute("DELETE FROM link_queue WHERE id=%s", [url["web_row"][0]])
    else:
        # The page is already in the database – check if it's fresh by mtime comparison, and reindex if it's outdated.
        pass
cursor.execute("UPDATE spyders SET last_claim_ts=%s WHERE id=%s", [int(time.time()),int(spyder_id)])
db.commit()
db.close()
