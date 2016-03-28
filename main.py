import simplejson as json
import requests 
from bs4 import BeautifulSoup
import yaml
import regex
import time




class Scraper(object):
	def __init__(self, rulesFileName):
		with open(rulesFileName, "r", encoding = "utf-8") as fileStream:
			self.rules = yaml.load(fileStream)
			self.foundListings = {}

	def catchUp(self):
		pageNumber = 1
		oldDate = 99999999999999999#this is for debug### JUST CHECKING AS WE GO BACK THROUGH THEM THAT THEY ARE BEING GIVEN TO US IN THE ORDER THAT THEY WERE POSTED TO THE SITE
		#while True: increment pageNumber til we reach where we were up to
		while(True):
			response = requests.get(self.rules["rootUrlStart"] + str(pageNumber) + self.rules["rootUrlEnd"])
			pageJSON = json.loads(response.text)
			for eachListing in pageJSON["data"]:
				try:
					print("checking listing with title:" + eachListing["title"])
				except UnicodeEncodeError:
					print("failed to print that title fam")
				unsanitisedDate = eachListing["created_at"]
				sanitisedDate = self.sanitiseDate(unsanitisedDate)
				print(sanitisedDate)
				
				assert(oldDate >= sanitisedDate)
				oldDate = sanitisedDate# this is for debug###
				if(self.sanitiseDate(self.rules["gotUpTo"]) > sanitisedDate):
					print("WE GOT UP TO WHERE WE WATCHED TIL LAST TIME, SO ENDING THE CATCHUP PHASE")
					print(sanitisedDate)
					return
				if(self.decideIfRelevant(eachListing)):
					print("while catching up, we found: " + eachListing["title"])
					self.foundListings[eachListing["title"]] = eachListing
			pageNumber += 1


			#TODO: WILL WANT TO HAVE AN "ENTRY" OBJECT DEFINED IN YAML SO THAT WE CAN STIPULATE E.G. MUST BE BY ONE OF THESE DESIGNERS REGEX, MUST HAVE THESE REGEXES IN THE TITLE OR DESC, MUST NOT HAVE THESE REGEXES
	def decideIfRelevant(self, listing):
		#check the title and description for our patterns
		for eachRegex in self.rules["goodPatterns"]:
			if(regex.search(eachRegex, listing["description"])):
				return True
			if(regex.search(eachRegex, listing["title"])):
				return True
		#check the designer
		for eachRegex in self.rules["goodDesigners"]:
			if(regex.search(eachRegex, listing["designer"]["name"])):
				return True
		return False

	#NOTE that this might print out that it is finding the old stuff over and over again, but it's just reputting the old stuff back into the dictionary 
	def watch(self, interval):
		response = requests.get(self.rules["rootUrlStart"] + str(1) + self.rules["rootUrlEnd"])
		pageJSON = json.loads(response.text)
		for eachListing in pageJSON["data"]:
			if(self.decideIfRelevant(eachListing)):
				self.foundListings[eachListing["title"]] = eachListing #TODO: should be a comdination of the title and the id for uniqueness. Should check whether it's already in tehre before adding it and play a sound if it adds something new.
				print("while watching, we found:" + eachListing["title"])
		time.sleep(interval)
		self.watch(interval)


	def sanitiseDate(self, dateString):
		return int(regex.sub("[a-z|A-Z|:|.|-]", "", dateString))




def main():
	scraper = Scraper("rules.yml")
	scraper.catchUp()
	print("catchup phase finished :)")
	scraper.watch(5)



	#response = requests.get(rules["rootUrlStart"] + str(pageNumber) + rules["rootUrlStart"], "utf8")
	#soup = BeautifulSoup(response.text, "html.parser")
	#jsonData = json.loads(response.text)
	#print(jsonData["data"][0]["created_at"])



if __name__ == "__main__":
	main()