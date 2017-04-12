import csv
import re
import string
import datetime
import glob
from ADTData import *

# File locations
inputpath = '/Users/scottfraundorf/Desktop/ADT/Test-3Block-Transaction/'
inputsuffix = '-Transaction.txt'
outputpath = '/Users/scottfraundorf/Desktop/ADT/Test-3Block-Transaction/'

# Used columns
ParticipantCol = 0
ActionCol = 1
DataCol= 2
ConfigCol = 3
TimeCol = 4	
		
# Start the output file:
outputfilename = outputpath + 'summary.csv'
summaryfile = open(outputfilename, 'w')
summaryfile.write('Participant,Config,Block,PctEducation,PctMedia,PctUntilFirstClick,PctUntilFirstMedia,' + \
                  'SecEducation,SecMedia,SecUntilFirstClick,SecUntilFirstMedia,' + \
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
		if line[ActionCol] == 'Session Started':
			# new block!
			# Initialize the block:
			currentblock = ADTBlock()
			# start and ending time:
			currentblock.starttime = adttime(line[TimeCol])
			currentblock.lasttime = adttime(line[TimeCol])
			# participant & list:
			currentblock.participant = line[ParticipantCol]
			currentblock.config = line[ConfigCol]
			# block name/ID:
			currentblock.block = int(str.replace(line[DataCol], ' Block ', ''))
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
			# Write the summary for this block
			currentblock.write_summary(summaryfile)
																
	# End of file--close
	txtfile.close()								

# Wrap up the files
summaryfile.close()
print 'Done!'