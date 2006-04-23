class dbench(test.test):
	version = 1

	# http://samba.org/ftp/tridge/dbench/dbench-3.04.tar.gz
	def setup(self, tarball = self.bindir + 'dbench-3.04.tar.gz'):
		self.tarball = unmap_potential_url(tarball, self.tmpdir)
		extract_tarball_to_dir(self.tarball, self.srcdir)
		os.chdir(self.srcdir)

		system('./configure')
		system('make')
		
	def execute(self, iterations = 1, args = None):
		for i in range(1, iterations+1):
			args = args + ' -c '+self.srcdir+'/client_oplocks.txt'
			system(self.srcdir + '/dbench ' + args)
