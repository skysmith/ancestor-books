set appPath to POSIX path of (path to me)
set scriptDir to do shell script ("dirname " & quoted form of appPath)
set launcherPath to scriptDir & "/Launch Image Gen.command"

do shell script ("open " & quoted form of launcherPath)
