import csv
import re
import string
import datetime
import glob
from ADTData import *

# File locations
inputpath = '/Users/scottfraundorf/Desktop/ADT/Test-3Block-HS/'
inputsuffix = '1.csv'
outputpath = '/Users/scottfraundorf/Desktop/ADT/Test-3Block-HS/'

# Used columns
ParticipantCol = 0
ActionCol = 1
DataCol= 2
ConfigCol = 3
TimeCol = 4	

# Threshold for "idling" on the educational activity
IdleThreshold = 10
		
# Start the output file:
outputfilename = outputpath + 'summary.csv'
summaryfile = open(outputfilename, 'w')
summaryfile.write('Participant,Config,Block,' + \
                  'PctEducationNoIdle,PctIdle,PctEducationTotal,' + \
                  'PctMedia,PctUntilFirstClick,PctUntilFirstMedia,' + \
                  'SecEducationNoIdle,SecIdle,SecEducationTotal,' + \
                  'SecMedia,SecUntilFirstClick,SecUntilFirstMedia,' + \
                  'NumSwitches,StartTime,EndTime,TotalSeconds,Attempted,Correct')
                  
# Get a list of all the input files:
filelist = glob.glob(inputpath+'*'+inputsuffix)

for textfilename in filelist:
	print 'Processing file %s...' % textfilename

	# Open the original file
	txtfile = open(textfilename, 'rb')
		
	# Begin reading the CSV
	csvreader = csv.reader(txtfile)
	
	# Skip variable names
	line = csvreader.next()
	
	# Go through events line by line
	for line in csvreader:
		# find the action type
		if len(line) < ActionCol:
			# blank line
			pass
	
		elif line[ActionCol] == 'Session Started':
			# new block!
			# Initialize the block:
			currentblock = ADTBlock()
			# start and ending time:
			currentblock.starttime = adttime(line[TimeCol])
			currentblock.lastcheckintime = adttime(line[TimeCol])
			currentblock.lasteventtime = adttime(line[TimeCol])
			# participant & list:
			currentblock.participant = line[ParticipantCol]
			currentblock.config = line[ConfigCol]
			# block name/ID:
			currentblock.block = int(str.replace(line[DataCol], ' Block ', ''))
			# idling threshold:
			currentblock.idlethreshold = IdleThreshold
			# initialize the task:
			currentblock.currenttask = 'Initial'
			
		elif line[ActionCol] == 'Click Event':
			# Get the time:
			newtime = adttime(line[TimeCol])
			# And the task:
			newtask = tasktype(line[DataCol])			
			if newtask == 'Bad task':
				print 'Bad task - %s' % line[DataCol]
			# Update the block data:
			currentblock.click_event(newtime, newtask)
			
		elif line[ActionCol] == '5SecondCheckIn':
			# Get the time:
			newtime = adttime(line[TimeCol])
			# Check in:
			currentblock.check_in(newtime)
						
		elif line[ActionCol] == 'QuestionAction:':
			# they answered an educational question
			if ' CORRECT' in line[DataCol]:
				currentblock.correctQs += 1
			elif ' INCORRECT' in line[DataCol] :
				currentblock.incorrectQs += 1
			else:
				print 'Bad question action - %s' % line[DataCol]
				
		elif line[ActionCol] == 'Session End':
			# End of block
			# Get the end time:
			endtime = adttime(line[-1])
			# Update the block data:
			currentblock.end_block(endtime)
			# Write the summary for this block:
			currentblock.write_summary(summaryfile)
			# Note that the block formally ended:
			currentblock.sessionended = True
	
	# End of file
	# Did we end the session successfully?
	if currentblock.sessionended == False:
		# No -- end the session now, recording everything
		# up to the last checkin or event (whichever is
		# most recent):
		endtime = max(currentblock.lastcheckintime,
		              currentblock.lasteventtime)
		# Update the block data:
		currentblock.end_block(endtime)
		# Write the summary for this block:
		currentblock.write_summary(summaryfile)
																
	# Close the file
	txtfile.close()								

# Wrap up the files
summaryfile.close()
print 'Done!'