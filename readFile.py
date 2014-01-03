from urllib2 import urlopen
import MySQLdb
from suggest.models import Feed,Dump,Temp
import pdb
from datetime import datetime
from django.db.models import Q
CLIMIT="1000"
ULIMIT="20"

def insert_data(pid,gname,gid,pmessage,username,userid,ctime,utime):
	# To insert messge data into database 
	ctime=ctime.split('+')[0]
	utime=utime.split('+')[0]
	try:
		Dump.objects.create(pid=pid,gp=gname,gid=gid,
                                   msg=pmessage,name=username,nameid=userid,ctime=ctime,utime=utime,clink="",llink="",link="",event_seen=0)
		Temp.objects.create(pid=pid,gp=gname,gid=gid,
			        msg=pmessage,name=username,nameid=userid,ctime=ctime,utime=utime,clink="",llink="",link="")
	except MySQLdb.Error,e:	  
		print "eception occured",e
		try:
			Temp.objects.create(pid=pid,gp=gname,gid=gid,
                                msg=pmessage,name=username,nameid=userid,ctime=ctime,utime=utime,clink="",llink="",link="")
		except MySQLdb.Error,e:
			print "eception occured",e
		
	except Exception,e:
		print "exception occured for post id",pid,e 
	

def extract_data(dic,gid):
	# To obtain data for each message 
	for d in dic["data"]:
		#print d
        	pid=d['id']
        	username=d['from']['name']
        	userid=d['from']['id']
        	gname= d['to']['data'][-1]['name']
		if(d.has_key('message')):
	        	pmessage= d['message']
		else:
			pmessage="" 
		#print "post id",pid,"is obtained"
        	ctime=d['created_time']
		utime=d['updated_time']
		pmessage=pmessage.replace("(","")
		pmessage=pmessage.replace(")","")
		pmessage=pmessage.replace("'","")
       		username=username.replace("'","")   
        	insert_data(pid,gname,gid,pmessage,username,userid,ctime,utime)
	
		             


def get_data(gid,token,next,level,visited,ulimit):
	# To travese through each facebook page 
	if(level==1):
		url="https://graph.facebook.com/"+gid+"/feed?limit="+ulimit+"&access_token="+token
	elif(level==2):
		url=next
	else :
		url=next+"&access_token="+token
	print(url)
	html=urlopen(url)
	s=html.read()
	s=s.replace("\n","\\n")
	s=s.replace("false","False")
	s=s.replace("true","True")
	s=s.replace("null","")
	dic=eval(s)
	#print type(dic)
	extract_data(dic,gid)
	if(visited==False):
		if(dic.has_key('paging')):
			next=dic["paging"]['next']
		else:
			next=""
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
			if(level==1):			
				next=get_data(gid,token,next,level,visited,CLIMIT)
				level=2
			else :
				if(level==2):
					#print gid
					#print token
					#print next
					#print level
                        		#pdb.set_trace()
					next=next.replace("limit=1000","limit=500")
					next=get_data(gid,token,next,level,visited,CLIMIT)
					level=3
				else:
					next=get_data(gid,token,next,level,visited,CLIMIT)



def get_feed():
	#to get the group url list from data base
	for row in Feed.objects.all().filter( Q(gstatus='C') | Q(gstatus='U') ):
		try:
			gidlist=[]
			#pdb.set_trace()
			gidlist.append(row.gid)
			if(row.gstatus=='U'):
				run_update(gidlist)
			elif(row.gstatus=='C'):
				run_create(gidlist)
				row.gstatus='U'
			row.gutime=datetime.now()
			row.save()
		except Exception, e:
			print "exception occured for value ",row.gid,e 
		


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
	get_feed()

main()
				
