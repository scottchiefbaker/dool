## 🔍 What is Dool?

Dool is a command line tool to monitor many aspects of your Linux system: CPU,
Memory, Network, Load Average, etc.  It also includes a robust plug-in
architecture to allow monitoring other system metrics.

Dool is a Python3 compatible fork of [Dstat](https://github.com/dagwieers/dstat).

### 📦 Installation:

1. Download the [latest release](https://github.com/scottchiefbaker/dool/releases) archive file or clone the Git repo
2. Copy `dool` into your `$PATH`
3. Copy `plugins/*` to `~/.dool/` (optional)

### ✨ Usage:

	dool [--preset] [--plugin] [delay]

My most common usage of Dool is:

	dool --more 15

which uses the `--more` preset and outputs data every 15 seconds. Available
presets are `--defaults`, `--more`, or `--all`. If no **delay** is specified,
Dool will default to outputting every second.

### 🖼️ Screenshots:

Dark mode (default)
![Dool Light](https://user-images.githubusercontent.com/3429760/192394845-bb4790b9-0a67-4137-90a2-87efcfc1014e.png)

Light mode
![Dool Light](https://user-images.githubusercontent.com/3429760/192389235-9cf5e4a5-cec2-42d9-a116-bcd9dd4e688d.png)

### 🔌 Plugins:

Dool ships with many plug-ins to configure the output to your taste.

	dool --cpu --net --time --full # Show CPU usage, and each network interface
	dool --disk -D total,sda,sdd   # Show the total disk IO, and /dev/sda and /dev/sdd
	dool --net -N eth0,eth1        # Show the network traffic for eth0 and eth1

A list of available plug-ins are available when you run `dool --version`

### 🎨 Colors:

Dool expects a 256 color compatible terminal. Most modern terminal emulators
support this automatically. A `--color16` option is available if you only have
a 16 color terminal.

### 📈 Bits vs Bytes:

One of the changes in `dool` is measurement of network and disk bandwidth in
*bits* instead of bytes. This can be confusing if you're used to seeing
lower numbers in `dstat`. If you would rather see bandwidth reported in bytes
you can use the `--bytes` option.

### 🧰 Other tools similar to Dool:

* [htop](https://htop.dev/)
* [btop](https://github.com/aristocratos/btop)
* [iotop](https://github.com/Tomas-M/iotop)

### 🌿 Pull Requests and Branches

The latest stable release (plus bugfixes) will live on the `master` branch.
Development of new features will occur on the `next` branch. Please have
pull requests target the `next` branch.

Various feature/bug branches may come and go as we work on more complex
functionality, but those can be safely ignored.

### 👨 Team

| Username         | Role                    |
| ---------------- | ----------------------- |
| @scottchiefbaker | Primary author          |
| @dagwieers       | Original `dstat` author |
| @raylu           | Pip release manager     |
