from urllib2 import urlopen
import MySQLdb
from suggest.models import Feed,Dump,Temp
import pdb
from datetime import datetime
from django.db.models import Q
CLIMIT="1000"
ULIMIT="500"

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
			#print next,"inside while"
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
	for row in Feed.objects.all().filter(Q(gstatus='U') | Q(gstatus='C') ):
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
		


gid="341591699228709"#Viterbi School of Engineering
gid="fall2013usc"
gid="333961479991731"#Computer Science
gid="324969354265911"#FREE FOOD u0040 USC  
gid="409595849094960"#USC Ticket Trades 
gid="333920903329122"# USC Graduate Students
gid="491533930864885" #usc fall 2013
gid="560425023973997"#fall2013usc
gid="150766218418138"#uscfall2013bangalore
gid="116047931844982"#uscfall2012
gid="333038996750646"#jobsandinternship
gid="333918209996058"#uscbusinessadministration
gid="22586725313"#uscfall2013official
gid="333875460000333"#uscclassof2013
gid="334056999982179"#classof2016
gid="333039016750644"#Housing
gid="2211303362"#uscacm
gid="333039026750643"#Free & For Sale 
gid="357239704394798"# usc linux group 
gid="334098683311344"#music industry
gid="334001126654433"#electrical engineering
gid="334063376648208"#psycology
gid="389570297764182"#internation students
gid="334504473270765"#student entreprenues
gid="2200556148"#ais
gid="333927766661769"#class2014
gid="333038976750648" #campustips
gid="106319576114470"#uscfall2011
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
	get_feed()

main()
				
