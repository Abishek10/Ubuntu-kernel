#!/usr/bin/env python
#

# An engine for processing bugs. The idea is to have a small config file, one
# element of which is a time-stamp of when the last time the engine ran looking for
# changes to LP bugs.
#

from sys                                import argv, exit
from datetime                           import datetime
from datetime                           import timedelta
import json

from lpltk.LaunchpadService             import LaunchpadService
from ktl.utils                          import error, date_to_string, string_to_date, stdo
from ktl.std_app                        import StdApp
from ktl.ubuntu                         import Ubuntu
from ktl.kernel_bug                     import KernelBug
from ktl.termcolor                      import colored
from bug_handler                        import BugHandler

from cmdline                            import Cmdline, CmdlineError

# BugEngineError
#
class BugEngineError(Exception):
    # __init__
    #
    def __init__(self, error):
        self.msg = error

# BugEngine
#
class BugEngine(StdApp):
    # __init__
    #
    def __init__(self, default_config={}, cmdline=None):
        self.defaults = default_config
        self.defaults['show'] = False
        StdApp.__init__(self)
        self.bdb = None
        if cmdline is None:
            self.cmdline = Cmdline()
        else:
            self.cmdline = cmdline

        self.show_buff = ''

    # __initialize
    #
    # A separate initialize that we can control when it gets called (not
    # when the object is instantiated).
    #
    def __initialize(self):
        self.ubuntu = Ubuntu()

        if 'staging' in self.cfg:
            self.defaults['launchpad_services_root'] = 'qastaging'
        self.vout(5, " . Connecting to Launchpad\n")
        self.lp = LaunchpadService(self.defaults)

        # The service.distributions property is a collection of distributions. We
        # pretty much only care about one, 'ubuntu'.
        #
        self.distro = self.lp.distributions['ubuntu']

        if 'debug' in self.cfg and 'kbug' in self.cfg['debug']:
            KernelBug.debug = True

        return

    # startup
    #
    def startup(self):
        """
        Performs tasks that need to be done before "main" is run.
        """
        return

    # shutdown
    #
    def shutdown(self):
        """
        Performs any cleanup tasks.
        """

        if self.bdb is not None:
            self.cfg['bugs_database'] = self.bdb
            if 'update-config' in self.cfg and self.cfg['update-config']:
                with open(self.cfg['configuration_file'], 'w') as f:
                    f.write(json.dumps(self.cfg, sort_keys=True, indent=4))

        return

    # run
    #
    def run(self):
        using_search_since = False
        try:
            self.merge_config_options(self.defaults, self.cmdline.process(argv, self.defaults))
            self.cmdline.verify_options(self.cfg)

            self.__initialize()

            if 'bug ids' in self.cfg:
                self.bug_handler_startup()
                for bug_id in self.cfg['bug ids']:
                    self.show_buff = ''

                    bug = KernelBug(self.lp.get_bug(bug_id))

                    try:
                        self.bug_handler(bug, self.cfg['package'])
                    except:
                        msg  = "An exception whas caught.\n"
                        msg += "            bug-id: %d.\n" % (bug.id)
                        msg += "           package: %s.\n" % (self.cfg['package'])
                        error(msg)
                        raise

                    if self.cfg['show']:
                        print(self.show_buff)
                self.bug_handler_shutdown()

            else:
                # Within the configuration file, there should be a section that is for bug information. If
                # it doesn't exist, create it.
                #
                if 'bugs_database' not in self.cfg:
                    self.cfg['bugs_database'] = {}
                    self.cfg['bugs_database']['packages'] = {}

                    six_months_ago = datetime.today() - timedelta(days=(31 * 6))
                    self.cfg['bugs_database']['updated'] = six_months_ago

                self.bdb = self.cfg['bugs_database']

                # Within the bug information in the configuration file should be a timestamp of the last
                # time this engine worked on the configuration file and worked on new bugs. If it doesn't
                # exist, this is a problem.
                #
                if 'updated' in self.bdb:
                    search_since = string_to_date(self.bdb['updated'])
                else:
                    raise BugEngineError("There is no timestamp in the configuration file. This is not good.")

                if 'search-criteria-status' in self.cfg:
                    search_criteria_status = self.cfg['search-criteria-status']
                else:
                    search_criteria_status = ["New"] # A list of the bug statuses that we care about

                now = datetime.utcnow()
                self.bdb['updated'] = date_to_string(now)

                # Now find all the New bugs for all the packages we care about and do something with them.
                #
                #for package_name in self.ubuntu.active_packages: # FIXME bjf: do we want to do all the packages or just the linux
                                                                  #            package? there's plenty to work on with just the one
                                                                  #            but we don't want to ignore the others either.
                for package_name in ['linux']:
                    self.vout(5, '%s\n' % package_name)

                    try:
                        source_package = self.distro.get_source_package(package_name)
                        if source_package == None:
                            raise BugEngineError("The source package (%s) does not exist in LaunchPad." % (package_name))

                        self.vout(5, "   since: %s" % (search_since))
                        tasks = source_package.search_tasks(status=search_criteria_status, modified_since=search_since)
                        #tasks = source_package.search_tasks(status=search_criteria_status)

                        this_package_bugs = None
                        self.bug_handler_startup()
                        for task in tasks:
                            if package_name not in self.bdb['packages']:
                                self.bdb['packages'][package_name] = {}
                                self.bdb['packages'][package_name]['bugs'] = {}
                            this_package_bugs = self.bdb['packages'][package_name]['bugs']

                            bug = KernelBug(task.bug)
                            stdo('%s (%s)\r' % (bug.id, package_name))
                            self.__verbose_bug_info(bug)

                            try:
                                self.show_buff = ''
                                self.bug_handler(bug, package_name)
                                if self.cfg['show']:
                                    if self.show_buff != '':
                                        print(self.show_buff)
                            except:
                                msg  = "An exception whas caught.\n"
                                msg += "            bug-id: %d.\n" % (bug.id)
                                if 'package' in self.cfg:
                                    msg += "           package: %s.\n" % (self.cfg['package'])
                                error(msg)
                                raise

                        self.bug_handler_shutdown()

                    except:
                        raise
                        raise BugEngineError("Exception caught processing the tasks, building the bugs database.\n")

        # Handle command line errors.
        #
        except CmdlineError as e:
            self.cmdline.error(e.msg, self.defaults)
            exit(0)

        return

    # bug_handler_startup
    #
    def bug_handler_startup(self):
        """
        Setup the list of bug handler plugins that this script will use.

        The plugin list is pulled in here because we only want to do it once
        and not every time the bug_handler is called. And also, because this
        method is called after the base class has created self.lp.
        """
        self.bug_handlers = BugHandler.get_plugins(self.lp, self.vout)

        # Yes, the verbose handling is a little stupid right now, it will get
        # cleaned up "soon".
        #
        if 'verbose' in self.cfg:
            BugHandler.verbose = self.cfg['verbose']

        if 'verbosity' in self.cfg:
            BugHandler.verbosity = self.cfg['verbosity']
        pass

    # bug_handler_shutdown
    #
    def bug_handler_shutdown(self):
        pass

    # bug_handler
    #
    def bug_handler(self, bug, package_name):
        """
        Called for every bug that is found via a task search.
        """
        for handler in self.bug_handlers:
            handler.show_buff = ''
            result = handler.run(bug, self.get_relevant_task(bug, package_name), package_name)
            if not result: break
            self.show_buff += handler.show_buff

        return

    # main
    #
    def main(self):
        """
        Run the base class methods.
        """
        try:
            self.startup()
            self.run()
            self.shutdown()

        # Handle the user presses <ctrl-C>.
        #
        except KeyboardInterrupt:
            exit(0)

        # Handle application errors.
        #
        except BugEngineError as e:
            error(e.msg)

        return

    # __verbose_bug_info
    #
    def __verbose_bug_info(self, bug):
        if 'verbosity' in self.cfg and self.cfg['verbosity'] < 2:
            print(" ")
            print(colored("    %s: %s" % (bug.id, bug.title), 'blue'))
            print(" ")
            print("        Owner: %s" % ("None" if bug.owner is None else bug.owner.display_name))

            tags = ""
            for t in bug.tags:
                tags += t
                tags += " "
            print("        Tags:")
            print("            %s" % (tags))

            tasks = bug.tasks
            print("        Tasks:")
            for task in tasks:
                print("            %45s %20s %20s" % (task.bug_target_name, task.status, task.importance))

    # get_relevant_task
    #
    def get_relevant_task(self, bug, pkg):
        retval = None
        for t in bug.tasks:
            name       = t.bug_target_name
            p = name.replace(' (Ubuntu)', '')
            if pkg == p:
                retval = t
                break
        return retval

# vi:set ts=4 sw=4 expandtab:
