# Dool

Dool is a Python3 compatible fork of [Dstat](https://github.com/dagwieers/dstat).

After Dag Wieers ceased development of Dstat I forked the project to continue
development.

## What is Dool?

Dool is a command line tool to monitor many aspects of your system: CPU,
Memory, Network, Load Average, etc. Dool allows you to monitor many aspects
of your system at the same time. It also includes a robust plug-in architecture
to allow monitoring other system metrics.

### Usage:

    dool [--preset] [--plugin] [delay]

My most common usage of Dool is:

    dool --more 15

which uses the `--more` preset and outputs data every 15 seconds. Available
presets are `--defaults`, `--more`, or `--all`. If no **delay** is specified,
Dool will default to outputting every second.

### Plugins:

Dool ships with many plug-ins to configure output to your taste.

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
