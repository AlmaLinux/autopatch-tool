Summary: Builds packages inside chroots
Name: mock
Version: 6.7
Release: 1%{?dist}
License: GPL-2.0-or-later
Source: https://github.com/rpm-software-management/%{name}/releases/download/%{name}-%{version}-1/%{name}-%{version}.tar.gz
URL: https://github.com/rpm-software-management/mock/
BuildArch: noarch
Requires: tar

%description
Mock takes an SRPM and builds it in a chroot.

%prep
%setup -q
for file in py/mock.py py/mock-parse-buildlog.py; do
  sed -i 1"s|#!/usr/bin/python3 |#!%{__python}|" $file
done

%build
%py3_build

%install
%py3_install

%files
%license COPYING
%{_bindir}/mock

%changelog
* Tue Mar 03 2026 Pavel Raiskup <pavel@raiskup.cz> 6.7-1
- mock: Use umask 0022 instead of 0002
