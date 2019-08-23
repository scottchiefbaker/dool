# $Id$
# Authority: Scott Baker
# Upstream: https://github.com/scottchiefbaker/dool

Summary: Pluggable real-time performance monitoring tool
Name: dool
Version: 0.9.9
Release: 1
License: GPL
Group: System Environment/Base
URL: https://github.com/scottchiefbaker/dool

Source: https://github.com/scottchiefbaker/dool/releases/dool-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

BuildArch: noarch
BuildRequires: python >= 2.6
Requires: python >= 2.6 python-six

%description
Dool is a versatile replacement for vmstat, iostat, netstat and ifstat.
Dool overcomes some of their limitations and adds some extra features,
more counters and flexibility. Dool is handy for monitoring systems
during performance tuning tests, benchmarks or troubleshooting.

Dool allows you to view all of your system resources in real-time, you
can eg. compare disk utilization in combination with interrupts from your
IDE controller, or compare the network bandwidth numbers directly
with the disk throughput (in the same interval).

Dool gives you detailed selective information in columns and clearly
indicates in what magnitude and unit the output is displayed. Less
confusion, less mistakes. And most importantly, it makes it very easy
to write plugins to collect your own counters and extend in ways you
never expected.

%prep
%setup

%build

%install
%{__rm} -rf %{buildroot}
%{__make} install DESTDIR="%{buildroot}"

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root, 0755)
%doc AUTHORS ChangeLog COPYING README.md TODO docs/*.html docs/*.adoc examples/
%doc %{_mandir}/man1/dool.1*
%{_bindir}/dool
%{_datadir}/dool/

%changelog
* Fri Aug 23 2019 Scott Baker <scott@perturb.org> - 0.9.9-1
- Updated to release 0.9.9.

* Fri Mar 18 2016 Dag Wieers <dag@wieers.com> - 0.7.3-1
- Updated to release 0.7.3.

* Tue Jun 15 2010 Dag Wieers <dag@wieers.com> - 0.7.2-1
- Updated to release 0.7.2.

* Mon Feb 22 2010 Dag Wieers <dag@wieers.com> - 0.7.1-1
- Updated to release 0.7.1.

* Wed Nov 25 2009 Dag Wieers <dag@wieers.com> - 0.7.0-1
- Updated to release 0.7.0.
- Reduce the number of paths used for importing modules. {CVE-2009-3894}

* Tue Dec 02 2008 Dag Wieers <dag@wieers.com> - 0.6.9-1
- Updated to release 0.6.9.

* Sun Aug 17 2008 Dag Wieers <dag@wieers.com> - 0.6.8-1
- Updated to release 0.6.8.

* Tue Feb 26 2008 Dag Wieers <dag@wieers.com> - 0.6.7-1
- Updated to release 0.6.7.

* Sat Apr 28 2007 Dag Wieers <dag@wieers.com> - 0.6.6-1
- Updated to release 0.6.6.

* Tue Apr 17 2007 Dag Wieers <dag@wieers.com> - 0.6.5-1
- Updated to release 0.6.5.

* Tue Dec 12 2006 Dag Wieers <dag@wieers.com> - 0.6.4-1
- Updated to release 0.6.4.

* Mon Jun 26 2006 Dag Wieers <dag@wieers.com> - 0.6.3-1
- Updated to release 0.6.3.

* Thu Mar 09 2006 Dag Wieers <dag@wieers.com> - 0.6.2-1
- Updated to release 0.6.2.

* Mon Sep 05 2005 Dag Wieers <dag@wieers.com> - 0.6.1-1
- Updated to release 0.6.1.

* Sun May 29 2005 Dag Wieers <dag@wieers.com> - 0.6.0-1
- Updated to release 0.6.0.

* Fri Apr 08 2005 Dag Wieers <dag@wieers.com> - 0.5.10-1
- Updated to release 0.5.10.

* Mon Mar 28 2005 Dag Wieers <dag@wieers.com> - 0.5.9-1
- Updated to release 0.5.9.

* Tue Mar 15 2005 Dag Wieers <dag@wieers.com> - 0.5.8-1
- Updated to release 0.5.8.

* Fri Dec 31 2004 Dag Wieers <dag@wieers.com> - 0.5.7-1
- Updated to release 0.5.7.

* Mon Dec 20 2004 Dag Wieers <dag@wieers.com> - 0.5.6-1
- Updated to release 0.5.6.

* Thu Dec 02 2004 Dag Wieers <dag@wieers.com> - 0.5.5-1
- Updated to release 0.5.5.

* Thu Nov 25 2004 Dag Wieers <dag@wieers.com> - 0.5.4-1
- Updated to release 0.5.4.
- Use dstat15 if distribution uses python 1.5.

* Sun Nov 21 2004 Dag Wieers <dag@wieers.com> - 0.5.3-1
- Updated to release 0.5.3.

* Sat Nov 13 2004 Dag Wieers <dag@wieers.com> - 0.5.2-1
- Updated to release 0.5.2.

* Thu Nov 11 2004 Dag Wieers <dag@wieers.com> - 0.5.1-1
- Updated to release 0.5.1.

* Tue Oct 26 2004 Dag Wieers <dag@wieers.com> - 0.4-1
- Initial package. (using DAR)
