import csv
import re
import string
import datetime
import glob

# File locations
inputpath = '/Users/scottfraundorf/Desktop/ADT/Test-Transaction/'
inputsuffix = '-Transaction.txt'
outputpath = '/Users/scottfraundorf/Desktop/ADT/Test-Transaction/'

# Used columns
ParticipantCol = 0
ActionCol = 1
DataCol= 2
ConfigCol = 3
TimeCol = 4

def adttime(timestr):
	return datetime.datetime.strptime(timestr, '%Y-%m-%d %I:%M:%S%p')
	
def tasktype(datastr):
	if ('Answer Selected' in datastr) or ('Start Button Clicked' in datastr) or ('Do Math Clicked:' in datastr):
		return 'Educational'
	elif 'Stimulus Clicked:' in datastr:
		return 'Internet'
	else:
		return 'Bad task'
		
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
	
	# Initialize:
	timeeducational = 0
	timeinternet = 0
	timefirstclick = 0
	timeuntilinternet = 0
	numswitches = 0
	correctQs = 0
	incorrectQs = 0
		
	# Go through events line by line
	for line in csvreader:
		# find the action type
		if line[ActionCol] == 'Session Started':
			# start and ending time:
			starttime = adttime(line[TimeCol])
			lasttime = adttime(line[TimeCol])
			# participant & list:
			participant = line[ParticipantCol]
			# initialize the task:
			currenttask = 'Initial'
			config = line[ConfigCol]
			# block:
			block = int(str.replace(line[DataCol], ' Block ', ''))
		elif line[ActionCol] == 'Click Event':
			# how much time since the last event?
			newtime = adttime(line[TimeCol])
			timeelapsed = (newtime - lasttime).seconds
			# find what type of task this is:
			newtask = tasktype(line[DataCol])			
			if newtask == 'Bad task':
				print 'Bad task - %s' % line[DataCol]
			# new event has started - add the time to the last action
			if currenttask == 'Initial':
				timefirstclick = timeelapsed
			elif currenttask == 'Educational':
				timeeducational += timeelapsed
			elif currenttask == 'Internet':
				timeinternet += timeelapsed
			# if this is not the same as the last task, count it as a switch
			if newtask != currenttask:
				numswitches += 1
			# is this the first Internet task?
			if newtask == 'Internet' and timeuntilinternet == 0:
				timeuntilinternet = (newtime - starttime).seconds
			# update the current task and time
			currenttask = newtask
			lasttime = newtime
		elif line[ActionCol] == 'QuestionAction:':
			# they answered an educational question
			if ' CORRECT' in line[DataCol]:
				correctQs += 1
			elif ' INCORRECT' in line[DataCol] :
				incorrectQs += 1
			else:
				print 'Bad question action - %s' % line[DataCol]
		elif line[ActionCol] == 'Session End':
			# compute the total time in the task
			endtime = adttime(line[-1])
			totaltime = (endtime - starttime).seconds		
			# how much time since the last event?
			timeelapsed = (endtime - lasttime).seconds
			# add the time since the last event to the current task
			if currenttask == 'Initial':
				timeinitial = timeelapsed
			elif currenttask == 'Educational':
				timeeducational += timeelapsed
			elif currenttask == 'Internet':
				timeinternet += timeelapsed			
			# if the Internet was never used
			if timeuntilinternet == 0:
				timeuntilinternet = totaltime		

	# Close the file
	txtfile.close()
	
	# Compute the percentages
	pcteducational = (timeeducational / float(totaltime)) * 100
	pctinternet = (timeinternet / float(totaltime)) * 100
	pctfirstclick = (timefirstclick / float(totaltime)) * 100
	pctfirstinternet = (timeuntilinternet / float(totaltime)) * 100
	
	# Write the summary for this subject
	summaryfile.write('\n')	
	summaryfile.write(','.join([participant, config, str(block),
								str(pcteducational), str(pctinternet), str(pctfirstclick), str(pctfirstinternet),
								str(timeeducational), str(timeinternet), str(timefirstclick), str(timeuntilinternet),
								str(numswitches), str(starttime), str(endtime), str(totaltime), 
								str(correctQs+incorrectQs), str(correctQs)]))

# Wrap up the files
summaryfile.close()
print 'Done!'