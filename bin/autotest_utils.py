import os,os.path,shutil,urllib,sys,signal

def grep(pattern, file):
# This is mainly to fix the return code inversion from grep
	return not os.system('grep "' + pattern + '" "' + file + '"')
	
	
def difflist(list1, list2):	
# returns items in list 2 that are not in list 1
	diff = [];
	for x in list2:
		if x not in list1:
			diff.append(x)
	return diff


def cat_file_to_cmd(file, command):
	if file.endswith('.bz2'):
		os.system('bzcat ' + file + ' | ' + command)
	elif file.endswith('.gz'):
		os.system('zcat ' + file + ' | ' + command)
	else:
		os.system('cat ' + file + ' | ' + command)
	

def get_file(src, dest):
	# get a file, either from url or local
	if (src.startswith('http://')) or (src.startswith('ftp://')):
		print 'PWD: ' + os.getcwd()
		print 'Fetching \n\t', src, '\n\t->', dest
		try:
			urllib.urlretrieve(src, dest)
		except IOError:
			sys.stderr.write("Unable to retrieve %s (to %s)\n" % (src, dest))
			sys.exit(1)
		return dest
	# elif os.path.isfile(src):
	shutil.copyfile(src, dest)
	return dest

def basename(path):
	i = path.rfind('/');
	return path[i+1:]


def force_copy(src, dest):
	if os.path.isfile(dest):
		os.remove(dest)
	return shutil.copyfile(src, dest)


def get_target_arch():
# Work out which CPU architecture we're running on
	if not os.system("egrep '^cpu.*(RS64|POWER(3|4|5)|PPC970|Broadband Engine)' /proc/cpuinfo"):
		return 'ppc64'
	elif not os.system("grep -q 'Opteron' /proc/cpuinfo"):
		# THIS IS WRONG, needs Intel too
		return 'x86_64'
	else:
		return 'i386'


def kernelexpand(kernel):
	# if not (kernel.startswith('http://') or kernel.startswith('ftp://') or os.path.isfile(kernel)):
	if kernel.find('/'):
		w, r = os.popen2('./kernelexpand ' + kernel)

		kernel = r.readline().strip()
		r.close()
		w.close()
	return kernel


def count_cpus():
	f = file('/proc/cpuinfo', 'r')
	cpus = 0
	for line in f.readlines():
		if line.startswith('processor'):
			cpus += 1
	return cpus


# We have our own definiton of system here, as the stock os.system doesn't
# correctly handle sigpipe (ie things like "yes | head" will hang because
# yes doesn't get the SIGPIPE).
def system(cmd):
	signal.signal(signal.SIGPIPE, signal.SIG_DFL)
	try:
		os.system(cmd)
	finally:
		signal.signal(signal.SIGPIPE, signal.SIG_IGN)


def where_art_thy_filehandles():
	os.system("ls -l /proc/%d/fd >> /dev/tty" % os.getpid())


def print_to_tty(string):
	os.system("echo " + string + " >> /dev/tty")


class fd_stack:
	# Note that we need to redirect both the sys.stdout type descriptor
	# (which print, etc use) and the low level OS numbered descriptor
	# which os.system() etc use.

	def __init__(self, fd, filehandle):
		self.fd = fd				# eg 1
		self.filehandle = filehandle		# eg sys.stdout
		self.stack = [(fd, filehandle)]


	def redirect(self, filename):
		fdcopy = os.dup(self.fd)
		self.stack.append( (fdcopy, self.filehandle) )
		# self.filehandle = file(filename, 'w')
		if (os.path.isfile(filename)):
			newfd = os.open(filename, os.O_WRONLY)
		else:
			newfd = os.open(filename, os.O_WRONLY | os.O_CREAT)
		os.dup2(newfd, self.fd)
		os.close(newfd)
		self.filehandle = os.fdopen(self.fd, 'w')


	def tee_redirect(self, filename):
		print_to_tty("tee_redirect to " + filename)
		where_art_thy_filehandles()
		fdcopy = os.dup(self.fd)
		self.stack.append( (fdcopy, self.filehandle) )
		r, w = os.pipe()
		pid = os.fork()
		if pid:			# parent
			os.close(r)
			os.dup2(w, self.fd)
			os.close(w)
		else:			# child
			os.close(w)
			os.dup2(r, 0)
			os.dup2(2, 1)
			os.execlp('tee', 'tee', filename)
		self.filehandle = os.fdopen(self.fd, 'w')
		where_art_thy_filehandles()
		print_to_tty("done tee_redirect to " + filename)

	
	def restore(self):
		print_to_tty("ENTERING RESTORE %d" % self.fd)
		# where_art_thy_filehandles()
		(old_fd, old_filehandle) = self.stack.pop()
		# print_to_tty("old_fd %d" % old_fd)
		# print_to_tty("self.fd %d" % self.fd)
		self.filehandle.close()   # seems to close old_fd as well.
		# where_art_thy_filehandles()
		os.dup2(old_fd, self.fd)
		# print_to_tty("CLOSING FD %d" % old_fd)
		os.close(old_fd)
		# where_art_thy_filehandles()
		self.filehandle = old_filehandle
		# where_art_thy_filehandles()
		# print_to_tty("EXIT RESTORE %d" % self.fd)
