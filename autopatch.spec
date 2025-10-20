Name:           autopatch
Version:        1.1.2
Release:        1%{?dist}
Summary:        Tool for autopatching source content for debranding/modification
License:        GPLv3+
URL:            https://github.com/almalinux/autopatch-tool
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
Requires:       %{name}-core = %{version}-%{release}
Requires:       git
Requires:       python3-flask
Requires:       python3-immudb_wrapper
Requires:       python3-requests
Requires:       python3-slackclient
Requires:       python3-werkzeug

%description
A tool to automatically patch upstream content for use downstream

%prep
%autosetup -n %{name}-%{version}

%build
%py3_build

%install
%py3_install

%files
# git
%{python3_sitelib}/%{name}/tools/git.py
%{python3_sitelib}/%{name}/tools/__pycache__/git.cpython*.pyc
%{python3_sitelib}/%{name}/debranding.py
%{python3_sitelib}/%{name}/__pycache__/debranding.cpython*.pyc
%{python3_sitelib}/package_patching.py
%{python3_sitelib}/__pycache__/package_patching.cpython*
%{_bindir}/autopatch_package_patching
# slack
%{python3_sitelib}/%{name}/tools/slack.py
%{python3_sitelib}/%{name}/tools/__pycache__/slack.cpython*.pyc
# web
%{python3_sitelib}/%{name}/webserv.py
%{python3_sitelib}/%{name}/tools/webserv_tools.py
%{python3_sitelib}/%{name}/tools/__pycache__/webserv_tools.cpython*.pyc
%{python3_sitelib}/%{name}/__pycache__/webserv.cpython*.pyc

%package core
Summary:        Core components of the autopatch tool
Requires:       python3
Requires:       python3-pyyaml

%description core
Core components of the autopatch tool

%files core
%doc README.md
%license LICENSE
%dir %{python3_sitelib}/%{name}/
%dir %{python3_sitelib}/%{name}/tools/
%{python3_sitelib}/autopatch_standalone.py
%{python3_sitelib}/validate_config.py
%{python3_sitelib}/%{name}/tools/__init__.py
%{python3_sitelib}/%{name}/tools/logger.py
%{python3_sitelib}/%{name}/tools/rpm.py
%{python3_sitelib}/%{name}/tools/tools.py
%{python3_sitelib}/%{name}/actions_handler.py
%{python3_sitelib}/%{name}-%{version}-py*.egg-info/
%{python3_sitelib}/__pycache__/autopatch_standalone.cpython*.pyc
%{python3_sitelib}/__pycache__/validate_config.cpython*.pyc
%{python3_sitelib}/%{name}/tools/__pycache__/__init__.cpython*.pyc
%{python3_sitelib}/%{name}/__pycache__/actions_handler.cpython*.pyc
%{python3_sitelib}/%{name}/tools/__pycache__/logger.cpython*.pyc
%{python3_sitelib}/%{name}/tools/__pycache__/rpm.cpython*.pyc
%{python3_sitelib}/%{name}/tools/__pycache__/tools.cpython*.pyc
%{_bindir}/autopatch
%{_bindir}/autopatch_validate_config

%changelog
* Mon Oct 20 2025 Eduard Abdullin <eabdullin@almalinux.org> - 1.1.2-1
- Fix bug with patch directive in pushd block
- Add indents for the multilines
- Bump version to 1.1.2

* Mon Aug 25 2025 Eduard Abdullin <eabdullin@almalinux.org> - 1.1.1-1
- Add ignore_version_macros and ignore_release_macros parameters
- Raise an error if there is no config for a package

* Thu Aug 14 2025 Eduard Abdullin <eabdullin@almalinux.org> - 1.1.0-1
- Bump version to 1.1.0

* Wed May 07 2025 Ben Morrice <ben.morrice@cern.ch> - 1.0.0-1
- initial release
- autopatch-core subpackage exists for a minimum install
- autopatch_standalone.py provided as %{bindir}/autopatch
