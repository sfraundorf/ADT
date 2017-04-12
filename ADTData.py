import datetime

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
		self.timefirstclick = 0
		self.timeuntilinternet = 0
		self.pcteducational = 0
		self.pctinternet = 0
		self.pctfirstclick = 0
		self.pctfirstinternet = 0
		self.numswitches = 0
		self.correctQs = 0
		self.incorrectQs = 0
		self.starttime = 0
		self.endtime = 0
		self.totaltime = 0
		self.lasttime = 0
		self.participant = ""
		self.block = ""
		self.currenttask = 'Initial'
		self.config = ""
		
	def add_time(self, task, timeelapsed):
		if task == 'Initial':
			self.timefirstclick = timeelapsed
		elif task == 'Educational':
			self.timeeducational += timeelapsed
		elif task == 'Internet':
			self.timeinternet += timeelapsed
				
	def click_event(self, newtime, newtask):
		# How much time since the last event?
		timeelapsed = (newtime - self.lasttime).seconds
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
		self.lasttime = newtime
		
	def end_block(self, endtime):
		# Ending time & total time in this block
		self.endtime = endtime
		self.totaltime = (self.endtime - self.starttime).seconds		
		# How much time since the last event?
		timeelapsed = (self.endtime - self.lasttime).seconds
		# Add the time since the last event to the current task
		self.add_time(self.currenttask, timeelapsed)
		# If the Internet was never used
		if self.timeuntilinternet == 0:
			self.timeuntilinternet = self.totaltime		
		# If nothing was ever clicked
		if self.timefirstclick == 0:
			self.timefirstclick = self.totaltime
		# Compute the percentages
		self.pcteducational = (self.timeeducational / float(self.totaltime)) * 100
		self.pctinternet = (self.timeinternet / float(self.totaltime)) * 100
		self.pctfirstclick = (self.timefirstclick / float(self.totaltime)) * 100
		self.pctfirstinternet = (self.timeuntilinternet / float(self.totaltime)) * 100

	def write_summary(self, summaryfile):
		summaryfile.write('\n')	
		summaryfile.write(','.join([self.participant, self.config, str(self.block),
								str(self.pcteducational), str(self.pctinternet), 
								str(self.pctfirstclick), str(self.pctfirstinternet),
								str(self.timeeducational), str(self.timeinternet), 
								str(self.timefirstclick), str(self.timeuntilinternet),
								str(self.numswitches), str(self.starttime),
								str(self.endtime), str(self.totaltime), 
								str(self.correctQs+self.incorrectQs), str(self.correctQs)]))	