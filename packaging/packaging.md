# Information for packaging maintainers

Packaging Dool for your platform should be very simple. Dool is a single Python script and some _optional_ plugins.

### Prerequisites

* Any recent version of Python 3.x

### Global installation

* The `dool` script should be in the global path. This is usually `/usr/bin/`
* The plugins should be placed in `/usr/share/dool/` (optional)
* The `dool.1` manpage should be placed the appropriate manpage location. This is usually `/usr/share/man/man1`

Plugin installation can be verified by running `dool --list` to show all the plugins that were found and what directories they were found in. If you are having problems packaging the plugins they can be skipped. 90% of the functionality is built in to the core `dool` script.

### Local user installation

* The `dool` script should be in the user's `$PATH`. Usually this is `~/bin/`
* The plugins should be placed in `~/.dool/` (optional)

### Building packages

Dool uses **make** to build packages. In the `packaging/` directory we break out each platform with an associated build script.

* Build a `.tar.gz` file: `make dist`
* Build an RPM for RedHat platforms: `make rpm`
* Build a Debian package: `make deb`
