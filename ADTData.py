import csv
import datetime
global spellcheck
try:
	from fuzzywuzzy import fuzz
	spellcheck = True
except ImportError, e:
	print "Unable to import from fuzzywuzzy package - spellchecking of answers not available"
	spellcheck = False

def adttime(timestr):
	return datetime.datetime.strptime(timestr, '%Y-%m-%d %I:%M:%S%p')
	
def tasktype(datastr):
	if ('Answer Selected' in datastr) or ('Start Button Clicked' in datastr) or ('Do Math Clicked:' in datastr):
		return 'Educational'
	elif 'Stimulus Clicked:' in datastr:
		return 'Internet'
	else:
		return 'Bad task'
		
class ADTBlock:
	"""A block of the Academic Diligence Task."""
	
	def __init__(self):
		self.timeeducational = 0
		self.timeinternet = 0
		self.timeidle = 0
		self.timefirstclick = 0
		self.timeuntilinternet = 0
		self.pcteducational = 0
		self.pctinternet = 0
		self.pctidle = 0
		self.totaleducational = 0
		self.pctfirstclick = 0
		self.pctfirstinternet = 0
		self.numswitches = 0
		self.correctQs = 0
		self.incorrectQs = 0
		self.totalQs = 0
		self.starttime = 0
		self.endtime = 0
		self.totaltime = 0
		self.lasteventtime = 0
		self.lastcheckintime = 0
		self.participant = ""
		self.blocknumber = 0
		self.currenttask = 'Initial'
		self.blockname = ""
		self.config = ""
		self.configname = ""
		self.uniqueblockid = ""
		self.sessionstarted = False
		self.sessionended = False
		self.idlethreshold = 10
		self.answerkeyunavailable = False		
		
	def add_time(self, task, timeelapsed):
		if task == 'Initial':
			self.timefirstclick = timeelapsed
		elif task == 'Educational':
			if timeelapsed > self.idlethreshold:
				self.timeeducational += self.idlethreshold
				self.timeidle += (timeelapsed - self.idlethreshold)
			else:
				self.timeeducational += timeelapsed
		elif task == 'Internet':
			self.timeinternet += timeelapsed
				
	def click_event(self, newtime, newtask):
		# How much time since the last event?
		timeelapsed = (newtime - self.lasteventtime).seconds
		# Add the time to the last action
		self.add_time(self.currenttask, timeelapsed)
		# If this is not the same as the last task, count it as a switch
		if newtask != self.currenttask:
			self.numswitches += 1
		# Is this the first Internet task?
		if newtask == 'Internet' and self.timeuntilinternet == 0:
			self.timeuntilinternet = (newtime - self.starttime).seconds
		# Update the current task and time:
		self.currenttask = newtask
		self.lasteventtime = newtime
		
	def check_in(self, newtime):
		# Update the time of the last check in:
		self.lastcheckintime = newtime
		
	def end_block(self, endtime):
		# Ending time & total time in this block
		self.endtime = endtime
		self.totaltime = (self.endtime - self.starttime).seconds		
		# How much time since the last event?
		timeelapsed = (self.endtime - self.lasteventtime).seconds		
		# Add the time since the last event to the current task:
		self.add_time(self.currenttask, timeelapsed)
		# If the Internet was never used
		if self.timeuntilinternet == 0:
			self.timeuntilinternet = self.totaltime		
		# If nothing was ever clicked
		if self.timefirstclick == 0:
			self.timefirstclick = self.totaltime
		# Compute the percentages
		self.pcteducational = (self.timeeducational / float(self.totaltime)) * 100
		self.pctidle = (self.timeidle / float(self.totaltime)) * 100
		self.pcttotaleducational = ((self.timeeducational + self.timeidle) / float(self.totaltime)) * 100
		self.pctinternet = (self.timeinternet / float(self.totaltime)) * 100
		self.pctfirstclick = (self.timefirstclick / float(self.totaltime)) * 100
		self.pctfirstinternet = (self.timeuntilinternet / float(self.totaltime)) * 100
		
	def add_question(self):
		self.totalQs += 1
		
	def evaluate_recall_question(self, selftestfile, response, currentkey, fuzzthreshold):
		global spellcheck
		# Figure out where in the cycle of items we are
		questionid = currentkey.get_id_from_serial_position(self.totalQs)
		# Find the intended response
		intendedresponse = currentkey.get_intended_response(questionid)
		# Compare the participant response to the intended response
		if spellcheck and fuzz.ratio(response.lower(), intendedresponse.lower()) >= fuzzthreshold:
			# Close match
			scoringtype = 'Auto'
			correct = True
		elif response.lower() == intendedresponse.lower():
			# Exact match, even if spellcheck unavailable:
			scoringtype = 'Auto'
			correct = True
		else:
			scoringtype = 'Manual'
			correct = bool()
		if scoringtype == 'Auto':
			correctstring = str(int(correct))
		else:
			correctstring = ""
		self.write_recall_response(selftestfile, questionid, intendedresponse, response, scoringtype, correctstring)
		# Add to the list of questions
		if scoringtype == 'Auto':
			self.score_question(correct)
		else:
			self.unscored_question()
		
	def evaluate_tf_question(self, correct):
		self.score_question(correct)
		
	def score_question(self, correct):
		self.add_question()
		if correct:
			self.correctQs += 1
		else:
			self.incorrectQs += 1
	
	def unscored_question(self):
		self.add_question()
								
	def write_recall_response(self, selftestfile, questionid, intendedresponse, response, scoringtype, correct):
		selftestfile.write('\n')	
		selftestfile.write(','.join([self.participant, self.config, str(self.blocknumber),
		                        str(questionid+1), str(self.totalQs+1),
		                        intendedresponse, response, scoringtype, correct]))
		
	def write_summary(self, summaryfile):
		summaryfile.write('\n')	
		summaryfile.write(','.join([self.participant, self.config, str(self.blocknumber),
								str(self.pcteducational), str(self.pctidle), str(self.pcttotaleducational),
								str(self.pctinternet), str(self.pctfirstclick), str(self.pctfirstinternet),
								str(self.timeeducational), str(self.timeidle), str(self.timeeducational + self.timeidle),
								str(self.timeinternet), str(self.timefirstclick), str(self.timeuntilinternet),
								str(self.numswitches), str(self.starttime),
								str(self.endtime), str(self.totaltime), 
								str(self.totalQs), str(self.correctQs)]))
								
class AnswerKey:
	"""An answer key for free response questions."""
	
	def __init__(self):
		self.answerkey = dict()
		self.numquestions = 0
		
	def read_key(self, inputpath, filename):
		# Open the file and begin reading CSV
		answerkeyfilename = inputpath + filename
		answerkeyfile = open(answerkeyfilename, 'rb')
		answerkeyreader = csv.reader(answerkeyfile)
		# Skip variable names
		line = answerkeyreader.next()
		# Read each question
		for line in answerkeyreader:
			questionid = int(line[0])-1 # 1-based in file
			intendedresponse = line[1]
			self.answerkey[questionid] = intendedresponse
		# Count the number of questions
		self.numquestions = len(self.answerkey)

	def get_id_from_serial_position(self, questionnum):
		questionid = questionnum % self.numquestions
		return questionid
		
	def get_intended_response(self, questionid):
		return self.answerkey[questionid]