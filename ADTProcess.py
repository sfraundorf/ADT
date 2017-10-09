import csv
import re
import string
import datetime
import glob
from ADTData import *

# File locations
inputpath = '/Users/scottfraundorf/Desktop/ADT/Test-SelfTestAnswers/'
inputsuffix = '-Transaction.txt'
outputpath = '/Users/scottfraundorf/Desktop/ADT/Test-SelfTestAnswers/'

# Threshold (in seconds) for "idling" on the educational activity
IdleThreshold = 10

# Maximum time (in seconds) allowed per block:
# Set to 0 if you do not want to impose a maximum time per block
MaxSeconds = 240

# Show detailed feedback in the console on session start times
# (may be relevant to debugging bad "Session Start" messages from
# Qualtrics)
verbose = False

# Threshold for auto-matching a string via spell-check.
# Higher number = stricter scoring. Suggested: 90
FuzzThreshold = 90

# Used columns
ParticipantCol = 0
ActionCol = 1
DataCol= 2
ConfigCol = 3
TimeCol = 4	
		
# Start the transaction summary file:
outputfilename = outputpath + 'summary.csv'
summaryfile = open(outputfilename, 'w')
summaryfile.write('Participant,Config,Block,' + \
                  'PctEducationNoIdle,PctIdle,PctEducationTotal,' + \
                  'PctMedia,PctUntilFirstClick,PctUntilFirstMedia,' + \
                  'SecEducationNoIdle,SecIdle,SecEducationTotal,' + \
                  'SecMedia,SecUntilFirstClick,SecUntilFirstMedia,' + \
                  'NumSwitches,StartTime,EndTime,TotalSeconds,Attempted,Correct')
stopTime = 0

# Function to create a self-test answer file, if needed:
def init_self_test(outputpath):
	outputfilename = outputpath + 'selftest.csv'
	selftestfile = open(outputfilename, 'w')
	selftestfile.write('Participant,Config,Block,' + \
			'QuestionID,SerialPosition,' + \
			'AnswerKey,Response,ScoringType,Correct')
	return selftestfile
	
# Are we tracking self-test responses?
selftestfileopen = False

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
			continue
	
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
				if verbose:
					print line
					print " ERROR"
				continue
			else:
				if currentblock.sessionstarted and not currentblock.sessionended:
					endtime = max(currentblock.lastcheckintime,
					              currentblock.lasteventtime)
					# Update the block data:
					currentblock.end_block(endtime)
					# Write the summary for this block:
					currentblock.write_summary(summaryfile)
					currentblock.sessionended = True
					blocknumber += 1					
				# A real block has started
				# Initialize the block:
				if verbose:
					print line
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
				currentblock.configname = re.split('.txt$', currentblock.config)[0]
				currentblock.uniqueblockid = currentblock.blockname + '-' + currentblock.config
				# block number:
				currentblock.blocknumber = blocknumber
				# idling threshold:
				currentblock.idlethreshold = IdleThreshold
				# initialize the task:
				currentblock.currenttask = 'Initial'
				# time at which this block needs to be capped
				if MaxSeconds > 0:
					# Cap requested
					stopTime = currentblock.starttime + datetime.timedelta(seconds=MaxSeconds)
				else:
					# No cap requested
					stopTime = 0
					
		if stopTime != 0:
			currentTime = datetime.datetime.strptime(line[-1], '%Y-%m-%d %I:%M:%S%p')
			#Check to see if session needs to be capped
			if currentTime > stopTime:
				if not(currentblock.sessionended):
					if verbose:
						print "Capping Session"
					currentblock.end_block(stopTime)
					# Write the summary for this block:
					currentblock.write_summary(summaryfile)
					currentblock.sessionended = True
					blocknumber += 1
				continue
			
		if line[ActionCol] == 'Click Event':
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
			# if noted whether the question is correct or not, tally it
			if ' CORRECT' in line[DataCol]:
				currentblock.evaluate_tf_question(True)
			elif ' INCORRECT' in line[DataCol] :
				currentblock.evaluate_tf_question(False)
			elif 'Question ' in line[DataCol]:
				if "REREAD" in line[DataCol]:
					# pure re-read, nothing to score
					currentblock.unscored_question()
				else:
					# self-test response
					if not selftestfileopen:
						# Start the self-test answer file if it doesn't
						# already exist
						selftestfile = init_self_test(outputpath)
						# Note it
						selftestfileopen = True	
					if currentblock.totalQs == 0 and not currentblock.answerkeyunavailable:
						# if the first question in a block, read in the
						# answer key
						answerkeyfilename = currentblock.configname + '_Answers.csv'					
						currentkey = AnswerKey()
						try:
							currentkey.read_key(inputpath, answerkeyfilename)
						except IOError:
							print "Can't find or open answer key with filename %s - no answer scoring for this block" % answerkeyfilename
							currentblock.answerkeyunavailable = True
					# Get the response and evaluate it
					if not currentblock.answerkeyunavailable:
						response = re.split('Question [0-9]+?:', line[DataCol])[1]
						currentblock.evaluate_recall_question(selftestfile, response, currentkey, FuzzThreshold)
				
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
	stopTime= 0							

# Wrap up the files
summaryfile.close()
if selftestfileopen:
	selftestfile.close()
print 'Processed %d file(s)' % (len(filelist))
print 'Done!'
