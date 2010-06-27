'''
Created on Jun 26, 2010

@author: jbrukh

Craigslist Mailer
Copyright (c) 2010 Jake Brukhman
LICENSE: Public domain.

Periodically checks a Craigslist RSS feed for new listings and e-mails
them to a recipient.  Set all configuration in conf.py.
'''

import sys
import random
import time
import os.path
import pickle
import scraper
import emailer
import conf
import getopt

QUERIES=[]
MIN_ASK=""
MAX_ASK=""
BEDROOMS=""

def main():
    """The main loop."""
    while True:
        if len(QUERIES)==0:
            retrieve_listings("",MIN_ASK,MAX_ASK,BEDROOMS)
        else:
            for query in QUERIES:
                retrieve_listings(query,MIN_ASK,MAX_ASK,BEDROOMS)
        sleep_randomly()

def retrieve_listings(query, min_ask, max_ask, bedrooms):
    """Retrieve the listings and e-mail them."""
    try:
        titles = load_cache()
    except IOError, errstr:
        print "Could not retrieve cache: ", errstr

    try:
        url = scraper.build_url(conf.CRAIGS_URL, query, min_ask, max_ask, bedrooms)
        items = scraper.extract(scraper.scrape(url))
    except:
        print "Could not retrieve listings."
        return
    
    new_listings = []
    for item in items:
        title = item[0]
        if not title in titles:
            print title
            new_listings.append(item)
            titles.add(title)
    
    if len(new_listings)>0:
        # send the e-mail
        msg = get_msg(new_listings, query)
        try:
            emailer.send_email(conf.SENDER, conf.RECIPIENT, msg)
        except:
            print "Could not send email: ", sys.exc_info()[0]
    else:
        print "Nothing to send."
    
    # persist
    cache(titles)

def get_msg( new_listings, query ):
    """Create the listing summary email."""
    subject = "Apartments -- %d for Query: %s" % (len(new_listings), query)
    header = "From: %s\nTo: %s\nSubject: %s\n\n" % (conf.SENDER, conf.RECIPIENT, subject)
    body = header+"\n\n".join(["%s\n%s"%(item) for item in new_listings])  
    return body    
    
def load_cache():
    """Load the titles cache."""
    # check whether the file exists
    if not os.path.exists(conf.CACHE_FILE):     
        cache(set())
    
    file = open(conf.CACHE_FILE,'r')
    titles = pickle.load(file)
    file.close()
    
    return titles
            
def cache( titles ):
    """Cache a bunch of titles."""
    file = open(conf.CACHE_FILE,'w')
    pickle.dump(titles,file)
    file.close()

def sleep_randomly():
    """Sleep for 1-5 minutes."""
    sleep_time = random.randint(60,60*5)
    print "Sleeping %d seconds before next retrieve..." % sleep_time
    time.sleep(sleep_time)
    
def usage():
    """Usage."""
    print """
        python craigslist-mailer.py 
            [-q,--queries <STRING,STRING,...>]   -- search queries
            [-m,--minAsk <INTEGER>]              -- minimum price
            [-M,--maxAsk <INTEGER>]              -- maximum price
            [-b,--bedrooms <INTEGER>]            -- number of bedrooms
    """

def get_args():
    global QUERIES, MIN_ASK, MAX_ASK, BEDROOMS
    """Get the commandline arguments."""
    opts,args = getopt.getopt(sys.argv[1:],\
            "q:m:M:b:h", ['query=', 'minAsk=', 'maxAsk=', 'bedrooms=', 'help'])
    for opt, arg in opts:
        if opt in ('-q', '--queries'):
            QUERIES=arg.split(',')
        if opt in ('-m', '--minAsk'):
            MIN_ASK=str(int(arg)) # checks for integer
        if opt in ('-M', '--maxAsk'):
            MAX_ASK=str(int(arg))
        if opt in ('-b', '--bedrooms'):
            BEDROOMS=str(int(arg))
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)

if __name__=='__main__':
    try:
        # get the options
        get_args();
        main()
    except ValueError:
        usage()
    except getopt.GetoptError:
        usage()
    except KeyboardInterrupt:
        print "Goodbye."
        sys.exit(0)
    sys.exit(2)