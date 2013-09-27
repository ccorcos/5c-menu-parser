import webapp2
import scrape

from google.appengine.ext import db
from google.appengine.api import memcache


class MenuXML(db.Model):
	xml = db.TextProperty()
	json = db.TextProperty()


class MainPage(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Access-Control-Allow-Origin'] = '*'
		self.response.headers['Content-Type'] = 'text/plain'
		curr_date = scrape.getDate()

		# First check if the menu has been cached
		cached_result = memcache.get(str(curr_date))
		if cached_result is None:
			# if the menu hasnt been cached, check the database
			date_key = db.Key.from_path('MenuXML', str(curr_date))
			db_result = MenuXML.get(db.Key.from_path('MenuXML', str(curr_date)))

			# if the database is empty, then parse
			if db_result == None or str(db_result.xml)=="None":
				new_xml, new_json = scrape.scrape_all()

				# add to database
				curr_date = scrape.getDate()
				mx = MenuXML(xml=new_xml,json=new_json,key_name=str(curr_date))
				mx.put()

				# add to memcache
				if not memcache.add(str(curr_date), mx, 7200): #keep for 1 hour. menu updates every hour
					logging.error('Memcache set failed.')

				### Delete old entries
				all_entries = MenuXML.all()
				to_be_deleted = all_entries.filter("__key__ != ", db.Key.from_path('MenuXML', str(curr_date)))
				db.delete(to_be_deleted)

				self.response.write(str(new_xml))

			# db_result is valie
			else: 
				# add to memcache
				if not memcache.add(str(curr_date), db_result, 7200): #keep for 1 hour. menu updates every hour
					logging.error('Memcache set failed.')
				# return xml
				self.response.write(str(db_result.xml))

		#otherwise, return the cached data		
		else:
			self.response.write(str(cached_result.xml))

class Get_JSON(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Access-Control-Allow-Origin'] = '*'
		self.response.headers['Content-Type'] = 'text/plain'
		curr_date = scrape.getDate()

		# First check if the menu has been cached
		cached_result = memcache.get(str(curr_date))
		if cached_result is None:
			# if the menu hasnt been cached, check the database
			date_key = db.Key.from_path('MenuXML', str(curr_date))
			db_result = MenuXML.get(db.Key.from_path('MenuXML', str(curr_date)))

			# if the database is empty, then parse
			if db_result == None or str(result.xml)=="None":
				new_xml, new_json = scrape.scrape_all()

				# add to database
				curr_date = scrape.getDate()
				mx = MenuXML(xml=new_xml,json=new_json,key_name=str(curr_date))
				mx.put()

				# add to memcache
				if not memcache.add(str(curr_date), mx, 7200): #keep for 1 hour. menu updates every hour
					logging.error('Memcache set failed.')

				### Delete old entries
				all_entries = MenuXML.all()
				to_be_deleted = all_entries.filter("__key__ != ", db.Key.from_path('MenuXML', str(curr_date)))
				db.delete(to_be_deleted)

				self.response.write(str(new_json))

			# db_result is valie
			else: 
				# add to memcache
				if not memcache.add(str(curr_date), db_result, 7200): #keep for 1 hour. menu updates every hour
					logging.error('Memcache set failed.')
				# return xml
				self.response.write(str(db_result.json))

		#otherwise, return the cached data		
		else:
			self.response.write(str(cached_result.json))

class Get_XML(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Access-Control-Allow-Origin'] = '*'
		self.response.headers['Content-Type'] = 'text/plain'
		curr_date = scrape.getDate()

		# First check if the menu has been cached
		cached_result = memcache.get(str(curr_date))
		if cached_result is None:
			# if the menu hasnt been cached, check the database
			date_key = db.Key.from_path('MenuXML', str(curr_date))
			db_result = MenuXML.get(db.Key.from_path('MenuXML', str(curr_date)))

			# if the database is empty, then parse
			if db_result == None or str(result.xml)=="None":
				new_xml, new_json = scrape.scrape_all()

				# add to database
				curr_date = scrape.getDate()
				mx = MenuXML(xml=new_xml,json=new_json,key_name=str(curr_date))
				mx.put()

				# add to memcache
				if not memcache.add(str(curr_date), mx, 7200): #keep for 1 hour. menu updates every hour
					logging.error('Memcache set failed.')

				### Delete old entries
				all_entries = MenuXML.all()
				to_be_deleted = all_entries.filter("__key__ != ", db.Key.from_path('MenuXML', str(curr_date)))
				db.delete(to_be_deleted)

				self.response.write(str(new_xml))

			# db_result is valie
			else: 
				# add to memcache
				if not memcache.add(str(curr_date), db_result, 7200): #keep for 1 hour. menu updates every hour
					logging.error('Memcache set failed.')
				# return xml
				self.response.write(str(db_result.xml))

		#otherwise, return the cached data		
		else:
			self.response.write(str(cached_result.xml))

class Update(webapp2.RequestHandler):
	def get(self):
		### Add new entry
		new_xml, new_json = scrape.scrape_all()
		curr_date = scrape.getDate()
		mx = MenuXML(xml=new_xml,json=new_json,key_name=str(curr_date))
		mx.put()

		### Delete old entries
		all_entries = MenuXML.all()
		to_be_deleted = all_entries.filter("__key__ != ", db.Key.from_path('MenuXML', str(curr_date)))
		db.delete(to_be_deleted)

		# Clear memcache entries
		memcache.flush_all()

		# Add to memcache
		if not memcache.add(str(curr_date), mx, 7200): #keep for 1 hour. menu updates every hour
			logging.error('Memcache set failed.')

class ViewDB(webapp2.RequestHandler):
	def get(self):
		all_entries = MenuXML.all()
		for entity in all_entries:
			if entity.xml != None or entity.json != None:
				self.response.write("NEW ENTRY - " + str(entity.key().name()) + "\n\n" + entity.xml + "\n\n" + entity.json + "\n\n")
			else:
				self.response.write("NO ENTRIES")



app = webapp2.WSGIApplication([('/',MainPage),('/json',Get_JSON),('/xml',Get_XML),('/update',Update),('/viewdb',ViewDB)], debug=True)

