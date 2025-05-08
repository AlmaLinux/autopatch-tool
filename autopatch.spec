# %{name} is a metapackage that will install all subpackages
# %{name}-core provides the base functionality
# other feature sets are split out to separate sub packages
Name:           autopatch
Version:        1.0.0
Release:        1%{?dist}
Summary:        Tool for autopatching source content for debranding/modification
License:        GPLv3+
URL:            https://github.com/almalinux/autopatch-tool
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
Requires:       %{name}-core = %{version}-%{release}
Requires:       %{name}-git = %{version}-%{release}
Requires:       %{name}-slack = %{version}-%{release}
Requires:       %{name}-web = %{version}-%{release}
Requires:       %{name}-ansible = %{version}-%{release}

%description
A tool to automatically patch upstream content for use downstream

%prep
%autosetup -n %{name}-%{version}

%build
%py3_build

%install
%py3_install

# Ansible stuff
mkdir -p %{buildroot}%{_datadir}/ansible/%{name}
cp -r ansible/* %{buildroot}%{_datadir}/ansible/%{name}/

# Empty file list for the %{name} metapackage, but we still need to define it
%files

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


%package git
Summary:        Git module for the autopatch tool
Requires:       %{name}-core = %{version}-%{release}
Requires:       python3
Requires:       python3-requests
Requires:       git
# python3-immudb-wrapper needs to be packaged (as well as the upstream python3-immudb)
Requires:       python3-immudb-wrapper

%description git
Git support for the autopatch tool

%files git
%{python3_sitelib}/%{name}/tools/git.py
%{python3_sitelib}/%{name}/tools/__pycache__/git.cpython*.pyc
%{python3_sitelib}/%{name}/debranding.py
%{python3_sitelib}/%{name}/__pycache__/debranding.cpython*.pyc
%{python3_sitelib}/package_patching.py
%{python3_sitelib}/__pycache__/package_patching.cpython*
%{_bindir}/autopatch_package_patching

%package slack
Summary:        Slack module for the autopatch tool
Requires:       %{name}-core = %{version}-%{release}
Requires:       python3
# python3-slackclient exists in Fedora, but not currently in EPEL9
Requires:       python3-slackclient

%description slack
Slack notification module for the autopatch tool

%files slack
%{python3_sitelib}/%{name}/tools/slack.py
%{python3_sitelib}/%{name}/tools/__pycache__/slack.cpython*.pyc

%package web
Summary:        Web interface for the autopatch tool
Requires:       %{name}-core = %{version}-%{release}
Requires:       python3
Requires:       python3-flask
Requires:       python3-werkzeug

%description web
Web interface for the autopatch tool

%files web
%{python3_sitelib}/%{name}/webserv.py
%{python3_sitelib}/%{name}/tools/webserv_tools.py
%{python3_sitelib}/%{name}/tools/__pycache__/webserv_tools.cpython*.pyc
%{python3_sitelib}/%{name}/__pycache__/webserv.cpython*.pyc

%package ansible
Summary: Ansible playbooks for %{name}
Requires: %{name}-core = %{version}-%{release}
Requires: ansible-core

%description ansible
Ansible playbooks for automating %{name} deployment and configuration

%files ansible
%{_datadir}/ansible/autopatch/

%changelog
* Wed May 07 2025 Ben Morrice <ben.morrice@cern.ch> - 1.0.0-1
- initial release
- code is split out through subpackages (a metapackage is also provided)
- autopatch_standalone.py provided as %{bindir}/autopatch
