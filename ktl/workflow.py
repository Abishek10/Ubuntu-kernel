#!/usr/bin/env python
#

from utils              import date_to_string
from datetime           import datetime
import re

# UbuntuError
#
class UbuntuError(Exception):
    # __init__
    #
    def __init__(self, error):
        self.msg = error

# Methods related to workflow in tracking bugs
#

class Properties:

    # __init__
    #
    def __init__(self, bug):
        # get the current properties and save them
        self.bug = bug
        self.oldprops = bug.properties
        self.newprops = {}
    
    # setBugProperties
    #
    # Note - this should perhaps be in lpltk
    def set(self, newprops):
        """
        Set key:value pairs in the bug description. This
        follows a convention established in lpltk
        Input: a lpltk bug object and a dictionary
        of key:value pairs
        This function only stages the changes and does not write them to the
        bug description, to avoid rewriting the description
        multiple times
        """
        self.newprops.update(newprops)

    # flushBugProperties
    #
    # Note - this should perhaps be in lpltk
    def flush(self):
        """
        If needed, rewrite the bug description including
        changes staged by calls to setBugProperties
        """
        # See whether we really need to write anything new
        rmlist = []
        for keyname in self.newprops:
            if keyname in self.oldprops:
                if self.oldprops[keyname] == self.newprops[keyname]:
                    rmlist.append(keyname)
                    continue
        for keyname in rmlist:
            del self.newprops[keyname]
        if len(self.newprops) == 0:
            return
    
        # Set a name:value pair in a bug description
        olddescr = self.bug.description
        newdscr = ''
        re_kvp            = re.compile("^(\s*)([\.\-\w]+):\s*(.*)$")
        # copy everything, removing an existing one with this name if it exists
        foundProp = False
        for line in olddescr.split("\n"):
            # Skip empty lines after we start properties
            if line == '' and foundProp:
                continue
            m = re_kvp.match(line)
            if m:
                foundProp = True
                # There is a property on this line (assume only one per line)
                # see if it matches the one we're adding
                level = m.group(1)
                item = m.group(2)
                value = m.group(3)
                key = item
                if len(level) > 0:
                    key = "%s.%s" %(last_key[''], item)
                if key in self.newprops:
                    # we're going to be adding this one, remove the existing one
                    continue
            newdscr = newdscr + line + '\n'

        for k in self.newprops:
            newdscr = newdscr + '%s:%s\n' % (k, self.newprops[k])
        self.bug.description = newdscr
        return


# Workflow
#
class Workflow:

    # Tasks, tags, etc vary according to the package name
    tdb = {
        'linux' :  {
            'task_assignment' : {
                'prepare-package'            : 'canonical-kernel-team',
                'prepare-package-lbm'        : 'canonical-kernel-team',
                'prepare-package-lrm'        : 'canonical-kernel-team',
                'prepare-package-lum'        : 'canonical-kernel-team',
                'prepare-package-meta'       : 'canonical-kernel-team',
                'prepare-package-ports-meta' : 'canonical-kernel-team',
                #'upload-to-ppa'              : 'canonical-kernel-team',
                'promote-to-proposed'        : 'ubuntu-sru',
                'verification-testing'       : 'canonical-kernel-team',
                'certification-testing'      : 'canonical-hw-cert',
                'regression-testing'         : 'canonical-platform-qa',
                'promote-to-updates'         : 'ubuntu-sru',
                'promote-to-security'        : 'ubuntu-sru',
                'security-signoff'           : 'canonical-security'
                },
            'initial_bug_tags' :
                ['kernel-release-tracking-bug'],
            'subscribers' :
                ["sru-verification", "ubuntu-sru", "hardware-certification"],
            'invalidate_tasks' : {
                'certification-testing' : [ '2.6.24' ]
                }
            },
        'linux-ec2' :  {
            'task_assignment' : {
                'prepare-package'            : 'stefan-bader-canonical',
                #'prepare-package-lbm'        : 'canonical-kernel-team',
                #'prepare-package-lrm'        : 'canonical-kernel-team',
                #'prepare-package-lum'        : 'canonical-kernel-team',
                'prepare-package-meta'       : 'canonical-kernel-team',
                #'prepare-package-ports-meta' : 'canonical-kernel-team',
                'upload-to-ppa'              : 'canonical-kernel-team',
                'promote-to-proposed'        : 'ubuntu-sru',
                'verification-testing'       : 'canonical-kernel-team',
                #'certification-testing'      : 'canonical-hw-cert',
                'regression-testing'         : 'canonical-platform-qa',
                'promote-to-updates'         : 'ubuntu-sru',
                'promote-to-security'        : 'ubuntu-sru',
                'security-signoff'           : 'canonical-security'
                },
            'initial_bug_tags' :
                ['kernel-release-tracking-bug'],
            'subscribers' :
                ["sru-verification", "ubuntu-sru", "hardware-certification"]
            },
        'linux-mvl-dove' :  {
            'task_assignment' : {
                'prepare-package'            : 'ubuntu-armel-kernel',
                #'prepare-package-lbm'        : 'canonical-kernel-team',
                #'prepare-package-lrm'        : 'canonical-kernel-team',
                #'prepare-package-lum'        : 'canonical-kernel-team',
                'prepare-package-meta'       : 'canonical-kernel-team',
                #'prepare-package-ports-meta' : 'canonical-kernel-team',
                'upload-to-ppa'              : 'canonical-kernel-team',
                'promote-to-proposed'        : 'ubuntu-sru',
                'verification-testing'       : 'ubuntu-armel-kernel',
                #'certification-testing    ' : 'ubuntu-armel-qa',
                'regression-testing'         : 'ubuntu-armel-qa',
                'promote-to-updates'         : 'ubuntu-sru',
                'promote-to-security'        : 'ubuntu-sru',
                'security-signoff'           : 'canonical-security'
                },
            'initial_bug_tags' :
                ['kernel-release-tracking-bug', 'armel'],
            'subscribers' :
                ["sru-verification", "ubuntu-sru", "ubuntu-armel-qa"]
            },
        'linux-fsl-imx51' :  {
            'task_assignment' : {
                'prepare-package'            : 'ubuntu-armel-kernel',
                #'prepare-package-lbm'        : 'canonical-kernel-team',
                #'prepare-package-lrm'        : 'canonical-kernel-team',
                #'prepare-package-lum'        : 'canonical-kernel-team',
                'prepare-package-meta'       : 'canonical-kernel-team',
                #'prepare-package-ports-meta' : 'canonical-kernel-team',
                'upload-to-ppa'              : 'canonical-kernel-team',
                'promote-to-proposed'        : 'ubuntu-sru',
                'verification-testing'       : 'ubuntu-armel-kernel',
                #'certification-testing'     : 'ubuntu-armel-qa',
                'regression-testing'         : 'ubuntu-armel-qa',
                'promote-to-updates'         : 'ubuntu-sru',
                'promote-to-security'        : 'ubuntu-sru',
                'security-signoff'           : 'canonical-security'
                },
            'initial_bug_tags' :
                ['kernel-release-tracking-bug', 'armel'],
            'subscribers' :
                ["sru-verification", "ubuntu-sru", "ubuntu-armel-qa"]
            },
        'linux-ti-omap4' :  {
            'task_assignment' : {
                'prepare-package'            : 'ubuntu-armel-kernel',
                #'prepare-package-lbm'        : 'canonical-kernel-team',
                #'prepare-package-lrm'        : 'canonical-kernel-team',
                #'prepare-package-lum'        : 'canonical-kernel-team',
                'prepare-package-meta'       : 'canonical-kernel-team',
                #'prepare-package-ports-meta' : 'canonical-kernel-team',
                'upload-to-ppa'              : 'canonical-kernel-team',
                'promote-to-proposed'        : 'ubuntu-sru',
                'verification-testing'       : 'ubuntu-armel-kernel',
                #'certification-testing'     : 'ubuntu-armel-qa',
                'regression-testing'         : 'ubuntu-armel-qa',
                'promote-to-updates'         : 'ubuntu-sru',
                'promote-to-security'        : 'ubuntu-sru',
                'security-signoff'           : 'canonical-security'
                },
            'initial_bug_tags' :
                ['kernel-release-tracking-bug', 'armel'],
            'subscribers' :
                ["sru-verification", "ubuntu-sru", "ubuntu-armel-qa"]
            },
        'linux-lts-backport-oneiric' :  {
            'task_assignment' : {
                'prepare-package'            : 'canonical-kernel-team',
                #'prepare-package-lbm'        : 'canonical-kernel-team',
                #'prepare-package-lrm'        : 'canonical-kernel-team',
                #'prepare-package-lum'        : 'canonical-kernel-team',
                'prepare-package-meta'       : 'canonical-kernel-team',
                #'prepare-package-ports-meta' : 'canonical-kernel-team',
                #'upload-to-ppa'              : 'canonical-kernel-team',
                'promote-to-proposed'        : 'ubuntu-sru',
                'verification-testing'       : 'canonical-kernel-team',
                #'certification-testing'     : 'canonical-hw-cert',
                'regression-testing'         : 'canonical-platform-qa',
                'promote-to-updates'         : 'ubuntu-sru',
                'promote-to-security'        : 'ubuntu-sru',
                'security-signoff'           : 'canonical-security'
                },
            'initial_bug_tags' :
                ['kernel-release-tracking-bug'],
            'subscribers' :
                ["sru-verification", "ubuntu-sru"],
            },
        'linux-lts-backport-oneiric' :  {
            'task_assignment' : {
                'prepare-package'            : 'canonical-kernel-team',
                #'prepare-package-lbm'        : 'canonical-kernel-team',
                #'prepare-package-lrm'        : 'canonical-kernel-team',
                #'prepare-package-lum'        : 'canonical-kernel-team',
                'prepare-package-meta'       : 'canonical-kernel-team',
                #'prepare-package-ports-meta' : 'canonical-kernel-team',
                #'upload-to-ppa'              : 'canonical-kernel-team',
                'promote-to-proposed'        : 'ubuntu-sru',
                'verification-testing'       : 'canonical-kernel-team',
                #'certification-testing'     : 'canonical-hw-cert',
                'regression-testing'         : 'canonical-platform-qa',
                'promote-to-updates'         : 'ubuntu-sru',
                'promote-to-security'        : 'ubuntu-sru',
                'security-signoff'           : 'canonical-security'
                },
            'initial_bug_tags' :
                ['kernel-release-tracking-bug'],
            'subscribers' :
                ["sru-verification", "ubuntu-sru"],
            },
        'linux-lts-backport-natty' :  {
            'task_assignment' : {
                'prepare-package'            : 'canonical-kernel-team',
                #'prepare-package-lbm'        : 'canonical-kernel-team',
                #'prepare-package-lrm'        : 'canonical-kernel-team',
                #'prepare-package-lum'        : 'canonical-kernel-team',
                'prepare-package-meta'       : 'canonical-kernel-team',
                #'prepare-package-ports-meta' : 'canonical-kernel-team',
                #'upload-to-ppa'              : 'canonical-kernel-team',
                'promote-to-proposed'        : 'ubuntu-sru',
                'verification-testing'       : 'canonical-kernel-team',
                #'certification-testing'     : 'canonical-hw-cert',
                'regression-testing'         : 'canonical-platform-qa',
                'promote-to-updates'         : 'ubuntu-sru',
                'promote-to-security'        : 'ubuntu-sru',
                'security-signoff'           : 'canonical-security'
                },
            'initial_bug_tags' :
                ['kernel-release-tracking-bug'],
            'subscribers' :
                ["sru-verification", "ubuntu-sru"],
            },
        'linux-lts-backport-maverick' :  {
            'task_assignment' : {
                'prepare-package'            : 'canonical-kernel-team',
                #'prepare-package-lbm'        : 'canonical-kernel-team',
                #'prepare-package-lrm'        : 'canonical-kernel-team',
                #'prepare-package-lum'        : 'canonical-kernel-team',
                'prepare-package-meta'       : 'canonical-kernel-team',
                #'prepare-package-ports-meta' : 'canonical-kernel-team',
                #'upload-to-ppa'              : 'canonical-kernel-team',
                'promote-to-proposed'        : 'ubuntu-sru',
                'verification-testing'       : 'canonical-kernel-team',
                #'certification-testing'     : 'canonical-hw-cert',
                'regression-testing'         : 'canonical-platform-qa',
                'promote-to-updates'         : 'ubuntu-sru',
                'promote-to-security'        : 'ubuntu-sru',
                'security-signoff'           : 'canonical-security'
                },
            'initial_bug_tags' :
                ['kernel-release-tracking-bug'],
            'subscribers' :
                ["sru-verification", "ubuntu-sru"],
            },
        'default' :  {
            'task_assignment' : {
                'prepare-package'            : 'canonical-kernel-team',
                'prepare-package-lbm'        : 'canonical-kernel-team',
                'prepare-package-lrm'        : 'canonical-kernel-team',
                'prepare-package-lum'        : 'canonical-kernel-team',
                'prepare-package-meta'       : 'canonical-kernel-team',
                'prepare-package-ports-meta' : 'canonical-kernel-team',
                #'upload-to-ppa'              : 'canonical-kernel-team',
                'promote-to-proposed'        : 'ubuntu-sru',
                'verification-testing'       : 'canonical-kernel-team',
                'certification-testing'      : 'canonical-hw-cert',
                'regression-testing'         : 'canonical-platform-qa',
                'promote-to-updates'         : 'ubuntu-sru',
                'promote-to-security'        : 'ubuntu-sru',
                'security-signoff'           : 'canonical-security'
                },
            'initial_bug_tags' :
                ['kernel-release-tracking-bug'],
            'subscribers' :
                ["sru-verification", "ubuntu-sru", "hardware-certification"]
            }
        }

    # assignee
    #
    def assignee(self, packagename, taskname):
        """
        Using the given package name and task name, return the launchpad
        team or person who should be assigned that task. If the
        package name is not in the dictionary, return the default
        """
        if packagename in self.tdb:
            if taskname in self.tdb[packagename]['task_assignment']:
                return self.tdb[packagename]['task_assignment'][taskname]
            else:
                return None
        else:
                return self.tdb['default']['task_assignment'][taskname]

    # initial_tags
    #
    def initial_tags(self, packagename):
        """
        Lookup the given package name and return the tags which
        should be initially applied to the tracking bug
        """
        if packagename in self.tdb:
                return self.tdb[packagename]['initial_bug_tags']
        else:
                return self.tdb['default']['initial_bug_tags']

    # subscribers
    #
    def subscribers(self, packagename):
        """
        Lookup the given package name and return a list of
        teams who should be initially subscribed to the tracking bug
        """
        if packagename in self.tdb:
                return self.tdb[packagename]['subscribers']
        else:
                return self.tdb['default']['subscribers']

    # is task invalid for that series version
    #
    def is_task_invalid(self, packagename, taskname, version):
        """
        Return if the task is invalid for that package version
        """
        if not packagename in self.tdb:
            return False
        if not 'invalidate_tasks' in self.tdb[packagename]:
            return False
        if not taskname in self.tdb[packagename]['invalidate_tasks']:
            return False
        version_list = self.tdb[packagename]['invalidate_tasks'][taskname]
        return (version in version_list)

if __name__ == '__main__':
    workflow = Workflow()
    db = workflow.tdb

    #for record in db:
    #    print db[record]

    print(workflow.assignee('linux', 'prepare-package'))
    print(workflow.assignee('linux', 'nonexistent-task'))
    print(workflow.initial_tags('linux-ti-omap4'))
    print(workflow.subscribers('linux-ti-omap4'))

# vi:set ts=4 sw=4 expandtab:
