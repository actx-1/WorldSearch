import urllib.robotparser


def parse_robots_txt(url, user_agent):
    # Used to grab robots.txt from websites when the crawler first visits or otherwise determines a re-check is necessary.
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(url + '/robots.txt')
    parser.read()
    # Extract sitemaps
    sitemaps = parser.site_maps()
    crawldelay = parser.crawl_delay(user_agent)
    requestrate = parser.request_rate(user_agent)
    return {
        'sitemaps': sitemaps,
        'crawldelay': crawldelay,
        'request_rate': requestrate
    }

result = parse_robots_txt("https://en.wikipedia.org","zBot")
print(result)

# Example for parsing locally from a file (with aspirations in future to do from a database)
parser = urllib.robotparser.RobotFileParser()
with open("wikipedia.robots.txt",'r') as file:
    contents = file.readlines()

    parser.parse(contents)

    can_access = parser.can_fetch("zBot","https://en.wikipedia.org/wiki/Semantic_satiation")

    print(can_access)
