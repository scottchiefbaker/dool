# Dool

Dool is a Python3 compatible fork of [Dstat](https://github.com/dagwieers/dstat).

After Dag Wieers ceased development of Dstat I forked the project to continue
development. Dool is a Python 3.x compatible version of Dstat with a couple minor bug fixes.

## What is Dool?

Dool is a command line tool to monitor many aspects of your system: CPU,
Memory, Network, Load Average, etc. Dool allows you to monitor many aspects
of your system at the same time. It also includes a robust plug-in architecture
to allow monitoring other system metrics.

### Usage:

    dool [--preset] [--plugin] [delay]

My most common usage of Dool is:

    dool --more 15

which uses the `--more` preset and outputs data every 15 seconds. Available presets are `--defaults`, `--more`, or `--all`. If no **delay** is specified, Dool will default to outputting every second.

### Plugins:

Dool ships with many plug-ins to configure output to your taste.

    dool --net --cpu --proc 15
    dool --cpu --time 5

A list of available plug-ins are available if you run `dool --version`

### Note:

Dool requires a 256 color compatible terminal. Most modern terminal emulators support this automatically.

### See also:

Other tools similar to Dool

* [htop](https://htop.dev/)
* [btop](https://github.com/aristocratos/btop)
* [iotop](https://github.com/Tomas-M/iotop)
