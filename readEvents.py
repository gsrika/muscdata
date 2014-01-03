from urllib2 import urlopen
import MySQLdb
from suggest.models import Feed,Dump,Temp
import pdb
from datetime import datetime
from django.db.models import Q
import re
import urllib
import json

CLIMIT="10000"
ULIMIT="10"

def event_grab(event_id):
    access_token = "CAAF4OpEnBMIBAMLdR9994eHdm0bmIgqOTntBXiAhEN8IwrkKjhdEUzUIet9rZCcudF7FVSS8buGJTNh8BJylkWnnUwW0brCQHmUcj1r1IDfxXCHmbogUObtza2yUvkTL15PVE2jIe6AySQikvL4bMpbnrDS5uj6OWe1DwooZCXdn7bZBj4Yvw1XHF7ZAhxEZD"
    url = "https://graph.facebook.com/"+event_id+"?access_token="+access_token
    request = urllib.urlopen(url)
    event_dict = json.load(request)
    keys = ['event_id','owner_name','owner_id','name','description','start_time','end_time','is_date_only','location','latitude','longitude','venue_id','state','city', 'street','zip']
    insert_dict = {}
    for k in keys:
        if k in event_dict.keys():
	    insert_dict[k] =event_dict[k]
        else:
            insert_dict[k] = ''
    if insert_dict['is_date_only'] == True and insert_dict["start_time"]!='':
        insert_dict["start_time"] += "T00:00:00-0800"
    if insert_dict['start_time']=='' or (not should_grab_date(insert_dict["start_time"])):
        return
    if insert_dict['end_time']=='':
        s = facebook_date(insert_dict["start_time"])
        insert_dict["end_time"] = datetime(s.year,s.month,s.day,11,59)
    else:
        insert_dict["end_time"] = facebook_date(insert_dict["end_time"])
    insert_dict["event_id"] = event_id
    insert_dict["owner_id"] = event_dict["owner"]["id"]
    insert_dict["owner_name"] = event_dict["owner"]["name"]
    if "venue" in event_dict.keys():
        if "country" in event_dict["venue"].keys() and event_dict["venue"]["country"] != "United States":
            return
        if "latitude" in event_dict["venue"].keys():
            insert_dict["latitude"] = event_dict["venue"]["latitude"]
        else:
            insert_dict["latitude"] = "NULL"
        if "longitude" in event_dict["venue"].keys():
            insert_dict["longitude"] = event_dict["venue"]["longitude"]
        else:
            insert_dict["longitude"] = "NULL"
        if "id" in event_dict["venue"].keys():
            insert_dict["venue_id"] = event_dict["venue"]["id"]
        else:
            insert_dict["venue_id"] = "NULL"
        if "city" in event_dict["venue"].keys():
            insert_dict["city"] = event_dict["venue"]["city"]
        if "street" in event_dict["venue"].keys():
            insert_dict["street"] = event_dict["venue"]["street"]
        if "state" in event_dict["venue"].keys():
            insert_dict["state"] = event_dict["venue"]["state"]
        if "zip" in event_dict["venue"].keys():
            insert_dict["zip"] = event_dict["venue"]["zip"]
        else:
            insert_dict["zip"] = "NULL"
    insert_dict["active"] = True
    insert_dict['start_time'] = facebook_date(insert_dict['start_time'])
    for k in ['venue_id','zip','is_date_only']:
	if  insert_dict[k] == "" :
	    insert_dict[k] = "NULL"    
    for key in insert_dict.keys():
        if insert_dict[key].__class__ == str :
            insert_dict[key] = MySQLdb.escape_string(insert_dict[key])
	elif insert_dict[key].__class__ == unicode :
	    insert_dict[key] = insert_dict[key].encode("ascii","replace")
	    insert_dict[key] = insert_dict[key].replace("?","")
	    insert_dict[key] = MySQLdb.escape_string(insert_dict[key])
    insert_statement = "Insert into suggest_event (event_id,owner_name,owner_id,name,description,start_time,end_time,is_date_only,location,latitude,longitude,venue_id,state,city,street,zipcode,is_active) VALUES"\
                                "(%s,'%s',%s,'%s','%s','%s','%s',%s,'%s',%s,%s,%s,'%s','%s','%s',%s,1) "\
                                "ON DUPLICATE KEY UPDATE "\
                                "owner_name='%s',owner_id=%s,name='%s',description='%s',start_time='%s',end_time='%s',is_date_only=%s,location='%s',latitude=%s,longitude=%s,venue_id=%s,state='%s',city='%s',street='%s',zipcode=%s,is_active=1;"\
                                %(insert_dict["event_id"],insert_dict["owner_name"],insert_dict["owner_id"],insert_dict["name"],insert_dict["description"],insert_dict["start_time"],insert_dict["end_time"],insert_dict["is_date_only"],insert_dict["location"],insert_dict["latitude"],insert_dict["longitude"],insert_dict["venue_id"],insert_dict["state"],insert_dict["city"],insert_dict["street"],insert_dict["zip"],insert_dict["owner_name"],insert_dict["owner_id"],insert_dict["name"],insert_dict["description"],insert_dict["start_time"],insert_dict["end_time"],insert_dict["is_date_only"],insert_dict["location"],insert_dict["latitude"],insert_dict["longitude"],insert_dict["venue_id"],insert_dict["state"],insert_dict["city"],insert_dict["street"],insert_dict["zip"])
    try:
	db=MySQLdb.connect(host="localhost",user="root",passwd="root",db="mu")
        cur=db.cursor()
        cur.execute(insert_statement)
        cur.close()
	print "success"
        db.commit()
        db.close()
    except MySQLdb.Error,e:
        print "eception occured in inserting",e,event_id
	raise


def should_grab_date(date_time_string):
	return facebook_date(date_time_string).date() >=datetime(2013,11,1,0,0).date()
	#return facebook_date(date_time_string).date() >= datetime.now().date()

def facebook_date(date_time_string):
    if(len(date_time_string)==24):
	    date_time_string = date_time_string[0:-5]
    return datetime.strptime(date_time_string,'%Y-%m-%dT%H:%M:%S')
	

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
		event_grab(eid)	
		             


def get_data(gid,token,next,level,visited,ulimit):
	# To travese through each facebook page 
	if(level==1):
		url="https://graph.facebook.com/"+gid+"/events/?fields=start_time"+"&limit="+ulimit+"&access_token="+token
	elif(level==2):
		url=next
	#print(url)
	html=urlopen(url)
	s=html.read()
	s=s.replace("\n","\\n")
	s=s.replace("false","False")
	s=s.replace("true","True")
	s=s.replace("null","")
	dic=eval(s)
	extract_data(dic,gid)
	if(dic.has_key('paging')):
		if "next" in dic.keys():
			next=dic["paging"]['next']
		else:
			next=""
	else:
		next=""
	return next
				
def run_create(newlist):
	#to create data entries for new url
	visited=False
	for gid in newlist:
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
				a=s.encode("ascii","replace")
				if(a.startswith("https://www.facebook.com/events/")):
					gid=(a.strip("https://www.facebook.com/events/")).split('/')[0]
					event_grab(gid)
			row.event_seen=1
			row.save()
		except Exception,e:
			print "exception occured at ",e,gid,s,row.pid  


token="CAAF4OpEnBMIBAMLdR9994eHdm0bmIgqOTntBXiAhEN8IwrkKjhdEUzUIet9rZCcudF7FVSS8buGJTNh8BJylkWnnUwW0brCQHmUcj1r1IDfxXCHmbogUObtza2yUvkTL15PVE2jIe6AySQikvL4bMpbnrDS5uj6OWe1DwooZCXdn7bZBj4Yvw1XHF7ZAhxEZD"
next="acces_token"
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
	get_feed1()
	start=datetime.now()
        get_feed2()
	print (datetime.now()-start).seconds
main()
				
