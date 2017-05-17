import csv
import re
import string
import datetime
import glob
from ADTData import *

# File locations
inputpath = '/Users/scottfraundorf/Desktop/ADT/3 block data/'
inputsuffix = '-Transaction.txt'
outputpath = '/Users/scottfraundorf/Desktop/ADT/3 block data/'

# Threshold (in seconds) for "idling" on the educational activity
IdleThreshold = 10

# Used columns
ParticipantCol = 0
ActionCol = 1
DataCol= 2
ConfigCol = 3
TimeCol = 4	
		
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
	
	# Initialize a blank block
	currentblock = ADTBlock()
	
	# Reset the block number
	blocknumber = 0
	
	# Go through events line by line
	for line in csvreader:
		# find the action type
		if len(line) < (ActionCol+1):
			# blank line
			pass
	
		elif line[ActionCol] == 'Session Started':
			# possible new block!
			# get its identifiers:
			blockname = line[DataCol]
			config = line[ConfigCol]
			uniqueblockid = blockname + '-' + config
			if currentblock.sessionstarted == True and uniqueblockid == currentblock.uniqueblockid:
				# if this block has already started,
				# this is a "phantom" Session Start that
				# the ADT puts out sometimes (bug).
				# Ignore it
				pass
			else:
				# A real block has started
				# Initialize the block:
				currentblock = ADTBlock()
				# start and ending time:
				currentblock.starttime = adttime(line[TimeCol])
				currentblock.lastcheckintime = adttime(line[TimeCol])
				currentblock.lasteventtime = adttime(line[TimeCol])
				# participant:
				currentblock.participant = line[ParticipantCol]
				# block name/ID:
				currentblock.blockname = line[DataCol]
				currentblock.config = line[ConfigCol]
				currentblock.uniqueblockid = currentblock.blockname + '-' + currentblock.config
				# block number:
				currentblock.blocknumber = blocknumber
				# idling threshold:
				currentblock.idlethreshold = IdleThreshold
				# initialize the task:
				currentblock.currenttask = 'Initial'
			
		elif line[ActionCol] == 'Click Event':
			# Confirm that at least one thing has happened in the block
			currentblock.sessionstarted = True
			# Get the time:
			newtime = adttime(line[TimeCol])
			# And the task:
			newtask = tasktype(line[DataCol])			
			if newtask == 'Bad task':
				print 'Bad task - %s' % line[DataCol]
			# Update the block data:
			currentblock.click_event(newtime, newtask)
			
		elif line[ActionCol] == '5SecondCheckIn':
			# Confirm that at least one thing has happened in the block
			currentblock.sessionstarted = True		
			# Get the time:
			newtime = adttime(line[TimeCol])
			# Check in:
			currentblock.check_in(newtime)
						
		elif line[ActionCol] == 'QuestionAction:':
			# Confirm that at least one thing has happened in the block
			currentblock.sessionstarted = True		
			# they answered an educational question
			if ' CORRECT' in line[DataCol]:
				currentblock.score_question(True)
			elif ' INCORRECT' in line[DataCol] :
				currentblock.score_question(False)
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
			# Update block counter:
			blocknumber += 1
	
	# End of file
	# Is this a real block that did start, but did not
	# end successfully?
	if currentblock.sessionstarted and not currentblock.sessionended:
		# No -- end the session now, recording everything
		# up to the last checkin or event (whichever is
		# most recent):
		endtime = max(currentblock.lastcheckintime,
		              currentblock.lasteventtime)
		# Update the block data:
		currentblock.end_block(endtime)
		# Write the summary for this block:
		currentblock.write_summary(summaryfile)
		# Update block counter:		
		blocknumber += 1
																
	# Close the file
	txtfile.close()								

# Wrap up the files
summaryfile.close()
print 'Processed %d file(s)' % (len(filelist) + 1)
print 'Done!'