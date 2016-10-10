from IPython import embed as shell
"""
RonTree.py

Created by Ronald Dekker on 2016-10-05.
Copyright (c) 2016 RD. All rights reserved.
"""

import os #, sys, datetime
# import subprocess, logging
# import pickle, datetime, time

import turtle
from PIL import Image, ImageEnhance, EpsImagePlugin

# import scipy as sp
import numpy as np
# import matplotlib.pylab as pl
from math import *

class RonTree(object):
	"""
	RonTree object, for creating naturalistic tree stimuli.
	"""
	def __init__(self, canvas_width = 510, canvas_height = 510, branch_chance = 0.5, stem_chance = 0.6, branch_angle = 20, branch_noise = 25, stem_angle = 0, stem_noise = 30, min_iters = 8, leaf_texture = os.path.join("Resources","Leaves","leaf4.png"), leaf_height = 16, leaf_brightness_chance = 0.7, leaves_per_branch = 10, leaf_chance = 0.03, trunk_size = 4, len_over_width = 8., base_len = 70., len_decay = 6, len_decay_noise = 3, min_len = 0.1):
	
		# set up canvas
		self.scale = (1/.722) # tscale / pscale
		self.canvas_width = canvas_width 
		self.canvas_height = canvas_height 
		self.canvas_width_t = canvas_width * self.scale # resized to default postscript DPI in pillow
		self.canvas_height_t = canvas_height * self.scale

		# odds and angles
		self.branch_chance = branch_chance 
		self.stem_chance = stem_chance
		self.branch_angle = branch_angle
		self.branch_noise = branch_noise
		self.stem_angle = stem_angle
		self.stem_noise = stem_noise
		self.min_iters = min_iters

		# leaves
		self.leaf_texture = leaf_texture
		self.leaf_height = leaf_height
		self.leaf_brightness_chance = leaf_brightness_chance # higher values correspond with more 'normal' leaves
		self.leaves_per_branch = leaves_per_branch # average potential leaf locations per branch
		self.leaf_chance = leaf_chance
		self.trunk_size = trunk_size # the trunk size is the nr of iters that can't have leaves

		# lengths
		self.len_over_width = len_over_width
		self.base_len = base_len
		self.len_decay = len_decay
		self.len_decay_noise = len_decay_noise
		self.min_len = min_len

		# set up filler variables
		self.leaf_indexes = []
		self.leaf_indexes_temp = []
	
	def tree(self, length, t, current_iters = 0):
		
		if length<self.min_len: # recursivity limiter
			return

		#t.width = length/self.len_over_width # set width to be proportional to len
		t.width(max(0,1*(5-1*current_iters))+(length/self.len_over_width)) # width is proportional to len, with the stem being slightly thicker

		if current_iters < self.trunk_size:
			t.forward(length)
		else:
			distance = 0
			while distance < length-.5*(length/self.leaves_per_branch): # half of the leaf interval is subtracted so branches are on average normal length
				step = np.random.uniform(0, 2*(length/self.leaves_per_branch))
				t.forward(step)
				distance += step
				if np.random.uniform()<self.leaf_chance:
					self.leaf_indexes_temp.append([t.xcor()*self.scale**-1,t.ycor()*self.scale**-1]) # keep in mind this is logged with the (0,0) being the canvas center.. ((+1/2X,-1/2Y) to make these normal coordinates)

		#t.forward(length)

		start_heading = t.heading()
		#shell()
		if np.random.uniform() < self.branch_chance: # branch right
			t.setheading(start_heading-self.branch_angle+np.random.uniform(-self.branch_noise,self.branch_noise))
			self.tree(length-self.len_decay+np.random.uniform(-self.len_decay_noise,self.len_decay_noise),t,current_iters+1) # recursion!

		if np.random.uniform() < self.branch_chance: # branch left
			t.setheading(start_heading+self.branch_angle+np.random.uniform(-self.branch_noise,self.branch_noise))
			self.tree(length-self.len_decay+np.random.uniform(-self.len_decay_noise,self.len_decay_noise),t,current_iters+1)

		if current_iters < self.min_iters or np.random.uniform() < self.stem_chance: # branch geradeaus
			t.setheading(start_heading+np.random.uniform(-self.branch_noise,self.branch_noise))
			self.tree(length-self.len_decay+np.random.uniform(-self.len_decay_noise,self.len_decay_noise),t,current_iters+1)
		t.setheading(start_heading)
		if current_iters < self.trunk_size:
			t.backward(length)
		else:
			t.backward(distance)
	#def oneTree(width, current_iters)

	def leaves(self, iters = 1, filename = "default"):
		def bg_transparent(img): # this function makes the background transparent, so we can paste the tree over the tree, and not all leaves appear in front of the tree
			img = img.convert("RGBA")
			datas = img.getdata()

			newData = []
			for item in datas:
				if item[0] > 100 and item[1] > 100 and item[2] > 100: # i.e. pixel is 'white'
					newData.append((255,255,255,0))
				else:
					newData.append(item)

			img.putdata(newData)
			return img

		# Generate leaf textures		
		leaf_im = Image.open(self.leaf_texture).resize((int(1.2*self.leaf_height),self.leaf_height)) # 
		leaf_brighter = leaf_im
		brightness = ImageEnhance.Brightness(leaf_im)
		leaf_brighter = brightness.enhance(1.5)
		leaf_darker = brightness.enhance(0.7)

		for numtree in range(iters):
			# load in tree skeleton
			tree_im = Image.open(os.path.join("EPS","Example-"+str(numtree+1)+".eps"))
			transparent_tree = bg_transparent(tree_im)

			np.random.shuffle(self.leaf_indexes[numtree]) # so leaves that go behind the tree aren't clustered
			for i, tcoords in enumerate(self.leaf_indexes[numtree]):
				pcoords = (int(tcoords[0]+0.5*self.canvas_width - 0.5*1.2*self.leaf_height), int(.5*self.canvas_height-tcoords[1] - 0.5*self.leaf_height)) # convert turtle coordinates to pillow coordinates and center image on coordinate
				if i == round(.8*len(self.leaf_indexes[numtree])):
					tree_im.paste(transparent_tree, None, transparent_tree)

				if np.random.uniform() < self.leaf_brightness_chance: # the brightness of the leaf is chosen, based of brightness chance
					selected_leaf = leaf_im
				elif np.random.uniform() < self.leaf_brightness_chance:
					selected_leaf = leaf_brighter
				else:
					selected_leaf = leaf_darker
				selected_leaf = selected_leaf.rotate(np.random.uniform(0,180)) # optional leaf rotation
				tree_im.paste(selected_leaf, pcoords, selected_leaf)

			#tree_im.show() # to show output on screen
			tree_im.save(os.path.join("Output",str(filename)+str(numtree+1)+".png"), "PNG") # to save

def main(instance, iters = 1, branch_color = "#3f1d05"): 
	"""
	Create branch skeleton and export to EPS
	"""
	t = turtle.Turtle()
	canvas = turtle.Screen()
	canvas.setup(width=instance.canvas_width_t, height=instance.canvas_height_t)
	canvas.screensize(canvwidth=instance.canvas_width_t, canvheight=instance.canvas_height_t)
	t.ht()
	#t.speed(0) # fast drawing
	t.tracer(0, 0) # no drawing
	t.up(); t.left(90); t.sety((-2/5.)*canvas.screensize()[1]) # initialize canvas settings	
	t.pencolor(branch_color)
	t.down()

	for i in range(iters):
		instance.tree(instance.base_len, t)
		instance.leaf_indexes.append(instance.leaf_indexes_temp) # this step is so indexes from one tree are clustered in their own list
		instance.leaf_indexes_temp = [] # clear buffer
		ts=t.getscreen()
		ts.getcanvas().postscript(file = os.path.join("EPS","Example-"+str(i+1)+".eps"))
		t.clear()
	#ts.getcanvas().postscript(file="PS/Example.ps", colormode='color')

	#canvas.exitonclick() # to display branches only output
	canvas.bye() # to skip display of branches only output

if __name__ == '__main__':

	# For single tree
	# main(Adam)
	# Adam.leaves("Example")

	instance = RonTree()
	# For N trees
	n = 4 # number of trees
	for i in range(n):
		#shell()

		main(instance, iters = n)
		#print "hello world"
		instance.leaves(iters = n, filename = "Leafy+Brancy+_-")

		print "All jobs finished!"


		

