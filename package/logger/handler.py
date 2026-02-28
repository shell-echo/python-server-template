import os
import time
from logging.handlers import TimedRotatingFileHandler as TRFH
from typing import Self


class TimedRotatingFileHandler(TRFH):
    def doRollover(self: Self) -> None:
        # super().doRollover()
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.
        """
        # get the time that this sequence started at and make it a TimeTuple
        currentTime = int(time.time())
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            dstNow = time.localtime(currentTime)[-1]
            dstThen = timeTuple[-1]
            if dstNow != dstThen:
                if dstNow:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time.localtime(t + addend)
        baseFilename = self.baseFilename[:-4] if self.baseFilename.endswith(".log") else self.baseFilename
        dfn = self.rotation_filename(baseFilename + "." + time.strftime(self.suffix, timeTuple) + ".log")
        if os.path.exists(dfn):
            # Already rolled over.
            return

        if self.stream:
            self.stream.close()
            self.stream = None  # type: ignore
        self.rotate(self.baseFilename, dfn)
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        if not self.delay:
            self.stream = self._open()
        self.rolloverAt = self.computeRollover(currentTime)
