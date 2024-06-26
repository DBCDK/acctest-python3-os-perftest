# acctest-python3-os-perftest

Archived 08/05-2025, Not used by DBC Digital any more

## OS perftest package

Migrated from https://svn.dbc.dk/repos/os-perftest/trunk

When running stand alone the package-name is taken from the current directory name

ie. `acctest-python3-os-perftest` will become `os-perftest-dbc` as the python module and `python3-os-perftest-dbc` as package name

When building using `Jenkinsfile` the `JOB_NAME` is used to determine package name.
And the packages are uploaded for `apt-get install`.

## Configuration

The `PACKAGE.ini` file contains segments (not a real ini file since no key-valye, but only segments)

 * `[version]`
    is the package version number (gets build-number attached)
 *  `[dependencies]`
    debian package names
 * `[description]`
    package title
 * `[long_description]`
    package description

## Directory layout

The directory structure is:

 * `bin/`
  This is where binary programs resides
 * `man/`
  If there's man pages are (if any)
 * `src/`
  Where `.py` modules resides
   * test packages (named `tests`) are not included in the debian package
   * nosetest are run on the `tests` packages before the debian package is built
