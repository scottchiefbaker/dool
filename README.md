# Dool

Dool is a Python3 compatible fork of [Dstat](https://github.com/dagwieers/dstat).

After Dag Wieers ceased development of Dstat I forked the project to continue
development.

## What is Dool?

Dool is a command line tool to monitor many aspects of your system: CPU,
Memory, Network, Load Average, etc.  It also includes a robust plug-in
architecture to allow monitoring other system metrics.

### Installation:

1. Download the [latest release](https://github.com/scottchiefbaker/dool/releases) archive file or clone the Git repo
2. Extract the archive to an appropriate temporary directory on your system
3. Run the `install.py` script

### Usage:

    dool [--preset] [--plugin] [delay]

My most common usage of Dool is:

    dool --more 15

which uses the `--more` preset and outputs data every 15 seconds. Available
presets are `--defaults`, `--more`, or `--all`. If no **delay** is specified,
Dool will default to outputting every second.

### Screenshots:

Dark mode (default)
![Dool Light](https://user-images.githubusercontent.com/3429760/192394845-bb4790b9-0a67-4137-90a2-87efcfc1014e.png)

Light mode
![Dool Light](https://user-images.githubusercontent.com/3429760/192389235-9cf5e4a5-cec2-42d9-a116-bcd9dd4e688d.png)

### Plugins:

Dool ships with many plug-ins to configure the output to your taste.

    dool --cpu --net --time --full # Show CPU usage, and each network interface
	dool --disk -D total,sda,sdd   # Show the total disk IO, and /dev/sda and /dev/sdd
    dool --net -N eth0,eth1        # Show the network traffic for eth0 and eth1

A list of available plug-ins are available if you run `dool --version`

### Note:

Dool requires a 256 color compatible terminal. Most modern terminal emulators
support this automatically.

### See also:

Other tools similar to Dool

* [htop](https://htop.dev/)
* [btop](https://github.com/aristocratos/btop)
* [iotop](https://github.com/Tomas-M/iotop)

### Pull Requests and Branches

The latest stable release (plus bugfixes) will live on the `master` branch,
and development of new features will occur on the `next` branch. Please have
pull requests target the `next` branch.

Various feature/bug branches may come and go as we work on more complex
functionality, but those can be safely ignored.
