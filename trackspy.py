#Copyright (c) 2013 David Harwood
#
#####
#This code is licensed under the terms of the MIT License.
#You should have received a copy of this license in an included file
#named COPYING. If you did not receive this file, you may obtain a
#copy of this file at http://opensource.org/licenses/MIT
#####

from selenium import webdriver
import sys
import sqlite3
import os
import os.path as path
import shutil
import time
import argparse

parser = argparse.ArgumentParser(description="A script to go through a list of provided URLs and display the trackers on each", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("urllistfile", help="Name of file containing list of URLs to go through, one URL per line")
parser.add_argument("-o", "--output", dest="output", default="results.sqlite", help="The path for the sqlite3 file to dump results in. This can be disabled by setting -o to none")
parser.add_argument("--no-lso", dest="lsos", action='store_false', help="Don't examine LSO access information")
parser.add_argument("--no-stdout", dest="printout", action='store_false', help="Don't print the results of the run to standard out")
args = parser.parse_args()

#url list file format:
#list of URLs, one per line

u = open(args.urllistfile, 'r')

HOME = path.expanduser('~') #let's make sure we know where we're working
GNASH_PATH = path.join(HOME, ".gnash")
GNASH_TMP = path.join(HOME, ".gnash_tmp")
MAC_PATH = path.join(HOME, ".macromedia")
MAC_TMP = path.join(HOME, ".macromedia_tmp")

os.stat_float_times(False) #make sure we're dealing with ints with atime

#setup for looking at LSOs, since they stick around no matter what FF profile is being used
if(args.lsos):
    if(path.exists(GNASH_PATH)):
        shutil.copytree(GNASH_PATH, GNASH_TMP)
        shutil.rmtree(GNASH_PATH)
        os.mkdir(GNASH_PATH) #need to do this to make sure we still have the structure of the directories the plugin is expecting
        gnash = True
    else:
        gnash = False

    if(path.exists(MAC_PATH)):
        shutil.copytree(MAC_PATH, MAC_TMP)
        shutil.rmtree(MAC_PATH)
        os.mkdir(MAC_PATH)
        macromedia = True
    else:
        macromedia = False

    lsodict = dict()

driver = webdriver.Firefox() #the driver for the browser
profloc = driver.firefox_profile.path #the location of the profile

#selenium uses an anonymous profile for running this, so I don't need to worry about cookie cross-pollination
#or the extensions I use getting in the way of Firefox doing its thing
cookiedb = sqlite3.connect(path.join(profloc, "cookies.sqlite"))
cur = cookiedb.cursor()

cookies = dict()
lastload = (0,)
timedict = dict()

#OK, here's the meat of the script: go to each site, look at it, keep track of what's done
for url in u:
    url = url.strip()
    if(args.printout):
        print("now loading " + url)
    driver.get(url)
    time.sleep(5) #let the clock tick a little bit to make sure that our time-keeping doesn't get thrown off
    if(path.exists(path.join(profloc, "cookies.sqlite"))):
        for c in cur.execute('SELECT DISTINCT baseDomain FROM moz_cookies WHERE lastAccessed > ?', lastload):
            if(c[0] in cookies):
                cookies[c[0]].append(url)
            else:
                cookies[c[0]] = [url]

    #look through the directories for LSOs and check to see if something has been accessed
    if(args.lsos):
        if(gnash):
            for x in os.listdir(GNASH_PATH):
                if(x not in lsodict):
                    lsodict[x] = [url]
                    for y in os.listdir(path.join(GNASH_PATH, x)):
                        info = os.stat(path.join(GNASH_PATH,x,y))
                        timedict[path.join(x,y)] = info.st_atime
                else:
                    accessed = False
                    for y in os.listdir(path.join(GNASH_PATH,x)):
                        if(path.join(x,y) not in timedict or timedict[path.join(x,y)] > (lastload[0] // pow(10,6))): #cookies use microseconds, stat() uses seconds...
                            accessed = True
                            timedict[path.join(x,y)] = os.stat(path.join(GNASH_PATH,x,y)).st_atime
                    if(accessed):
                        lsodict[x].append(url)

        if(macromedia):
            for x in os.listdir(MAC_PATH):
                if(x not in lsodict):
                    lsodict[x] = [url]
                    for y in os.listdir(path.join(MAC_PATH, x)):
                        info = os.stat(path.join(MAC_PATH,x,y))
                        timedict[path.join(x,y)] = info.st_atime
                else:
                    accessed = False
                    for y in os.listdir(path.join(MAC_PATH,x)):
                        if(path.join(x,y) not in timedict or timedict[path.join(x,y)] > (lastload[0] // pow(10,6))):
                            accessed = True
                            timedict[path.join(x,y)] = os.stat(path.join(MAC_PATH,x,y)).st_atime
                    if(accessed):
                        lsodict[x].append[url]

    lastload = (time.time() * pow(10,6),) #cookie entries use microseconds for lastAccessed

driver.close()

if(args.output != "none"):
    dataout = sqlite3.connect(path.join(HOME, args.output))
    d_out = dataout.cursor()

    d_out.execute('CREATE TABLE cookies (site_url text, cookie_url text)')

    for k in cookies.keys():
        if(args.printout):
            print(k + " found on " + str(cookies[k]))
        for b in cookies[k]:
            x = (b, k)
            d_out.execute('INSERT INTO cookies VALUES (?, ?)', x)

    dataout.commit()
    if(args.lsos):
        d_out.execute('CREATE TABLE lsos (site_url text, lso_name text)')

        #output the results from the LSO analysis
        for l in lsodict.keys():
            if(args.printout):
                print(l + " LSO(s) were accessed by " + str(lsodict[l]))
            for b in lsodict[l]:
                x = (b, l)
                d_out.execute('INSERT INTO lsos VALUES (?, ?)', x)

    dataout.commit()
    dataout.close()
elif(args.printout):
    for k in cookies.keys():
        print(k + " found on " + str(cookies[k]))
    if(args.lsos):
        for l in lsodict.keys():
            print(l + " LSO(s) were accessed by " + str(lsodict[l]))

if(args.lsos):
        #replace the LSOs that were removed at the beginning
        if(gnash):
            shutil.rmtree(GNASH_PATH)
            shutil.copytree(GNASH_TMP, GNASH_PATH)
            shutil.rmtree(GNASH_TMP)

        if(macromedia):
            shutil.rmtree(MAC_PATH)
            shutil.copytree(MAC_TMP, MAC_PATH)
            shutil.rmtree(MAC_TMP)

