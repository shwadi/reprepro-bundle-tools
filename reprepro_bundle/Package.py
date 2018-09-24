#!/usr/bin/python3 -Es
# -*- coding: utf-8 -*-
import logging
import apt_pkg
import re
import reprepro_bundle
from reprepro_bundle.PackageStatus import PackageStatus
from reprepro_bundle.PackageExistence import PackageExistence

logger = logging.getLogger(__name__)

class Package:
    '''
        This class describes a source package or binary packages that
        are identified by their source package name and their status.
        This class provides methods for reading and writing single lines
        of the sources_control.list generated by the class Bundle.
    '''
    def __init__(self, sourceName, version, suiteName, section, existanceType, status=PackageStatus.UNKNOWN):
        self.sourceName = sourceName
        self.version = version
        self.suiteName = suiteName
        self.section = section
        self.existanceType = existanceType
        self.status = status
        self.active = False

    def __str__(self):
        return "Package('{}', '{}', '{}', '{}', {}, {})".format(self.sourceName, self.version, self.suiteName, self.section, self.existanceType, self.status)

    def updateStatus(self, current):
        if not current:
            self.status = PackageStatus.IS_MISSING
        elif self == current:
            self.status = PackageStatus.IS_CURRENT
        elif self.version == current.version:
            self.status = PackageStatus.IS_SAME_VERSION
        elif self < current:
            self.status = PackageStatus.IS_DOWNGRADE
        elif self > current:
            self.status = PackageStatus.IS_UPGRADE
        else:
            self.status = PackageStatus.UNKNOWN

    def formatActionString(self):
        (action, prep) = self.status.getAction()
        comment = "# " if not self.active else ""
        return "{:19} {:8} OF {} {} {} {} {}".format(comment + action, str(self.existanceType), self.sourceName, self.version, prep, str(self.suiteName), self.section)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return other and self.status == other.status and self.sourceName == other.sourceName and self.version == other.version and self.suiteName == other.suiteName and self.section == other.section and self.existanceType == other.existanceType

    def __ne__(self, other):
        return not(self == other)

    def __lt__(self, other):
        if not other:
            return False
        if self.status != other.status:
            return self.status < other.status
        elif self.sourceName != other.sourceName:
            return self.sourceName < other.sourceName
        elif self.version != other.version:
            return apt_pkg.version_compare(self.version, other.version) < 0
        elif self.suiteName != other.suiteName:
            return self.suiteName < other.suiteName
        elif self.section != other.section:
            return self.section < other.section
        elif self.existanceType != other.existanceType:
            return self.existanceType < other.existanceType
        return False

    @staticmethod
    def getByQueryResults(source, binaries):
        peType = PackageExistence.MISSING
        res = None
        if source and binaries:
            (peType, res) = (PackageExistence.SRCBIN, source)
        elif source and not binaries:
            (peType, res) = (PackageExistence.SOURCE, source)
        elif not source and binaries:
            (peType, res) = (PackageExistence.BIN, binaries)
        if res:
            (sourceName, version, suite, section) = res.getData()
            return Package(sourceName, version, suite.getSuiteName(), section, peType)
        return None

    @staticmethod
    def getByActionString(line):
        line = re.sub(" +", " ", line)
        if(len(line.split(" ")) != 8):
            logger.warn("illegal format in line: {}".format(line))
            return None
        (action, what, _, sourceName, version, _, suite, section) = line.split(" ")
        peType = PackageExistence.getByStr(what)
        status = PackageStatus.getByAction(action)
        return Package(sourceName, version, suite, section, peType, status)
