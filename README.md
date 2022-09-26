# Dool

Dool is a Python3 compatible fork of [Dstat](https://github.com/dagwieers/dstat).

After Dag Wieers ceased development of Dstat I forked the project to continue
development.

## What is Dool?

Dool is a command line tool to monitor many aspects of your system: CPU,
Memory, Network, Load Average, etc. Dool allows you to monitor many aspects
of your system at the same time. It also includes a robust plug-in architecture
to allow monitoring other system metrics.

### Installation:

Single user:
1. Download the [latest release](https://github.com/scottchiefbaker/dool/releases) archive file
2. Extract the archive to an appropriate directory on your system
3. Create a symlink to the `dool` script in your `$PATH`

System wide (as root):
1. `make install`

### Usage:

    dool [--preset] [--plugin] [delay]

My most common usage of Dool is:

    dool --more 15

which uses the `--more` preset and outputs data every 15 seconds. Available
presets are `--defaults`, `--more`, or `--all`. If no **delay** is specified,
Dool will default to outputting every second.

### Screenshots:

Dark mode (default)
![Dool Light](https://user-images.githubusercontent.com/3429760/192389287-9cce4de1-e190-4a3f-8835-33d7446ae934.png)

Light mode
![Dool Light](https://user-images.githubusercontent.com/3429760/192389235-9cf5e4a5-cec2-42d9-a116-bcd9dd4e688d.png)

### Plugins:

Dool ships with many plug-ins to configure the output to your taste.

    dool --cpu --net --time --ful 15   # Show CPU usage, and each network interface
    dool --disk --memory 5             # Show disk totals, and memory consumption
    dool --cpu --load --swap --time 60 # Show CPU, load, and swap

A list of available plug-ins are available if you run `dool --version`

### Note:

Dool requires a 256 color compatible terminal. Most modern terminal emulators
support this automatically.

### See also:

Other tools similar to Dool

* [htop](https://htop.dev/)
* [btop](https://github.com/aristocratos/btop)
* [iotop](https://github.com/Tomas-M/iotop)

