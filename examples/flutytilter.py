#!/home/fluty/miniconda2/bin/python
#Written by Adam Fluty, 2/23/18

import os
import sys
import shlex
import subprocess



helpstr="""
Use the following command line syntax:
	flutytilter.py [mdoc file] [tilt order] [suffix.ext]

Tilt order: can be 'negfirst' 'posfirst' or 'chrono'
suffix.ext: the exact string that distinguishes any processed frames from the original frames (including the extension). 
"""



#input syntax check
try: filename, extension=os.path.splitext(sys.argv[1])
except:
	print(helpstr)
	sys.exit()

helps=["-h","--h","-H","--H","-help","--help"]
if sys.argv[1] in helps:
	print (helpstr)
	sys.exit()

if extension != ".mdoc":
	print("Error: File '{}' is not an 'mdoc' file".format(sys.argv[1]))
	sys.exit()
mdoc=str(sys.argv[1])

options=["negfirst","posfirst","chrono"]
try: order=str(sys.argv[2])
except:
	print(helpstr)
	sys.exit()
if order not in options:
	print(helpstr)
	sys.exit()

try: suffix, ext = sys.argv[3].rsplit(".",1)
except: suffix="_proc.mrc"

tiltname=filename.strip(".").strip("/").strip("\\").rsplit(".",1)[0]+suffix




#Parsing (thanks for the code, Michael Bell)
zval=-1
info=[]
print("MDOC: {}".format(mdoc))
with open(mdoc) as mdocf:
	for l in mdocf.readlines():
			p = l.strip()
			if "ZValue" in p:
				zval+=1
			elif p != "":
				x,y = p.split("=")[:2]
				x = x.strip()
				if x == "TiltAngle": ang=float(y)
				elif x == "SubFramePath":
					name = y.split("\\")[-1]+("_RawImages")+suffix+"."+ext
					info.append([ang,name])




#properly order images
if order=="chrono":
	sortedlist=sorted(info,key=lambda x: x[1])
else:
	sortedlist=sorted(info, key=lambda x: x[0])

if order =="posfirst":
	sortedlist=reversed(sortedlist)

filenames=""
for i in sortedlist: filenames+=i[1]+" "




#print output
print("File order:")
for i in sortedlist:
	print("{}\t-\t{}".format(i[0],i[1]+"."+ext))
print("\nWriting tilt angles to:   {}".format(tiltname+".tlt")+
	"\nWriting tilt series to:   {}".format(tiltname+".lst")+
	"\n\nNOTE: To write your '.lst' file to a proper image stack, use the following command:"+
	"\n     e2proc2d.py {} {}".format(tiltname+".lst",tiltname+".mrcs"))



#file writing:
#.tlt
newtlt=open(tiltname+".tlt","w")
for i in sortedlist:
	newtlt.write(str(i[0])+"\n")
newtlt.close()

#.lst
cmd="e2proclst.py {}--create {}".format(filenames,tiltname+".lst")
#print("\n\n"+cmd)
process=subprocess.Popen(shlex.split(cmd),stdout=subprocess.PIPE)
process.communicate()
exit_code=process.wait()
print("\nDone")


