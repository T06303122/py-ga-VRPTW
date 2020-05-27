import os
from json import load

print "on github"
print "I'm glad everythings working now"
print 'woop woop'

instName = 'A-n32-k5.py'
# data/json_customize/A-n32-k5.json
# C:\Users\s.janischka\PycharmProjects\py-ga-VRPTW\data\json_customize\A-n32-k5.json
jsonDataDir = os.path.join(' C:\Users\s.janischka\PycharmProjects\py-ga-VRPTW\data', 'json_customize')
jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)

# I did this xx sharon
print jsonDataDir
print 'jsonFile is ', jsonFile
jsonFile2 = jsonFile.replace(os.sep, '/')
print 'jsonFile2 is ', jsonFile2

#with this one it works
jsonFile3 = 'C:\Users\s.janischka\PycharmProjects\py-ga-VRPTW\data\json_customize\A-n32-k5.json'
print 'jsonFile3 is ', jsonFile3
print 'jsonFile3 works!'

jsonFile4 = 'C:\\Users\\s.janischka\\PycharmProjects\\py-ga-VRPTW\\data\\json_customize\\A-n32-k5.py.json'
print 'jsonFile4 is ', jsonFile3

with open(jsonFile4) as f:
    instance = load(f)

with open(jsonFile3) as f:
    instance = load(f)