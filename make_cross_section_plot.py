import os, sys
import numpy as np
import math

def execute(command):
	print "Executing: " + command
	r = os.system(command);
	if r != 0:
		sys.exit("Command failed.")
	
def normalise(v):
	l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
	return v/l

def project(p, c, n):
	return p - np.dot((p - c), n) * n

def perp(v):
    if v[1] == 0 and v[2] == 0:
        if v[0] == 0:
            raise ValueError('zero vector')
        else:
            return np.cross(v, [0, 1, 0])
    return np.cross(v, [1, 0, 0])

if len(sys.argv) != 6:
	sys.exit("Usage: python make_cross_section_plot.py PLANE1XTR PLANE2XTR STEPLENGTH1 STEPLENGTH2 TIME")

plane1 = sys.argv[1]
plane2 = sys.argv[2]
steplength1 = str(float(sys.argv[3]))
steplength2 = str(float(sys.argv[4]))
time = str(float(sys.argv[5]))

hemeXtract = "~/hemeXtract/hemeXtract"

execute(hemeXtract + " -C " + plane1 + " " + plane2 + " -A " + steplength1 + " -B " + steplength2 + " -1 " + time + " -n 1 -o __hemeXtract_output\n")

# Read in the site coordinates and values from file
coords = []
data = []
with open("__hemeXtract_output", "r") as infile:
	for line in infile.readlines():
		if line.startswith("#"):
			continue
		x, y, z, val = [float(i) for i in line.split()]
		coords.append(np.array([x,y,z]))
		data.append(val)

# Calculate centroid of all site coordinates
cx = 0
cy = 0
cz = 0
for coord in coords:
	cx += coord[0]
	cy += coord[1]
	cz += coord[2]
n = len(coords)
cx/=n
cy/=n
cz/=n
centroid = np.array([cx, cy, cz])

# Subtract centroid from all site coordinates, centering the cloud on the origin
for i, coord in enumerate(coords):
	coords[i] = coord - centroid;
coords = np.array(coords)

# Do a singular value decomposition of the coordinate matrix
U, s, V = np.linalg.svd(coords, full_matrices=False)

# The normal of the plane is the right-most vector in the SVD
normal = V[-1]

# Get two perpendicular vectors in the plane of the points
a = perp(normal)
b = np.cross(normal, a)

# The centroid is now zero
centroid = np.array([0,0,0])

# Project the points onto the calculated plane
out = []
new = []
for p in coords:
	new.append(project(p, centroid, normal))
	out.append(p)

# Project points onto the two in-plane orthogonal axes
out = []
minx = float("Inf")
maxx = float("-Inf")
miny = float("Inf")
maxy = float("-Inf")
for i, p in enumerate(new):
	x = np.dot(p, a)
	y = np.dot(p, b)
	out.append([x, y, data[i]])

	if x > maxx:
		maxx = x
	elif x < minx:
		minx = x
	if y > maxy:
		maxy = y
	elif y < miny:
		miny = y
out = np.array(out)

# Sort the x,y coords in ascending order
indices = np.lexsort((out[:, 1], out[:, 0]))
out = out[indices]

# Write out realigned data
with open("__tmp_cross_section", "w") as outfile:
	for p in out:
		outfile.write(str(p[0]) + " " + str(p[1]) + " " + str(p[2]) + "\n")

# Make gnuplot file
planetit = plane1.split("plane_")[1]
title = planetit.replace(".xtr", "")
output = title + "_comp"
s = ""
s += "unset key\n"
s += "set view map\n"
s += "set title '" + title + "'\n"
s += "set ylabel 'y'\n"
s += "set xlabel 'x'\n"
#s += "set cbrange [0:0.008]\n"
s += "set term postscript eps noenhanced color font 'Times-Roman,24 lw 15'\n"
s += "set output '" + output + ".eps'\n"
s += "splot './__tmp_cross_section' using 1:2:3 with points palette pointsize 1.1 pointtype 5\n"
with open("__tmp_gnuplot", "w") as outfile:
	outfile.write(s)

execute("gnuplot __tmp_gnuplot\n")
execute("convert -flatten -density 300 " + output + ".eps " + output + ".png\n")