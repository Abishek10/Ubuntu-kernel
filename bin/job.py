from autotest_utils import *
import os, sys, kernel, test, pickle, threading
import profilers

# Parallel run interface.
class AsyncRun(threading.Thread):
    def __init__(self, cmd):
	threading.Thread.__init__(self)        
	self.cmd = cmd
    def run(self):
    	x = self.cmd.pop(0)
	x(*self.cmd)

# JOB: the actual job against which we do everything.
class job:
	def __init__(self, control, jobtag='default'):
		self.autodir = os.environ['AUTODIR']
		self.testdir = self.autodir + '/tests'
		self.profdir = self.autodir + '/profilers'
		self.tmpdir = self.autodir + '/tmp'
		if os.path.exists(self.tmpdir):
			system('rm -rf ' + self.tmpdir)
		os.mkdir(self.tmpdir)
		self.resultdir = self.autodir + '/results/' + jobtag
		if os.path.exists(self.resultdir):
			system('rm -rf ' + self.resultdir)
		os.mkdir(self.resultdir)
		os.mkdir(self.resultdir + "/debug")
		os.mkdir(self.resultdir + "/analysis")
		
		self.control = control
		self.jobtab = jobtag

		self.stdout = fd_stack(1, sys.stdout)
		self.stderr = fd_stack(2, sys.stderr)

		self.profilers = profilers.profilers(self)

	def kernel(self, topdir, base_tree):
		return kernel.kernel(self, topdir, base_tree)

	def runtest(self, tag, testname, *test_args):
		sys.path.insert(0, self.testdir + '/' + testname)
		exec "import %s" % testname
		exec "mytest = %s.%s(self, testname + '.' + tag)" % (testname, testname)
		mytest.bindir = self.testdir + '/' + testname
		mytest.srcdir = mytest.bindir + '/src'
		if os.path.exists(mytest.srcdir):
			# Bad idea, as it'll always rebuild, but will do for now
			system('rm -rf ' + mytest.srcdir)
		mytest.tmpdir = self.tmpdir + '/' + testname
		os.mkdir(mytest.tmpdir)
		mytest.run(testname, test_args)

	def noop(self, text):
		print "job: noop: " + text

	# Job control primatives.
	def parallel(self, *l):
		tasks = []
		for t in l:
			task = AsyncRun(t)
			tasks.append(task)
			task.start()
		for t in tasks:
			t.join()

	# XXX: should have a better name.
	def quit(self):
		sys.exit(5)

	def complete(self, status):
		# We are about to exit 'complete' so clean up the control file.
		try:
			os.unlink(self.control + '.state')
		except:
			pass
		if os.path.exists(self.control):
			os.rename(self.control, self.control + '.complete')
		sys.exit(status)

	# STEPS: the stepping engine -- if the control file defines
	#        step_init we will be using this engine to drive multiple
	#        runs.
	steps = []
	def next_step(self, step):
		self.steps.append(step)
		pickle.dump(self.steps, open(self.control + '.state', 'w'))

	def step_engine(self, init):
		# If there is a mid-job state file load that in and continue
		# where it indicates.  Otherwise start stepping at the passed
		# entry.
		try:
			self.steps = pickle.load(open(self.control + '.state',
				'r'))
		except:
			self.next_step(init)

		# Run the step list.
		while len(self.steps) > 0:
			step = self.steps.pop(0)
			pickle.dump(self.steps, open(self.control + '.state',
				'w'))

			cmd = step.pop(0)
			cmd(*step)

		# all done, clean up and exit.
		self.complete(0)

