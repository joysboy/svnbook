#!/usr/bin/env python
# vim:sw=4

# ----------------------------------------------------------------------
# build-and-deploy.py:  Subversion book (nightly) build script.
#
# Read a configuration file (INI-format) for information about scheduled
# builds of the Subversion book sources -- which versions, which output
# formats, where to drop the results, etc. -- and perform the requisite
# builds.
# ----------------------------------------------------------------------

import sys
import os
import getopt
import shutil
import time
import subprocess
import traceback
import ConfigParser

# ----------------------------------------------------------------------
# The configuration file has a [general] section, then a set of build
# definition sections, each of which describes a build to attempt:
#
#    [general]
#
#    # Destination email address for build reports.
#    report_target =
#
#    # Sender email address for build reports.
#    report_sender =
#
#    # Sender name for build reports.
#    report_sender_name =
#
#
#    [BUILD-NAME1]
#    
#    # Locale code ("en", "de", ...).  Required.
#    locale =
#
#    # Book version number ("1.5", "1.2", ...).  Required.
#    version = BOOK-VERSION
#
#    # Path to the locale version book source directory.  Defaults to
#    # "branches/<version>/<locale>".
#    src_path =
#
#    # Path in which the build deliverables should be dropped.  Defaults
#    # to "www/<locale>/<version>".
#    dst_path = PUBLISH-PATH
#
#    # Comma-delimited list of output formats to use.  Defaults to
#    # "html, html-chunk, pdf".
#    formats = FORMAT1[, FORMAT2 ...]
#
#    # Set to "1" if AdSense code substitution should be applied.  Defaults
#    # to "0".
#    adsense = "0" | "1"
#
#    [BUILD-NAME2]
#    ...
#
# Here's an example of such a file.  Note that the trunk English
# version requires a "src_path", that both English version add AdSense
# stuff, and that the German 1.5 version doesn't generate PDF output.
#
#    [general]
#    report_target = svnbook-dev@red-bean.com
#    report_sender = svnbook-build-daemon@red-bean.com
#    report_sender_name = Svnbook Build Daemon
#
#    [en-trunk]
#    locale = en
#    version = 1.7
#    src_path = trunk/en
#    adsense = 1
#
#    [en-1.6]
#    locale = en
#    version = 1.6
#    adsense = 1
#
#    [de-1.5]
#    locale = de
#    version = 1.5
#    formats = html, html-chunk
# ----------------------------------------------------------------------


def format_duration(seconds):
    """Return a string describing SECONDS as a more pretty-printed
    string describing hours, minutes, and seconds."""

    seconds = int(seconds)
    hours = seconds / 3600
    minutes = seconds % 3600 / 60
    seconds = seconds % 60
    return ((hours and "%dh " % hours or "")
            + (minutes and "%dm " % minutes or "")
            + "%ds" % seconds)


def sendmail(mail_from, mail_from_name, mail_to, subject, body):
    """Open a pipe to the 'sendmail' binary, and use it to transmit an
    email from MAIL_FROM (with name MAIL_FROM_NAME) to MAIL_TO, with
    SUBJECT and BODY."""

    assert mail_from and mail_to and mail_from_name
    try:
        p = subprocess.Popen(['/usr/sbin/sendmail', '-f', mail_from, mail_to],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        p.stdin.write("Subject: %s\n" % subject)
        p.stdin.write("To: %s\n" % mail_to)
        p.stdin.write("From: %s <%s>\n" % (mail_from_name, mail_from))
        p.stdin.write("\n")
        p.stdin.write(body)
        p.stdin.close()
        output = p.stdout.read()
        status = p.wait()
        if len(output) or status:
            sys.stderr.write("MTA output when sending email (%s):\n" % subject)
            sys.stderr.write(output)
            sys.stderr.write("Exit status %d\n" % status)
    except IOError:
        etype, value, tb = sys.exc_info()
        sys.stderr.write("Failed sending email (%s):\n" % subject)
        traceback.print_exception(etype, value, tb)
        sys.stderr.write("\n")
        sys.stderr.write("Email body:\n")
        sys.stderr.write(body)


def do_build(locale, version, src_path, dst_path, formats,
             dry_run=False, verbose=False):

    temp_dir = os.path.join(src_path, '__TEMPINSTALL__')
    
    if verbose:
        print "Build requested:"
        print "   Locale = %s" % (locale)
        print "   Version = %s" % (version)
        print "   Source Path = %s" % (src_path)
        print "   Destination Path = %s" % (dst_path)
        print "   Formats = %s" % (str(formats))
        print "   Temporary Directory = %s" % (temp_dir)
        
    # Extend FORMATS to include relevant archived formats, too.
    if 'html' in formats:
        formats.append('html-arch')
    if 'html-chunk' in formats:
        formats.append('html-chunk-arch')

    # Remove the temporary directory if it already exists.
    if os.path.isdir(temp_dir):
        if verbose:
            print "Erase: %s" % (temp_dir)
        if not dry_run:
            shutil.rmtree(temp_dir)

    # Create the destination directory (and parents) as necessary.
    if not os.path.isdir(dst_path):
        if verbose:
            print "Create (with parents): %s" % (dst_path)
        if not dry_run:
            os.makedirs(dst_path)

    make_cmd = (['make', 'INSTALL_SUBDIR=__TEMPINSTALL__', 'clean', 'valid']
                + map(lambda x: 'install-%s' % x, formats))
    build_log = os.path.join(dst_path, 'nightly-build.log')
    log_fp = open(build_log, 'w', 1)

    # Change to the source directory and fire off 'make'.
    cwd = os.getcwd()
    os.chdir(src_path)
    try:
        if verbose:
            print "Change directory: %s" % (src_path)
        if verbose:
            print "Building: %s" % (' '.join(make_cmd))
        if not dry_run:
            p = subprocess.Popen(make_cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
            while 1:
                data = p.stdout.readline()
                if not data:
                    break
                if verbose:
                    print data.rstrip("\n")
                log_fp.write(data)
            exitcode = p.wait()
            if exitcode:
                raise RuntimeError("make exited with error %d" % exitcode)
    # Regardless of how the build went, change back toour
    # original directory.
    finally:
        log_fp.close()
        if verbose:
            print "Change directory: %s" % (cwd)
        os.chdir(cwd)

    # Move stuff into place, deleting old stuff first.
    build_log = os.path.join(dst_path, 'nightly-build.log')
    temp_build_log = os.path.join(temp_dir, 'nightly-build.log')
    if verbose:
        print "Rename: %s -> %s" % (build_log, temp_build_log)
    if not dry_run:
        os.rename(build_log, temp_build_log)
    if os.path.isdir(dst_path):
        if verbose:
            print "Erase: %s" % (dst_path)
        if not dry_run:
            shutil.rmtree(dst_path)
    if verbose:
        print "Move into place: %s -> %s" % (temp_dir, dst_path)
    if not dry_run:
        os.rename(temp_dir, dst_path)


def get_option(cfg, section, option, default_value=None):
    """Return the value of OPTION in SECTION from CFG.  If there is no
    such option, or its value is empty, return DEFAULT_VALUE
    instead."""
    
    if not cfg.has_option(section, option):
        return default_value
    return cfg.get(section, option) or default_value


def main(conf_file, dry_run, verbose):
    """Read CONF_FILE and attempt the builds described there.  If
    DRY_RUN is set, don't really do anything.  If VERBOSE is set, be
    verbose."""
    
    cfg = ConfigParser.RawConfigParser()
    cfg.read(conf_file)
    build_sections = []
    mail_from = get_option(cfg, 'general', 'report_sender')
    mail_to = get_option(cfg, 'general', 'report_target')
    mail_from = get_option(cfg, 'general', 'report_sender',
                           'SvnBook Build Daemon')
    for section in cfg.sections():
        if section == 'general':
            continue
        build_sections.append(section)

    # Update the working copy
    if verbose:
        print "SVN Update: ."
    if not dry_run:
        if verbose:
            os.system('svn up')
        else:
            os.system('svn up -q')

    # Do the build(s)
    for section in build_sections:
        locale = cfg.get(section, 'locale')
        version = cfg.get(section, 'version')
        src_path = get_option(cfg, section, 'src_path',
                              'branches/%s/%s' % (version, locale))
        dst_path = get_option(cfg, section, 'dst_path',
                              'www/%s/%s' % (locale, version))
        formats = map(lambda x: x.strip(),
                      get_option(cfg, section, 'formats',
                                 'html, html-chunk, pdf').split(','))
        build_log = os.path.join(dst_path, 'nightly-build.log')
        try:
            build_begin_time = time.time()
            do_build(locale, version, src_path, dst_path, formats,
                     dry_run, verbose)
            build_end_time = time.time()
        except Exception, e:
            if dry_run:
                print "Send failure email: %s" % (locale)
            else:
                body = "The svnbook build for the '%s' locale has failed.\n" \
                       "Please investigate.\n\n%s\n" \
                       "-- Svnbook Build Daemon.\n" % (locale, build_log)
                if mail_to and mail_from:
                    sendmail(mail_from, mail_from_name, mail_to,
                             "Build Failure Alert: '%s'" % locale, body)
                else:
                    sys.stderr.write(body)
                    sys.stderr.write(str(e) + "\n")


def usage_and_exit(errmsg=None):
    stream = errmsg and sys.stderr or sys.stdout
    stream.write("""\
Usage: %s [OPTIONS] BUILD-CONF-FILE

Options:

   --help (-h)      Show this usage message and exit.    
   --dry-run (-n)   Don't really do anything.  (Implies --verbose.)
   --verbose (-v)   Be verbose about what's going on.

Read Subversion Book build definitions from BUILD-CONF-FILE and build the
specified distributions.
""" % (os.path.basename(sys.argv[0])))
    if errmsg:
        stream.write("ERROR: %s\n" % (errmsg))
    sys.exit(errmsg and 1 or 0)


if __name__ == "__main__":
    dry_run = False
    verbose = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hnv",
                                   ["help", "dry-run", "verbose"])
    except getopt.GetoptError, e:
        usage_and_exit(str(e))
    for option, value in opts:
        if option in ["-h", "--help"]:
            usage_and_exit()
        elif option in ["-n", "--dry-run"]:
            dry_run = True
        elif option in ["-v", "--verbose"]:
            verbose = True
    if not args:
        usage_and_exit("Not enough arguments.")
    conf_file = args[0]
    if dry_run:
        verbose = True
    main(conf_file, dry_run, verbose)
