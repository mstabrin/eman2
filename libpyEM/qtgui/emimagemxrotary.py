#!/usr/bin/env python

#
# Author: Steven Ludtke (sludtke@bcm.edu)
# Copyright (c) 2000-2006 Baylor College of Medicine
#
# This software is issued under a joint BSD/GNU license. You may use the
# source code in this file under either license. However, note that the
# complete EMAN2 and SPARX software packages have some GPL dependencies,
# so you are responsible for compliance with the licenses of these packages
# if you opt to use BSD licensing. The warranty disclaimer below holds
# in either instance.
#
# This complete copyright notice must be included in any revised version of the
# source code. Additional authorship citations may be added, but existing
# author citations must be preserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston MA 02111-1307 USA
#
#

from PyQt4 import QtCore, QtGui, QtOpenGL
from PyQt4.QtCore import Qt
from OpenGL import GL,GLU,GLUT
from OpenGL.GL import *
from OpenGL.GLU import *
from valslider import ValSlider
from math import *
from EMAN2 import *
import EMAN2
import sys
import numpy
from emimageutil import ImgHistogram,EMParentWin
from weakref import WeakKeyDictionary
from pickle import dumps,loads
from PyQt4.QtGui import QImage
from PyQt4.QtCore import QTimer

from emglobjects import EMOpenGLFlagsAndTools

from emfloatingwidgets import EMGLRotaryWidget, EMGLView2D,EM3DWidget


class EMImageMXRotary(QtOpenGL.QGLWidget):
	"""A QT widget for rendering EMData objects. It can display stacks of 2D images
	in 'matrix' form on the display. The middle mouse button will bring up a
	control-panel. The QT event loop must be running for this object to function
	properly.
	"""
	allim=WeakKeyDictionary()
	def __init__(self, data=None,parent=None):
		self.image_rotary = None
		#self.initflag = True
		self.mmode = "drag"

		fmt=QtOpenGL.QGLFormat()
		fmt.setDoubleBuffer(True);
		#fmt.setDepthBuffer(True)
		QtOpenGL.QGLWidget.__init__(self,fmt, parent)
		EMImageMXRotary.allim[self]=0
		
		
		self.image_rotary = EMImageMXRotaryCore(data,self)
		
		self.imagefilename = None
		
		self.fov = 20
		self.aspect = 1.0
		self.zNear = 1
		self.zFar = 5000
		
		self.animatables = []
		
		self.timer = QTimer()
		QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.timeout)
		self.timer.start(10)
		
	def setData(self,data):
		self.image_rotary.setData(data)
	
	def get_optimal_size(self):
		lr = self.image_rotary.rotary.get_suggested_lr_bt_nf()
		width = lr[1] - lr[0]
		height = lr[3] - lr[2]
		return [width+80,height+20]
	
	def timeout(self):
		
		if len(self.animatables) == 0: return
		
		for i,animatable in enumerate(self.animatables):
			if not animatable.animate(time.time()):
				# this could be dangerous
				self.animatables.pop(i)
		
		self.updateGL()
		
	def register_animatable(self,animatable):
		self.animatables.append(animatable)
	
	def setImageFileName(self,name):
		#print "set image file name",name
		self.imagefilename = name
		
	def getImageFileName(self):
		return self.imagefilename
	
	def initializeGL(self):
		glClearColor(0,0,0,0)
		
		glLightfv(GL_LIGHT0, GL_AMBIENT, [0.1, 0.1, 0.1, 1.0])
		glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
		glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
		glLightfv(GL_LIGHT0, GL_POSITION, [0.1,.1,1.,0.])
	
		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		
		glEnable(GL_DEPTH_TEST)
		
		glEnable(GL_NORMALIZE)
		
		glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
		glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST)
		glHint(GL_TEXTURE_COMPRESSION_HINT, GL_NICEST)
		
	def paintGL(self):
		if not self.parentWidget() : return
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		
		if ( self.image_rotary == None ): return
		self.image_rotary.render()

	
	def resizeGL(self, width, height):
		if width <= 0 or height <= 0: return None
		GL.glViewport(0,0,width,height)
	
		GL.glMatrixMode(GL.GL_PROJECTION)
		GL.glLoadIdentity()
		self.aspect = float(width)/float(height)
		GLU.gluPerspective(self.fov,self.aspect,self.zNear,self.zFar)
		#GL.glOrtho(0.0,width,0.0,height,-width,width)
		GL.glMatrixMode(GL.GL_MODELVIEW)
		GL.glLoadIdentity()
		
	def get_depth_for_height(self, height):
		# This function returns the width and height of the renderable 
		# area at the origin of the data volume
		depth = height/(2.0*tan(self.fov/2.0*pi/180.0))
	
		return depth
	def set_mmode(self,mode):
		print "in normal set"
		self.mmode = mode
		self.image_rotary.set_mmode(mode)
	
	def mousePressEvent(self, event):
		self.image_rotary.mousePressEvent(event)
			
	def wheelEvent(self,event):
		self.image_rotary.wheelEvent(event)
	
	def mouseMoveEvent(self,event):
		self.image_rotary.mouseMoveEvent(event)

	def mouseReleaseEvent(self,event):
		self.image_rotary.mouseReleaseEvent(event)
	
	def keyPressEvent(self,event):
		if self.mmode == "app":
			self.emit(QtCore.SIGNAL("keypress"),event)

	def dropEvent(self,event):
		self.image_rotary.dropEvent(event)
		
	def closeEvent(self,event) :
		self.image_rotary.closeEvent(event)
		
	def dragEnterEvent(self,event):
		self.image_rotary.dragEnterEvent(event)

	def dropEvent(self,event):
		self.image_rotary.dropEvent(event)
		
	def isVisible(self,n):
		return self.image_rotary.isVisible(n)
	
	def setSelected(self,n):
		return self.image_rotary.setSelected(n)
	
	def scrollTo(self,n,yonly):
		return self.image_rotary.scrollTo(n,yonly)
	
	def set_shapes(self,shapes,shrink):
		self.image_rotary.set_shapes(shapes,shrink)
		
class EMImageMXRotaryCore:

	allim=WeakKeyDictionary()
	def __init__(self, data=None,parent=None):
		self.parent = parent
		self.data=None
		self.datasize=(1,1)
		self.scale=1.0
		self.minden=0
		self.maxden=1.0
		self.invert=0
		self.fft=None
		self.mindeng=0
		self.maxdeng=1.0
		self.gamma=1.0
		self.origin=(0,0)
		self.nperrow=8
		self.nshow=-1
		self.mousedrag=None
		self.nimg=0
		self.changec={}
		self.mmode="drag"
		self.selected=[]
		self.targetorigin=None
		self.targetspeed=20.0
		self.mag = 1.1				# magnification factor
		self.invmag = 1.0/self.mag	# inverse magnification factor
		self.glflags = EMOpenGLFlagsAndTools() 	# supplies power of two texturing flags
		self.tex_names = [] 		# tex_names stores texture handles which are no longer used, and must be deleted
		self.supressInspector = False 	# Suppresses showing the inspector - switched on in emfloatingwidgets
		
		self.coords={}
		self.nshown=0
		self.valstodisp=["Img #"]
		try: self.parent.setAcceptDrops(True)
		except:	pass

		self.timer = QTimer()
		QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.timeout)

		self.initsizeflag = True
		self.inspector=None
		if data:
			self.setData(data)
		
		self.rotary = EMGLRotaryWidget(self,-25,10,40,EMGLRotaryWidget.LEFT_ROTARY)
		self.widget = EM3DWidget(self,self.rotary)
		self.widget.set_draw_frame(False)
	
	def emit(self,signal,event,integer=None):
		if integer != None:
			self.parent.emit(signal,event,integer)
		else:
			self.parent.emit(signal,event)	
	def set_mmode(self,mode):
		self.mmode = mode
		self.rotary.set_mmode(mode)

	def set_shapes(self,shapes,shrink):
		self.rotary.set_shapes(shapes,shrink)

	def register_animatable(self,animatable):
		self.parent.register_animatable(animatable)
		
	def width(self):
		return self.parent.width()
	
	def height(self):
		return self.parent.height()

	def getImageFileName(self):
		''' warning - could return none in some circumstances'''
		try: return self.parent.getImageFileName()
		except: return None
	
	def __del__(self):
		if ( len(self.tex_names) > 0 ):	glDeleteTextures(self.tex_names)
		
	def setData(self,data):
		if data == None or not isinstance(data,list) or len(data)==0:
			self.data = [] 
			return
		
		if (self.initsizeflag):
			self.initsizeflag = False
			if len(data)<self.nperrow :
				w=len(data)*(data[0].get_xsize()+2)
				hfac = 1
			else : 
				w=self.nperrow*(data[0].get_xsize()+2)
				hfac = len(data)/self.nperrow+1
			hfac *= data[0].get_ysize()
			if hfac > 512:
				hfac = 512
			try:
				self.parent.resize(int(w),int(hfac))
			except:
				pass
			#self.parent.resizeGL(w,hfac)
		
		

		self.data=data
		if data==None or len(data)==0:
			self.updateGL()
			return
		
		self.nimg=len(data)
		
		self.minden=data[0].get_attr("mean")
		self.maxden=self.minden
		self.mindeng=self.minden
		self.maxdeng=self.minden
		
		for i in data:
			if i.get_zsize()!=1 :
				self.data=None
				self.updateGL()
				return
			mean=i.get_attr("mean")
			sigma=i.get_attr("sigma")
			m0=i.get_attr("minimum")
			m1=i.get_attr("maximum")
		
			self.minden=min(self.minden,max(m0,mean-3.0*sigma))
			self.maxden=max(self.maxden,min(m1,mean+3.0*sigma))
			self.mindeng=min(self.mindeng,max(m0,mean-5.0*sigma))
			self.maxdeng=max(self.maxdeng,min(m1,mean+5.0*sigma))
		
		
		self.rotary.clear_widgets()
		for d in self.data:
			w = EMGLView2D(self,d)
			self.rotary.add_widget(w)
		#self.showInspector()		# shows the correct inspector if already open
		#self.timer.start(25)
		
		# experimental for lst file writing
		for i,d in enumerate(data):
			d.set_attr("original_number",i)

	def updateGL(self):
		try: self.parent.updateGL()
		except: pass
		
	def setDenRange(self,x0,x1):
		"""Set the range of densities to be mapped to the 0-255 pixel value range"""
		self.minden=x0
		self.maxden=x1
		self.updateGL()
	
	def setOrigin(self,x,y):
		"""Set the display origin within the image"""
		self.origin=(x,y)
		self.targetorigin=None
		self.updateGL()
		
	def setScale(self,newscale):
		"""Adjusts the scale of the display. Tries to maintain the center of the image at the center"""
		
		if self.targetorigin : 
			self.origin=self.targetorigin
			self.targetorigin=None
			
		if self.data and len(self.data)>0 and (self.data[0].get_ysize()*newscale>self.parent.height() or self.data[0].get_xsize()*newscale>self.parent.width()):
			newscale=min(float(self.parent.height())/self.data[0].get_ysize(),float(self.parent.width())/self.data[0].get_xsize())
			if self.inspector: self.inspector.scale.setValue(newscale)
			
			
#		yo=self.height()-self.origin[1]-1
		yo=self.origin[1]
#		self.origin=(newscale/self.scale*(self.width()/2+self.origin[0])-self.width()/2,newscale/self.scale*(self.height()/2+yo)-self.height()/2)
#		self.origin=(newscale/self.scale*(self.width()/2+self.origin[0])-self.width()/2,newscale/self.scale*(yo-self.height()/2)+self.height()/2)
		self.origin=(newscale/self.scale*(self.parent.width()/2+self.origin[0])-self.parent.width()/2,newscale/self.scale*(self.parent.height()/2+self.origin[1])-self.parent.height()/2)
#		print self.origin,newscale/self.scale,yo,self.height()/2+yo
		
		self.scale=newscale
		self.updateGL()
		
	def setDenMin(self,val):
		self.minden=val
		self.updateGL()
		
	def setDenMax(self,val):
		self.maxden=val
		self.updateGL()

	def setGamma(self,val):
		self.gamma=val
		self.updateGL()
	
	def setNPerRow(self,val):
		if self.nperrow==val: return
		if val<1 : val=1
		
		self.nperrow=val
		self.updateGL()
		try:
			if self.inspector.nrow.value!=val :
				self.inspector.nrow.setValue(val)
		except: pass
		
	def setNShow(self,val):
		self.nshow=val
		self.updateGL()

	def setInvert(self,val):
		if val: self.invert=1
		else : self.invert=0
		self.updateGL()
	

	def timeout(self):
		"""Called a few times each second when idle for things like automatic scrolling"""
		if self.targetorigin :
			vec=(self.targetorigin[0]-self.origin[0],self.targetorigin[1]-self.origin[1])
			h=hypot(vec[0],vec[1])
			if h<=self.targetspeed :
				self.origin=self.targetorigin
				self.targetorigin=None
			else :
				vec=(vec[0]/h,vec[1]/h)
				self.origin=(self.origin[0]+vec[0]*self.targetspeed,self.origin[1]+vec[1]*self.targetspeed)
			#self.updateGL()
	
	def getMaxMatrixRanges(self):
		return getMatrixRanges(0,0)
	
	def getMatrixRanges(self,x,y):
		n=len(self.data)
		w=int(min(self.data[0].get_xsize()*self.scale,self.parent.width()))
		h=int(min(self.data[0].get_ysize()*self.scale,self.parent.height()))
		
		yoff = 0
		if y < 0:
			ybelow = floor(-y/(h+2))
			yoff = ybelow*(h+2)+y
			visiblerows = int(ceil(float(self.parent.height()-yoff)/(h+2)))
		else: visiblerows = int(ceil(float(self.parent.height()-y)/(h+2)))
				
		maxrow = int(ceil(float(n)/self.nperrow))
		ystart =-y/(h+2)
		if ystart < 0: ystart = 0
		elif ystart > 0:
			ystart = int(ystart)
			visiblerows = visiblerows + ystart
		if visiblerows > maxrow: visiblerows = maxrow

		xoff = 0
		if x < 0:
			xbelow = floor(-x/(w+2))
			xoff = xbelow*(w+2)+x
			visiblecols =  int(ceil(float(self.parent.width()-xoff)/(w+2)))
		else: visiblecols =  int(ceil(float(self.parent.width()-x)/(w+2)))

		xstart =-x/(w+2)
		if xstart < 0:
			xstart = 0
		else:
			xstart = int(xstart)
			visiblecols = visiblecols + xstart
		if visiblecols > self.nperrow:
			visiblecols = self.nperrow
	
		return [int(xstart),int(visiblecols),int(ystart),int(visiblerows)]
	
	def render(self):

		glLoadIdentity()
		
		if not self.data : return
		for i in self.data:
			self.changec[i]=i.get_attr("changecount")
		
		if not self.invert : pixden=(0,255)
		else: pixden=(255,0)
		lr = self.rotary.get_suggested_lr_bt_nf()
		#print lr
		GL.glEnable(GL.GL_DEPTH_TEST)
		GL.glEnable(GL.GL_LIGHTING)
		#print self.parent.get_depth_for_height(self.height())
		#lr = self.rotary.get_lr_bt_nf()
		
		GL.glPushMatrix()
		glTranslate(-(lr[1]+lr[0])/2.0,-(lr[3]+lr[2])/2.0,-self.parent.get_depth_for_height(abs(lr[3]-lr[2])))
		self.widget.paintGL()
		GL.glPopMatrix()
		return
		
		n=len(self.data)
		hist=numpy.zeros(256)
		#if len(self.coords)>n : self.coords=self.coords[:n] # dont know what this does? Had to comment out, changing from a list to a dictionary
		glColor(0.5,1.0,0.5)
		glLineWidth(2)
		try:
			# we render the 16x16 corner of the image and decide if it's light or dark to decide the best way to 
			# contrast the text labels...
			a=self.data[0].render_amp8(0,0,16,16,16,self.scale,pixden[0],pixden[1],self.minden,self.maxden,self.gamma,4)
			ims=[ord(pv) for pv in a]
			if sum(ims)>32768 : txtcol=(0.0,0.0,0.2)
			else : txtcol=(.8,.8,1.0)
		except: txtcol=(1.0,1.0,1.0)

		if ( len(self.tex_names) > 0 ):	glDeleteTextures(self.tex_names)
		self.tex_names = []

		self.nshown=0
		
		x,y=-self.origin[0],-self.origin[1]
		w=int(min(self.data[0].get_xsize()*self.scale,self.parent.width()))
		h=int(min(self.data[0].get_ysize()*self.scale,self.parent.height()))
		
		[xstart,visiblecols,ystart,visiblerows] = self.getMatrixRanges(x,y)
			
		#print "rows",visiblerows-ystart,"cols",visiblecols-xstart
		#print "yoffset",yoff,"xoffset",xoff
		#print (visiblerows-ystart)*(h+2)+yoff,self.parent.height(),"height",(visiblecols-xstart)*(w+2)+xoff,self.parent.width()		
		invscale=1.0/self.scale
		self.coords = {}
		for row in range(ystart,visiblerows):
			for col in range(xstart,visiblecols):
				i = (row)*self.nperrow+col
				#print i,n
				if i >= n : break
				tx = int((w+2)*(col) + x)
				ty = int((h+2)*(row) + y)
				tw = w
				th = h
				rx = 0	#render x
				ry = 0	#render y
				#print "Prior",i,':',row,col,tx,ty,tw,th,y,x
				drawlabel = True
				if (tx+tw) > self.parent.width():
					tw = int(self.parent.width()-tx)
				elif tx<0:
					drawlabel=False
					rx = int(ceil(-tx*invscale))
					tw=int(w+2+tx)
					tx = 0
					

				#print h,row,y
				#print "Prior",i,':',row,col,tx,ty,tw,th,'offsets',yoffset,xoffset
				if (ty+th) > self.parent.height():
					#print "ty + th was greater than",self.parent.height()
					th = int(self.parent.height()-ty)
				elif ty<0:
					drawlabel = False
					ry = int(ceil(-ty*invscale))
					th=int(h+2+ty)
					ty = 0
					
				#print i,':',row,col,tx,ty,tw,th,'offsets',yoffset,xoffset
				if th < 0 or tw < 0:
					#weird += 1
					print "weirdness"
					print col,row,
					continue
				#i = (row+yoffset)*self.nperrow+col+xoffset
				#print i,':',row,col,tx,ty,tw,th
				shown = True
				#print rx,ry,tw,th,self.parent.width(),self.parent.height()
				if not self.glflags.npt_textures_unsupported():
					a=self.data[i].render_amp8(rx,ry,tw,th,(tw-1)/4*4+4,self.scale,pixden[0],pixden[1],self.minden,self.maxden,self.gamma,2)
					self.texture(a,tx,ty,tw,th)
				else:
					a=self.data[i].render_amp8(rx,ry,tw,th,(tw-1)/4*4+4,self.scale,pixden[0],pixden[1],self.minden,self.maxden,self.gamma,6)
					glRasterPos(tx,ty)
					glDrawPixels(tw,th,GL_LUMINANCE,GL_UNSIGNED_BYTE,a)
						
				
				hist2=numpy.fromstring(a[-1024:],'i')
				hist+=hist2
				# render labels

				if drawlabel:
					tagy = ty
					glColor(*txtcol)
					for v in self.valstodisp:
						if v=="Img #" : self.renderText(tx,tagy,"%d"%i)
						else : 
							av=self.data[i].get_attr(v)
							if isinstance(av,float) : avs="%1.4g"%av
							else: avs=str(av)
							try: self.renderText(tx,tagy,str(avs))
							except: self.renderText(tx,tagy,"------")
						tagy+=16
				
				self.coords[i]=(tx,ty,tw,th)
				
				#try: self.coords[i]=(tx,ty,self.data[i].get_xsize()*self.scale,self.data[i].get_ysize()*self.scale,shown)
				#except: self.coords.append((tx,ty,self.data[i].get_xsize()*self.scale,self.data[i].get_ysize()*self.scale,shown))
				if shown : self.nshown+=1
		
		for i in self.selected:
			try:
				data = self.coords[i]	
				glColor(0.5,0.5,1.0)
				glBegin(GL_LINE_LOOP)
				glVertex(data[0],data[1])
				glVertex(data[0]+data[2],data[1])
				glVertex(data[0]+data[2],data[1]+data[3])
				glVertex(data[0],data[1]+data[3])
				glEnd()
			except:
				# this means the box isn't visible!
				pass
		# If the user is lost, help him find himself again...
		if self.nshown==0 : 
			try: self.targetorigin=(0,self.coords[self.selected[0]][1]-self.parent.height()/2+self.data[0].get_ysize()*self.scale/2)
			except: self.targetorigin=(0,0)
			self.targetspeed=100.0
		
		if self.inspector : self.inspector.setHist(hist,self.minden,self.maxden)
		
	def texture(self,a,x,y,w,h):
		
		tex_name = glGenTextures(1)
		if ( tex_name <= 0 ):
			raise("failed to generate texture name")
		
		width = w/2.0
		height = h/2.0
		
		glPushMatrix()
		glTranslatef(x+width,y+height,0)
			
		glBindTexture(GL_TEXTURE_2D,tex_name)
		glTexImage2D(GL_TEXTURE_2D,0,GL_LUMINANCE,w,h,0,GL_LUMINANCE,GL_UNSIGNED_BYTE, a)
		
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, tex_name)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
		# using GL_NEAREST ensures pixel granularity
		# using GL_LINEAR blurs textures and makes them more difficult
		# to interpret (in cryo-em)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		# this makes it so that the texture is impervious to lighting
		glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
		
		
		# POSITIONING POLICY - the texture occupies the entire screen area
		glBegin(GL_QUADS)
		
		glTexCoord2f(0,0)
		glVertex2f(-width,height)
		
		glTexCoord2f(1,0)
		glVertex2f(width,height)
			
		glTexCoord2f(1,1)
		glVertex2f(width,-height)
		
		glTexCoord2f(0,1)
		glVertex2f(-width,-height)
			
		glEnd()
		
		glDisable(GL_TEXTURE_2D)
		
		glPopMatrix()
		self.tex_names.append(tex_name)
	
	def renderText(self,x,y,s):
#	        print 'in render Text'
		glRasterPos(x+2,y+2)
		for c in s:
			GLUT.glutBitmapCharacter(GLUT.GLUT_BITMAP_9_BY_15,ord(c))

	def resizeEvent(self, width, height):
		
		#print width/(self.data[0].get_xsize()*self.scale)
		if self.data and len(self.data)>0 : self.setNPerRow(int(width/(self.data[0].get_xsize()*self.scale)))
		#except: pass
		
		if self.data and len(self.data)>0 and (self.data[0].get_ysize()*self.scale>self.parent.height() or self.data[0].get_xsize()*self.scale>self.parent.width()):
			self.scale=min(float(self.parent.height())/self.data[0].get_ysize(),float(self.parent.width())/self.data[0].get_xsize())
	
	def isVisible(self,n):
		try: return self.coords[n][4]
		except: return False
	
	def scrollTo(self,n,yonly=0):
		"""Moves image 'n' to the center of the display"""
#		print self.origin,self.coords[0],self.coords[1]
#		try: self.origin=(self.coords[n][0]-self.width()/2,self.coords[n][1]+self.height()/2)
#		try: self.origin=(self.coords[8][0]-self.width()/2-self.origin[0],self.coords[8][1]+self.height()/2-self.origin[1])
		if yonly :
			try: 
				self.targetorigin=(0,self.coords[n][1]-self.parent.height()/2+self.data[0].get_ysize()*self.scale/2)
			except: return
		else:
			try: self.targetorigin=(self.coords[n][0]-self.parent.width()/2+self.data[0].get_xsize()*self.scale/2,self.coords[n][1]-self.parent.height()/2+self.data[0].get_ysize()*self.scale/2)
			except: return
		self.targetspeed=hypot(self.targetorigin[0]-self.origin[0],self.targetorigin[1]-self.origin[1])/20.0
#		print n,self.origin
#		self.updateGL()
	
	def setSelected(self,numlist):
		"""pass an integer or a list/tuple of integers which should be marked as 'selected' in the
		display"""
		if isinstance(numlist,int) : numlist=[numlist]
		if isinstance(numlist,list) or isinstance(numlist,tuple) : self.selected=numlist
		else : self.selected=[]
		self.updateGL()
	
	def setValDisp(self,v2d):
		"""Pass in a list of strings describing image attributes to overlay on the image, in order of display"""
		v2d.reverse()
		self.valstodisp=v2d
		self.updateGL()
	
	def showInspector(self,force=0):
		if (self.supressInspector): return
		if not force and self.inspector==None : return
		self.initInspector()
		self.inspector.show()

	def initInspector(self):
		if not self.inspector : self.inspector=EMImageMxInspector2D(self)
		self.inspector.setLimits(self.mindeng,self.maxdeng,self.minden,self.maxden)

	def scrtoimg(self,vec):
		"""Converts screen location (ie - mouse event) to pixel coordinates within a single
		image from the matrix. Returns (image number,x,y) or None if the location is not within any
		of the contained images. """
		absloc=((vec[0]),(self.parent.height()-(vec[1])))
		for item in self.coords.items():
			index = item[0]
			data = item[1]
			if absloc[0]>data[0] and absloc[1]>data[1] and absloc[0]<data[0]+data[2] and absloc[1]<data[1]+data[3] :
				return (index,(absloc[0]-data[0])/self.scale,(absloc[1]-data[1])/self.scale)
		return None
	
	def closeEvent(self,event) :
		if self.inspector: self.inspector.close()
		
	def dragEnterEvent(self,event):
#		f=event.mimeData().formats()
#		for i in f:
#			print str(i)
		
		if event.source()==self:
			event.setDropAction(Qt.MoveAction)
			event.accept()
		elif event.provides("application/x-eman"):
			event.setDropAction(Qt.CopyAction)
			event.accept()

	
	def dropEvent(self,event):
		lc=self.scrtoimg((event.pos().x(),event.pos().y()))
		if event.source()==self:
#			print lc
			n=int(event.mimeData().text())
			if not lc : lc=[len(self.data)]
			if n>lc[0] : 
				self.data.insert(lc[0],self.data[n])
				del self.data[n+1]
			else : 
				self.data.insert(lc[0]+1,self.data[n])
				del self.data[n]
			event.setDropAction(Qt.MoveAction)
			event.accept()
		elif EMAN2.GUIbeingdragged:
			self.data.append(EMAN2.GUIbeingdragged)
			self.setData(self.data)
			EMAN2.GUIbeingdragged=None
		elif event.provides("application/x-eman"):
			x=loads(event.mimeData().data("application/x-eman"))
			if not lc : self.data.append(x)
			else : self.data.insert(lc[0],x)
			self.setData(self.data)
			event.acceptProposedAction()


	def mousePressEvent(self, event):
		self.widget.mousePressEvent(event)
		self.updateGL()
	
	def mouseMoveEvent(self, event):
		self.widget.mouseMoveEvent(event)
		self.updateGL()
		
	def mouseReleaseEvent(self, event):
		self.widget.mouseReleaseEvent(event)
		self.updateGL()
		
	def wheelEvent(self, event):
#		if event.delta() > 0:
#			self.setScale( self.scale * self.mag )
#		elif event.delta() < 0:
#			self.setScale(self.scale * self.invmag )
#		self.resizeEvent(self.parent.width(),self.parent.height())
#		# The self.scale variable is updated now, so just update with that
#		if self.inspector: self.inspector.setScale(self.scale)
		self.widget.wheelEvent(event)
		self.updateGL()
	def leaveEvent(self):
		pass

class EMImageMxInspector2D(QtGui.QWidget):
	def __init__(self,target) :
		QtGui.QWidget.__init__(self,None)
		self.target=target
		
		self.vals = QtGui.QMenu()
		self.valsbut = QtGui.QPushButton("Values")
		self.valsbut.setMenu(self.vals)
		
		try:
			self.vals.clear()
			vn=self.target.data[0].get_attr_dict().keys()
			vn.sort()
			for i in vn:
				action=self.vals.addAction(i)
				action.setCheckable(1)
				action.setChecked(0)
		except Exception, inst:
			print type(inst)     # the exception instance
			print inst.args      # arguments stored in .args
			print int
		
		action=self.vals.addAction("Img #")
		action.setCheckable(1)
		action.setChecked(1)
		
		self.vbl = QtGui.QVBoxLayout(self)
		self.vbl.setMargin(2)
		self.vbl.setSpacing(6)
		self.vbl.setObjectName("vboxlayout")
		
		self.hbl3 = QtGui.QHBoxLayout()
		self.hbl3.setMargin(0)
		self.hbl3.setSpacing(6)
		self.hbl3.setObjectName("hboxlayout")
		self.vbl.addLayout(self.hbl3)
		
		self.hist = ImgHistogram(self)
		self.hist.setObjectName("hist")
		self.hbl3.addWidget(self.hist)

		self.vbl2 = QtGui.QVBoxLayout()
		self.vbl2.setMargin(0)
		self.vbl2.setSpacing(6)
		self.vbl2.setObjectName("vboxlayout")
		self.hbl3.addLayout(self.vbl2)

		self.bsavedata = QtGui.QPushButton("Save")
		self.vbl2.addWidget(self.bsavedata)
		
		self.bsavelst = QtGui.QPushButton("Save Lst")
		self.vbl2.addWidget(self.bsavelst)


		self.bsnapshot = QtGui.QPushButton("Snap")
		self.vbl2.addWidget(self.bsnapshot)

		# This shows the mouse mode buttons
		self.hbl2 = QtGui.QHBoxLayout()
		self.hbl2.setMargin(0)
		self.hbl2.setSpacing(6)
		self.hbl2.setObjectName("hboxlayout")
		self.vbl.addLayout(self.hbl2)
		
		#self.mmeas = QtGui.QPushButton("Meas")
		#self.mmeas.setCheckable(1)
		#self.hbl2.addWidget(self.mmeas)

		self.mapp = QtGui.QPushButton("App")
		self.mapp.setCheckable(1)
		self.hbl2.addWidget(self.mapp)
		
		self.mdel = QtGui.QPushButton("Del")
		self.mdel.setCheckable(1)
		self.hbl2.addWidget(self.mdel)

		self.mdrag = QtGui.QPushButton("Drag")
		self.mdrag.setCheckable(1)
		self.mdrag.setDefault(1)
		self.hbl2.addWidget(self.mdrag)

		self.bg=QtGui.QButtonGroup()
		self.bg.setExclusive(1)
#		self.bg.addButton(self.mmeas)
		self.bg.addButton(self.mapp)
		self.bg.addButton(self.mdel)
		self.bg.addButton(self.mdrag)

		self.hbl = QtGui.QHBoxLayout()
		self.hbl.setMargin(0)
		self.hbl.setSpacing(6)
		self.hbl.setObjectName("hboxlayout")
		self.vbl.addLayout(self.hbl)
		
		self.hbl.addWidget(self.valsbut)
		
		self.lbl = QtGui.QLabel("#/row:")
		self.lbl.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
		self.hbl.addWidget(self.lbl)
		
		self.nrow = QtGui.QSpinBox(self)
		self.nrow.setObjectName("nrow")
		self.nrow.setRange(1,50)
		self.nrow.setValue(self.target.nperrow)
		self.hbl.addWidget(self.nrow)
		
		self.scale = ValSlider(self,(0.1,5.0),"Mag:")
		self.scale.setObjectName("scale")
		self.scale.setValue(1.0)
		self.vbl.addWidget(self.scale)
		
		self.mins = ValSlider(self,label="Min:")
		self.mins.setObjectName("mins")
		self.vbl.addWidget(self.mins)
		
		self.maxs = ValSlider(self,label="Max:")
		self.maxs.setObjectName("maxs")
		self.vbl.addWidget(self.maxs)
		
		self.brts = ValSlider(self,(-1.0,1.0),"Brt:")
		self.brts.setObjectName("brts")
		self.vbl.addWidget(self.brts)
		
		self.conts = ValSlider(self,(0.0,1.0),"Cont:")
		self.conts.setObjectName("conts")
		self.vbl.addWidget(self.conts)
		
		self.gammas = ValSlider(self,(.5,2.0),"Gam:")
		self.gammas.setObjectName("gamma")
		self.gammas.setValue(1.0)
		self.vbl.addWidget(self.gammas)

		self.lowlim=0
		self.highlim=1.0
		self.busy=0
		
		QtCore.QObject.connect(self.vals, QtCore.SIGNAL("triggered(QAction*)"), self.newValDisp)
		QtCore.QObject.connect(self.nrow, QtCore.SIGNAL("valueChanged(int)"), target.setNPerRow)
		QtCore.QObject.connect(self.scale, QtCore.SIGNAL("valueChanged"), target.setScale)
		QtCore.QObject.connect(self.mins, QtCore.SIGNAL("valueChanged"), self.newMin)
		QtCore.QObject.connect(self.maxs, QtCore.SIGNAL("valueChanged"), self.newMax)
		QtCore.QObject.connect(self.brts, QtCore.SIGNAL("valueChanged"), self.newBrt)
		QtCore.QObject.connect(self.conts, QtCore.SIGNAL("valueChanged"), self.newCont)
		QtCore.QObject.connect(self.gammas, QtCore.SIGNAL("valueChanged"), self.newGamma)
		
		#QtCore.QObject.connect(self.mmeas, QtCore.SIGNAL("clicked(bool)"), self.setMeasMode)
		QtCore.QObject.connect(self.mapp, QtCore.SIGNAL("clicked(bool)"), self.setAppMode)
		QtCore.QObject.connect(self.mdel, QtCore.SIGNAL("clicked(bool)"), self.setDelMode)
		QtCore.QObject.connect(self.mdrag, QtCore.SIGNAL("clicked(bool)"), self.setDragMode)

		QtCore.QObject.connect(self.bsavedata, QtCore.SIGNAL("clicked(bool)"), self.saveData)
		QtCore.QObject.connect(self.bsavelst, QtCore.SIGNAL("clicked(bool)"), self.saveLst)
		QtCore.QObject.connect(self.bsnapshot, QtCore.SIGNAL("clicked(bool)"), self.snapShot)
	
	def setScale(self,val):
		if self.busy : return
		self.busy=1
		self.scale.setValue(val)
		self.busy=0
	
	def saveData(self):
		if self.target.data==None or len(self.target.data)==0: return

		# Get the output filespec
		fsp=QtGui.QFileDialog.getSaveFileName(self, "Select File","","","",QtGui.QFileDialog.DontConfirmOverwrite)
		fsp=str(fsp)
		
	def saveLst(self):
		if self.target.data==None or len(self.target.data)==0: return
		
		origname = self.target.getImageFileName()
		if origname == None:
			print "error, origname is none. Either the data is not already on disk or there is a bug"
			return

		# Get the output filespec
		fsp=QtGui.QFileDialog.getSaveFileName(self, "Specify lst file to save","","","")
		fsp=str(fsp)
		
		if fsp != '':
			f = file(fsp,'w')
			f.write('#LST\n')
			
			for d in self.target.data:
				#try:
					f.write(str(d.get_attr('original_number')) +'\t'+origname+'\n')
				#except:
					#pass
						
			f.close()
			
	def snapShot(self):
		"Save a screenshot of the current image display"
		
		try:
			qim=self.target.grabFrameBuffer()
		except:
			QtGui.QMessageBox.warning ( self, "Framebuffer ?", "Could not read framebuffer")
		
		# Get the output filespec
		fsp=QtGui.QFileDialog.getSaveFileName(self, "Select File")
		fsp=str(fsp)
		
		qim.save(fsp,None,90)
		
	def newValDisp(self):
		v2d=[str(i.text()) for i in self.vals.actions() if i.isChecked()]
		self.target.setValDisp(v2d)

	def setAppMode(self,i):
		self.target.mmode="app"
	
	def setMeasMode(self,i):
		self.target.mmode="meas"
	
	def setDelMode(self,i):
		self.target.mmode="del"
	
	def setDragMode(self,i):
		self.target.mmode="drag"

	def newMin(self,val):
		if self.busy : return
		self.busy=1
		self.target.setDenMin(val)

		self.updBC()
		self.busy=0
		
	def newMax(self,val):
		if self.busy : return
		self.busy=1
		self.target.setDenMax(val)
		self.updBC()
		self.busy=0
	
	def newBrt(self,val):
		if self.busy : return
		self.busy=1
		self.updMM()
		self.busy=0
		
	def newCont(self,val):
		if self.busy : return
		self.busy=1
		self.updMM()
		self.busy=0
	
	def newGamma(self,val):
		if self.busy : return
		self.busy=1
		self.target.setGamma(val)
		self.busy=0

	def updBC(self):
		b=0.5*(self.mins.value+self.maxs.value-(self.lowlim+self.highlim))/((self.highlim-self.lowlim))
		c=(self.mins.value-self.maxs.value)/(2.0*(self.lowlim-self.highlim))
		self.brts.setValue(-b)
		self.conts.setValue(1.0-c)
		
	def updMM(self):
		x0=((self.lowlim+self.highlim)/2.0-(self.highlim-self.lowlim)*(1.0-self.conts.value)-self.brts.value*(self.highlim-self.lowlim))
		x1=((self.lowlim+self.highlim)/2.0+(self.highlim-self.lowlim)*(1.0-self.conts.value)-self.brts.value*(self.highlim-self.lowlim))
		self.mins.setValue(x0)
		self.maxs.setValue(x1)
		self.target.setDenRange(x0,x1)
		
	def setHist(self,hist,minden,maxden):
		self.hist.setData(hist,minden,maxden)

	def setLimits(self,lowlim,highlim,curmin,curmax):
		self.lowlim=lowlim
		self.highlim=highlim
		self.mins.setRange(lowlim,highlim)
		self.maxs.setRange(lowlim,highlim)
		self.mins.setValue(curmin)
		self.maxs.setValue(curmax)

# This is just for testing, of course
if __name__ == '__main__':
	app = QtGui.QApplication(sys.argv)
	GLUT.glutInit("")
	print "a"
	window = EMImageMXRotary()
	if len(sys.argv)==1 : window.setData([test_image(),test_image(1),test_image(2),test_image(3)]*4)
	else :
		a=EMData.read_images(sys.argv[1])
		window.setImageFileName(sys.argv[1])
		window.setData(a)
	window2=EMParentWin(window)
	window2.show()
	window2.resize(*window.get_optimal_size())
#	w2=QtGui.QWidget()
#	w2.resize(256,128)
	
#	w3=ValSlider(w2)
#	w3.resize(256,24)
#	w2.show()
	
	sys.exit(app.exec_())
