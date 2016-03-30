import simplejson as json
import requests 
from bs4 import BeautifulSoup
import yaml
import regex
import time
import vlc



def main():
	scraper = Scraper("settings.json")
	scraper.catchUp()
	print("catchup phase finished :)")
	scraper.watch(120)




class Scraper(object):
	def __init__(self, rulesFileName):
		with open(rulesFileName, "r", encoding = "utf-8") as fileStream:
			self.rules = json.load(fileStream)
			self.foundListings = {}
			self.blacklist = []

			#TODO, really this method could just be looped over instead of the watch() method. Actually not much more efficienct because we are just getting one page of json either way
	def catchUp(self):
		pageNumber = 1
		oldDate = 99999999999999999#this is for debug### JUST CHECKING AS WE GO BACK THROUGH THEM THAT THEY ARE BEING GIVEN TO US IN THE ORDER THAT THEY WERE POSTED TO THE SITE
		#while True: increment pageNumber til we reach where we were up to
		while(True):
			response = requests.get(self.rules["info"]["rootUrlStart"] + str(pageNumber) + self.rules["info"]["rootUrlEnd"])
			pageJSON = json.loads(response.text)
			for eachListing in pageJSON["data"]:
				#try:
				#	print("checking listing with title:" + eachListing["title"])
				#except UnicodeEncodeError:
				#	print("failed to print that title fam")
				unsanitisedDate = eachListing["created_at"]
				sanitisedDate = self.sanitiseDate(unsanitisedDate)
				#print(sanitisedDate)
				
				assert(oldDate >= sanitisedDate)
				oldDate = sanitisedDate# this is for debug###
				if(self.sanitiseDate(self.rules["info"]["gotUpTo"]) > sanitisedDate):
					print("WE GOT UP TO WHERE WE WATCHED TIL LAST TIME, SO ENDING THE CATCHUP PHASE")
					#print(sanitisedDate)
					self.logCurrentFoundItems()
					return
				if(self.decideIfRelevant(eachListing)):
					print("while catching up, we found: " + eachListing["title"])
					self.playAlert()
					self.foundListings[eachListing["title"]] = eachListing
			pageNumber += 1



			#TODO: WILL WANT TO HAVE AN "ENTRY" OBJECT DEFINED IN YAML SO THAT WE CAN STIPULATE E.G. MUST BE BY ONE OF THESE DESIGNERS REGEX, MUST HAVE THESE REGEXES IN THE TITLE OR DESC, MUST NOT HAVE THESE REGEXES, MUST HAVE ONE OF THESE REGEXES. 
			#so it has to pass all of those aforementioned stages before it would be added to the found list. If e.g. it can be any designer. Then i just put a wildcard regex in that category
	def decideIfRelevant(self, listing):
		for eachRule in self.rules["searchRules"]:
			if any(regex.search(eachDesignerRegex, listing["designer"]["name"]) for eachDesignerRegex in eachRule["allowedDesigners"]) and all(regex.search(eachAndRegex, listing["title"] + listing["description"]) for eachAndRegex in eachRule["andTerms"]) and any(regex.search(eachOrRegex, listing["title"] + listing["description"]) for eachOrRegex in eachRule["orTerms"]):
				return True
		return False

	#NOTE that this might print out that it is finding the old stuff over and over again, but it's just reputting the old stuff back into the dictionary 
	def watch(self, interval):
		response = requests.get(self.rules["info"]["rootUrlStart"] + str(1) + self.rules["info"]["rootUrlEnd"])
		pageJSON = json.loads(response.text)
		for eachListing in pageJSON["data"]:
			if(self.decideIfRelevant(eachListing)):
				if(eachListing["title"] not in self.foundListings and self.rules["info"]["grailedBasePath"] + eachListing["pretty_path"] + " " + eachListing["title"] not in self.blacklist):
					self.playAlert()
					print("while watching, we found:" + eachListing["title"])
				self.foundListings[eachListing["title"]] = eachListing #TODO: should be a comdination of the title and the id for uniqueness. Should check whether it's already in tehre before adding it and play a sound if it adds something new.
		self.logCurrentFoundItems()
		#update the part of the rules file that keeps track of what time we are up to. 
		nowUpTo = pageJSON["data"][0]["created_at"]
		self.rules["info"]["gotUpTo"] = nowUpTo;
		with open("settings.json", "w") as fileStream:
			json.dump(self.rules, fileStream)
		time.sleep(interval)
		self.watch(interval)


	def sanitiseDate(self, dateString):
		return int(regex.sub("[a-z|A-Z|:|.|-]", "", dateString))

	def playAlert(self):
		sound = vlc.MediaPlayer("tone.mp3")
		sound.play()

	def logCurrentFoundItems(self):
		linesFromWatchScrape = []
		sortedListings = []
		#sort the listings found with the scrape
		for eachWatchedListing in self.foundListings:
			sortedListings.append(self.foundListings[eachWatchedListing])
		sortedListings.sort(key=lambda x: x["created_at"], reverse=True)
		#create the lines from the scrape
		for eachListing in sortedListings:
			linesFromWatchScrape.append(self.rules["info"]["grailedBasePath"] + eachListing["pretty_path"] + " " + eachListing["title"])


		#now we want to get the old lines that are already in the file and append them
		linesFromFile = []
		with open("log.txt", "r") as fileStream:
			linesFromFile = fileStream.readlines()
		#clean the newline chars from the file AND collect any blacklist items
		for eachIndex in range(len(linesFromFile)):
			linesFromFile[eachIndex] = linesFromFile[eachIndex].replace("\n", "")
			if "wackting" in linesFromFile[eachIndex]: #TODO this is kind of a gross hack where i just add the string and the string with wackting in standard place removed to a list of strings that shouldn't be written. actually it's ok because it's not going to be expensive as it only has to keep enough to stop things from 1st page getting rewritten when we dont actually want them (old things that get wacktinged will just be dropped from the file once and then never put back in). But you should generalise the " wackting" thing a lil maybe
				self.blacklist.append(linesFromFile[eachIndex].replace(" idontwant", ""))
				self.blacklist.append(linesFromFile[eachIndex])
				print("adding this to the blacklist: |" + linesFromFile[eachIndex].replace("wackting", "") + "|")
		
		#finally, combine the two groups of lines and write all of the lines back to the file
		linesToWrite = []
		for each in linesFromWatchScrape:
			linesToWrite.append(each)
		for each in linesFromFile:
			if(each not in linesToWrite):
				linesToWrite.append(each)
		with open("log.txt", "w") as fileStream:
			for eachLine in linesToWrite:
				#only write it to the file if it's not on the blacklist
				#if not any(x in linesFromFile[eachIndex] for x in self.blacklist):
				#linesFromFile.remove(eachIndex)
				if eachLine not in self.blacklist:
					fileStream.write(eachLine + "\n")







if __name__ == "__main__":
	main()