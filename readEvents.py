from urllib2 import urlopen
import MySQLdb
from suggest.models import Feed,Dump,Temp
import pdb
from datetime import datetime
from django.db.models import Q
import re
CLIMIT="1000"
ULIMIT="10"

	

def extract_data(dic,gid):
	# To obtain data for each message 
	event={}
	for d in dic["data"]:
		#print d
		if(d.has_key('start_time')):
			stime=d['start_time']
		else:
			stime=""
		eid=d['id']
		event[eid]=stime
		#print event.stime,event.
	print event	
		             


def get_data(gid,token,next,level,visited,ulimit):
	# To travese through each facebook page 
	if(level==1):
		url="https://graph.facebook.com/"+gid+"/events/?fields=start_time"+"&limit="+ulimit+"&access_token="+token
	elif(level==2):
		url=next
	print(url)
	html=urlopen(url)
	s=html.read()
	s=s.replace("\n","\\n")
	s=s.replace("false","False")
	s=s.replace("true","True")
	s=s.replace("null","")
	dic=eval(s)
	#print(type(dic))
	#print type(dic)
	extract_data(dic,gid)
	if(dic.has_key('paging')):
		next=dic["paging"]['next']
	else:
		next=""
	return next



def run_update(gidlist):
	# to create data entries for existing urls
	visited=True
	for gid in gidlist:
		#print gid 
		level=1
		next="access_token"
		#pdb.set_trace()
		while next!="":
			next=next.replace("\/","/")
			#print next,"inside while"
			if(level==1):
				next=get_data(gid,token,next,level,visited,ULIMIT)
				level=2
			else :
				if(level==2):
					#print gid
					#print token
					#print next
					#print level
                        		#pdb.set_trace()
					next=next.replace("limit=1000","limit="+ULIMIT)
					next=get_data(gid,token,next,level,visited,ULIMIT)
					level=3
				else:
					next=get_data(gid,token,next,level,visited,ULIMIT)
				
def run_create(newlist):
	#to create data entries for new url
	visited=False
	for gid in newlist:
		#print gid 
		level=1
		next="access_token"
		#pdb.set_trace()
		while next!="":
			next=next.replace("\/","/")
			next=get_data(gid,token,next,level,visited,CLIMIT)
			level=2



def get_feed1():
	#to get the group url list from data base
	for row in Feed.objects.all().filter(Q(gstatus='U') | Q(gstatus='C') ):
		try:
			gidlist=[]
			#pdb.set_trace()
			gidlist.append(row.gid)
			run_create(gidlist)
		except Exception, e:
			print "exception occured for value ",row.gid,e 
		

def get_feed2():
	gidlist=[]
	for row in Dump.objects.all().filter(event_seen=0):
        	try:
			msg=row.msg
			msg=msg.replace("\/","/")
			for s in re.findall('http[s]?://[^\s<>"]+|www\.[^\s<>"]+', msg):
				a=str(s)
				if(a.startswith("https://www.facebook.com/events/")):
					gid=(a.strip("https://www.facebook.com/events/")).split('/')[0]
					print gid	 
			#row.event_seen=1
			#row.save()
		except Exception,e:
			print "exception occured at ",e 



token="CAAF4OpEnBMIBAMLdR9994eHdm0bmIgqOTntBXiAhEN8IwrkKjhdEUzUIet9rZCcudF7FVSS8buGJTNh8BJylkWnnUwW0brCQHmUcj1r1IDfxXCHmbogUObtza2yUvkTL15PVE2jIe6AySQikvL4bMpbnrDS5uj6OWe1DwooZCXdn7bZBj4Yvw1XHF7ZAhxEZD"
next="acces_token"
gidlist=['333039026750643','341591699228709','333961479991731','324969354265911','409595849094960','333920903329122','491533930864885','560425023973997','150766218418138','333038996750646','333918209996058','333918209996058','22586725313','333875460000333','334056999982179','334056999982179','334056999982179','333039016750644','2211303362','357239704394798','334098683311344','334001126654433','334001126654433','334063376648208','389570297764182','334504473270765','2200556148','333927766661769','333038976750648','106319576114470']
def msg_time():
	# To get time taken for running job for particular number of messages 
	for i in range(20, 25,10):
		start=datetime.now()
		ULIMIT=str(i)
		get_feed()
		print "Number of Messages ",ULIMIT, " TimeTaken ",(datetime.now()-start).microseconds
		Temp.objects.all().delete()
		Dump.objects.all().delete()

def main():
	# Calls the feed
	#get_feed1()
        get_feed2()
main()
				
