Name: redhat-release
Version: 1.0
Release: 1%{?dist}
Summary: Test package for line deletion matching
License: GPLv3+
Source0: %{name}-%{version}.tar.gz

%description
This is a test package for testing specific line deletion

%prep
%setup -q -n redhat-release-%{base_release_version} -T -D -a 4
%setup -q -n redhat-release-%{base_release_version} -T -D -a 400

%build

%install

%files

%changelog
* Mon May 09 2025 Ben Morrice <ben.morrice@cern.ch> - 1.0-1
- Initial package
