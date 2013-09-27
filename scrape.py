from bs4 import BeautifulSoup
from bs4 import element
import datetime
import time
import re
import json
import urllib2
from xml.dom.minidom import Document
import sys

######## HELPER FUNCTIONS #########

def getYear():
	return datetime.datetime.now().year

def createDateFromString(date_string):
	try:
		item_list = date_string.split(" ")
		month = item_list[0]
		month_int = getMonthFromString(month)
		day = item_list[1]
		day_int = int(day)
		year = getYear()
		return datetime.date(year,month_int,day_int)
	except:
		return "INVALID"

def getMonthFromString(month_string):
	try:
		title_trans=''.join(chr(c) if chr(c).isupper() or chr(c).islower() else ' ' for c in range(256))
		fixed_string = month_string.translate(title_trans).replace(' ','')
		return time.strptime(fixed_string, "%b")[1]
	except ValueError as ve:
		unconverted_value_match = re.search("unconverted data remains: (.+)", str(ve))
		if (unconverted_value_match != None):
			unconverted_value = unconverted_value_match.group(1)
			new_month_string = month_string.replace(unconverted_value, "")
			return getMonthFromString(new_month_string)
		else:
			raise ve

def getCurrentWeekFromMonday():
	getWeekFromMonday(datetime.datetime.today())
	

def getWeekFromMonday(date):
	""" Given a single date, this will output a list of dates of Monday-Sunday which contains the given date"""
	day_of_week = date.weekday()
	new_date_list = []
	for i in range(7):
		if i < day_of_week:
			time_delta = datetime.timedelta(days=(day_of_week-i))
			new_date = date - time_delta
			fixed_date = datetime.date(new_date.year, new_date.month, new_date.day)
			new_date_list.append(str(fixed_date))
		else:
			time_delta = datetime.timedelta(days=(i-day_of_week))
			new_date = date + time_delta
			fixed_date = datetime.date(new_date.year, new_date.month, new_date.day)
			new_date_list.append(str(fixed_date))
	return new_date_list

def getOnlyTags(tag):
	tag_list = []
	for item in tag.children:
		if type(item) == element.Tag:
			tag_list.append(item)
	return tag_list

def getDate():
	return datetime.datetime.now().date()

def is_menu_link(tag):
	return tag.name == 'a' and ('dining/menus/' in tag.attrs['href'] or 'menu-files' in tag.attrs['href'])


# and ('dining/menus/' in tag.attrs['href'])


def getMuddURL():
	url = "http://www.hmcdining.com/index.html"
	usock = urllib2.urlopen(url)
	data = usock.read()
	usock.close()

	soup = BeautifulSoup(data)
	result = soup.find_all(is_menu_link)
	return ["http://www.hmcdining.com/" + i.attrs['href'] for i in result]
	#return "http://www.hmcdining.com/" + result[-1].attrs['href']



##### Main Scrapers #####

def scrape_mudd(menu_data):
	url_list = getMuddURL()
	for url in url_list:
		# print url
		if url == "FAILED":
			return menu_data
		usock = urllib2.urlopen(url)
		data = usock.read()
		# print str(data)
		usock.close()

		# soup = BeautifulSoup(open("mudd.html"), "lxml")
		soup = BeautifulSoup(data)

		body_tag = soup.html.body

		#### get important sections of body - top and container
		top_tag = None
		container_tag = None
		for tag in body_tag.contents:
			if (type(tag) == element.Tag):
				try:
					if (tag["id"] == "top"):
						top_tag = tag
					elif (tag["id"] == "container"):
						container_tag = tag
				except KeyError:
					continue

		#### get dates from top tag ####
		topTbl_tag = None
		for tag in top_tag.contents:
			if (type(tag) == element.Tag):
				topTbl_tag = tag

		row_count = 1
		dateRow_tag = None

		for tag in topTbl_tag.contents:
			if (type(tag) == element.Tag and tag.name == "tr"):
				if row_count == 2:
					dateRow_tag = tag
					break
				row_count += 1

		date_list = []
		ordered_date_list = []
		for cell in dateRow_tag.contents:
			if (type(cell) == element.Tag):
				date_list.append(cell.text.strip().replace('  ',' '))
		for date_string in date_list:
			# print date_string
			formatted_date = createDateFromString(date_string.encode("ascii","ignore"))
			ordered_date_list.append(str(formatted_date))
		# print ordered_date_list

		#### initialize MUDD sections for each date in the global menu data dictionary ####
		#### NOTE that there will be one "INVALID" in ordered_date_list. initialize that too and delete it later ####
		#### Keeping the invalid in makes dealing with rows in the future easier ####
		for item in ordered_date_list:
			if item not in menu_data:
				menu_data[item] = {"MUDD" : {}}
			else:
				menu_data[item]["MUDD"] = {}
		# print ordered_date_list
		#### Fill MUDD sections for each date ####
		table_tag = container_tag.contents[1]
		
		#### Go row by row through the table ####
		in_breakfast_brunch = False
		in_lunch_brunch = False
		in_dinner = False
		curr_station = ""
		count = 0
		ordered_meal_list = []
		for row_tag in table_tag.contents:
			### ignore non rows
			try:
				if (type(row_tag) == element.Tag):
					#### Get rid of all the navigable strings in the row
					cell_tags = []
					for tag in row_tag.contents:
						if (type(tag) == element.Tag):
							cell_tags.append(tag)
					#### Ignore the divider rows and day headers strewn about
					if "divider_row" in str(cell_tags[0]['class']) or "day_header" in str(cell_tags[0]['class']):
						continue
					if "meal_row" in str(cell_tags[0]['class']):
						curr_station = ""
						ordered_meal_list = []
						for index in range(len(cell_tags)):
							ordered_meal_list.append(cell_tags[index].text.strip().lower())
					#### Then go column by column
					else:
						# print cell_tags
						# print ordered_meal_list
						for index in range(len(cell_tags)):
							curr_meal = ordered_meal_list[index]
							if index == 0:
								## This cell is where stations are labeled. If the station is empty, then we're already in a station. Else it's a new station
								if cell_tags[index].text.strip() != "":
									curr_station = cell_tags[index].text.strip()
								# print_string += curr_station
							else:
								food_item = cell_tags[index].text.strip()
								#### add food item to menu data
								if curr_meal not in menu_data[ordered_date_list[index]]["MUDD"]:
									menu_data[ordered_date_list[index]]["MUDD"][curr_meal] = {}
								if curr_station not in menu_data[ordered_date_list[index]]["MUDD"][curr_meal]:
									menu_data[ordered_date_list[index]]["MUDD"][curr_meal][curr_station] = []
								if food_item != "":
									menu_data[ordered_date_list[index]]["MUDD"][curr_meal][curr_station].append(food_item)
			except:
				continue
	return menu_data



def scrape_pomona(menu_choice, menu_data):
	ordered_date_list = []
	ordered_meal_list = []

	URL = ""
	menu_name = ""
	if (menu_choice == 1):
		URL = "http://www.pomona.edu/administration/dining/menus/frary.aspx"
		menu_name = "FRARY"
	elif (menu_choice == 2):
		URL = "http://www.pomona.edu/administration/dining/menus/frank.aspx"
		menu_name = "FRANK"
	else:
		URL = "http://www.pomona.edu/administration/dining/menus/oldenborg.aspx"
		menu_name = "OLDENBORG"

	usock = urllib2.urlopen(URL)
	data = usock.read()
	usock.close()

	# with open("oldenborg.html","r") as f:
	# 	data = f.read()

	soup = BeautifulSoup(data)
	menus_tag = soup.find(id="menus")
	if menus_tag != None:
		title = soup.html.head.title.text
		date_match = re.search("[A-Za-z ]+[0-9]+/[0-9]+ - ([0-9]+)/([0-9]+)/([0-9]+)", title.encode("ascii","ignore"))
		date = ""
		if (date_match != None):
			month = date_match.group(1)
			day = date_match.group(2)
			year = date_match.group(3) if len(date_match.group(3)) == 4 else "20" + date_match.group(3)
			end_date = datetime.date(int(year), int(month), int(day))
			ordered_date_list = getWeekFromMonday(end_date)
			# for i in range(1,7):
			# 	time_delta = datetime.timedelta(days=i)
			# 	next_date = start_date + time_delta
			# 	ordered_date_list.append(next_date)
		else:
			#### If we can't get the date for some reason, use this weeks date.
			ordered_date_list = getCurrentWeekFromMonday()
		### Initialize the dates in the global menu_data 
		# print ordered_date_list
		for date in ordered_date_list:
			if date not in menu_data:
				menu_data[date] = {menu_name : {}}
			else:
				menu_data[date][menu_name] = {}
	
	
		menu_list = []
		for m in menus_tag.contents:
			if type(m) == element.Tag and m.name == "table":
				menu_list.append(m)
		### Need to add catch if list sizes are different
		if len(menu_list) < len(ordered_date_list):
			# print "mismatched lengths"
			for i in range(len(ordered_date_list) - len(menu_list)):
				menu_list.append("")
		for index in range(len(menu_list)):
			if type(menu_list[index]) != str:
				row_list = getOnlyTags(menu_list[index])
				count = 0
				meal_list = []
				for row in row_list:
					if count == 0:
						## Get the meal titles. The first element is the "Station title" - so ignore it
						meal_list = getOnlyTags(row)[1:]
						count += 1
					else:
						cell_list = getOnlyTags(row)
						station = cell_list[0].text.strip().lower()
						# now ignore the station cell since we already dealt with it
						# cell_list should be the same length of meal_list. Otherwise this will crash.
						cell_list = cell_list[1:]
						for i in range(len(cell_list)):
							## The food string is a comma separated list
							food_string = cell_list[i].text.strip().lower()
							food_list = food_string.split(",")
							meal_name = meal_list[i].text.strip().lower()
							if meal_name not in menu_data[ordered_date_list[index]][menu_name].keys():
								menu_data[ordered_date_list[index]][menu_name][meal_name] = {station : []}
							if food_list != ['']:
								menu_data[ordered_date_list[index]][menu_name][meal_name][station] = food_list

	return menu_data


def scrape_rss(menu_data,URL,hall_name):
	
	usock = urllib2.urlopen(URL)
	data = usock.read()
	usock.close()

	# print str(data)

	soup = BeautifulSoup(data)
	# print soup == None
	for i in soup.find_all("item"):
		# print "NEW ITEM = " + str(i)
		title = i.title.text
		date = str(datetime.datetime.strptime(title,"%a, %d %b %Y")).replace(" 00:00:00","").strip()
		# print date
		if date not in menu_data.keys():
			menu_data[date] = {hall_name : {}}
		else:
			menu_data[date][hall_name] = {}
		data = i.description.text
		curr_meal = ""
		for line in data.split("\n"):
			try:
				# print "line = " + line
				if "<h4>" in line:
					food_match = re.search(r"<h4>\[([A-Za-z @']+)\](.*)&nbsp;</h4>", line.encode("ascii","ignore"))
					if (food_match != None):
						station = food_match.group(1)
						food_items = re.split(r'[;,]',food_match.group(2))

						if curr_meal != "ERROR":
							if station not in menu_data[date][hall_name][curr_meal].keys():
								menu_data[date][hall_name][curr_meal][station] = []
							curr_items = menu_data[date][hall_name][curr_meal][station]
							curr_items = curr_items + food_items
							menu_data[date][hall_name][curr_meal][station] = curr_items

				elif "<h3>" in line:
					## It's a meal header
					meal_match = re.search(r"<h3>(\w+)</h3>",line.encode("ascii","ignore"))
					if (meal_match != None):
						curr_meal = meal_match.group(1)
						if curr_meal not in menu_data[date][hall_name].keys():
							menu_data[date][hall_name][curr_meal] = {}
					else:
						curr_meal = "ERROR"
			except:
				continue

	return menu_data


				
def clean_menu_data(menu_data):
	
	new_md = dict(menu_data)
	for key in menu_data.keys():
		try:
			date_key = datetime.datetime.strptime(key,'%Y-%m-%d').date()
			if date_key < (datetime.datetime.today() - datetime.timedelta(hours=8)).date():
				del new_md[key]
			else:
				for menu in menu_data[key].keys():
					for meal in menu_data[key][menu].keys():
						for station in menu_data[key][menu][meal].keys():
							l = []
							for item in menu_data[key][menu][meal][station]:
								l.append(re.sub(r"\s+"," ",item))
							menu_data[key][menu][meal][station] = l
							if menu_data[key][menu][meal][station] == []:
								del new_md[key][menu][meal][station]
						if new_md[key][menu][meal] == {}:
							del new_md[key][menu][meal]
					if new_md[key][menu] == {}: 
						del new_md[key][menu]
				if new_md[key] == {}:
					del new_md[key]
		except ValueError:
			del new_md[key]
	return new_md


def write_md_to_xml(menu_data):
	doc = Document()
	main_element = doc.createElement("alldays")
	doc.appendChild(main_element)
	for date in menu_data.keys():
		# print date
		date_element = doc.createElement("date")
		date_element.setAttribute("name",str(date))
		for menu in menu_data[date].keys():
			# print menu
			menu_element = doc.createElement("menu")
			menu_element.setAttribute("name",menu)
			for meal in menu_data[date][menu].keys():
				meal_element = doc.createElement("meal")
				meal_element.setAttribute("name",meal)
				for station in menu_data[date][menu][meal].keys():
					station_element = doc.createElement("station")
					station_element.setAttribute("name",station)
					for food_item in menu_data[date][menu][meal][station]: 
						food_element = doc.createElement("menuitem")
						text = doc.createTextNode(food_item.strip())
						food_element.appendChild(text)
						station_element.appendChild(food_element)
					meal_element.appendChild(station_element)
				menu_element.appendChild(meal_element)
			date_element.appendChild(menu_element)
		main_element.appendChild(date_element)
	xml = doc.toprettyxml()
	xml = xml.encode("ascii", "ignore")
	xml = xml.replace("&amp;","and")
	return xml

def write_md_to_json(menu_data):
	""" want json format to be 
	{'dates': [
		{'date':'09-27-2012', menus': [
			{'name' : 'MUDD', 'meals': [
				{'name' = 'lunch', 'stations': [
					{'name' = 'grill', 'items': ['food1','food2'] } ]
				}, {another meal}, ... ]
			}, {another menu}, ... ]
		}, {another date}, ...]
	}
	menu-data reflects this already so the conversion should be easy."""
	overall_dict = {'dates':[]}
	for date in menu_data.keys():
		date_dict = {'date':date,'menus':[]}
		for menu in menu_data[date].keys():
			menu_dict = {'name':menu,'meals':[]}
			for meal in menu_data[date][menu].keys():
				meal_dict = {'name':meal,'stations':[]}
				for station in menu_data[date][menu][meal].keys():
					station_dict = {'name':station,'items':menu_data[date][menu][meal][station]}
					meal_dict['stations'].append(station_dict)
				menu_dict['meals'].append(meal_dict)
			date_dict['menus'].append(menu_dict)
		overall_dict['dates'].append(date_dict)
	return json.dumps(overall_dict)

def scrape_all():
	# try:

	menu_data = {}
	menu_data = scrape_mudd(menu_data)
	menu_data = scrape_pomona(1,menu_data)
	menu_data = scrape_pomona(2,menu_data)
	menu_data = scrape_pomona(3,menu_data)
	menu_data = scrape_rss(menu_data,"http://www.cafebonappetit.com/rss/menu/219","PITZER")
	menu_data = scrape_rss(menu_data,"http://www.cafebonappetit.com/rss/menu/50","CMC")	
	menu_data = clean_menu_data(menu_data)
	# print menu_data
	# for i in menu_data.keys():
	# 	print i + ":\n\t"
	# 	for j in menu_data[i].keys():
	# 		print j
	xml = write_md_to_xml(menu_data)
	json = write_md_to_json(menu_data)
	return (xml,json)
	# except Exception as e:
	# 	print "hit an error: " + str(e)


# def main():
# 	xml, json = scrape_all()
# 	#print type(xml)
# 	print json

# if __name__ == "__main__":
#  	main()



		












