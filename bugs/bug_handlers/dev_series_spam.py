#!/usr/bin/env python
#

from core.bug_handler                   import BugHandler

from ktl.termcolor                      import colored

class DevSeriesSpammer(BugHandler):
    """
    Add a tag to the given bug. That tag is the name of the series the bug was
    filed against.
    """

    # __init__
    #
    def __init__(self, cfg, lp, vout):
        BugHandler.__init__(self, cfg, lp, vout)

        self.comment = "Thank you for taking the time to file a bug report on this issue.\n\nHowever, given the number of bugs that the Kernel Team receives during any development cycle it is impossible for us to review them all. Therefore, we occasionally resort to using automated bots to request further testing. This is such a request.\n\nWe have noted that there is a newer version of the development kernel currently in the release pocket than the one you tested when this issue was found. Please test again with the newer kernel and indicate in the bug if this issue still exists or not.\n\nIf the bug still exists, change the bug status from Incomplete to <previous-status>. If the bug no longer exists, change the bug status from Incomplete to Fix Released.\n\nThank you for your help.\n"
        self.comment_subject = "Test with newer development kernel (%s)" % self.cfg['released_development_kernel']

    # change_status
    #
    def change_status(self, bug, task, package_name, new_status):
        self.show_buff += colored('%s Status: "%s" -> "%s" ' % (task.bug_target_name, task.status, new_status), 'green')
        task.status = new_status  # Make the status change

    # run
    #
    def run(self, bug, task, package_name):
        retval = True

        current_status = task.status
        comment = self.comment.replace('<previous-status>', task.status)

        self.change_status(bug, task, package_name, "Incomplete")
        bug.add_comment(comment, self.comment_subject)
        bug.tags.append('kernel-request-%s' % self.cfg['released_development_kernel'])

        return retval

# vi:set ts=4 sw=4 expandtab:
