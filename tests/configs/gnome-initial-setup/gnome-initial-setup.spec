%define autorelease(e:s:pb:n) %{?-p:0.}%{lua:
    release_number = 15;
    base_release_number = tonumber(rpm.expand("%{?-b*}%{!?-b:1}"));
    print(release_number + base_release_number - 1);
}%{?-e:.%{-e*}}%{?-s:.%{-s*}}%{!?-n:%{?dist}}
## END: Set by rpmautospec

%global nm_version 1.2
%global nma_version 1.0
%global glib_required_version 2.63.1
%global gtk_required_version 4.6
%global geoclue_version 2.3.1
%global gnome_desktop_version 44.0-7

%global tarball_version %%(echo %{version} | tr '~' '.')

%if 0%{?rhel}
%bcond_with webkitgtk
%else
%bcond_without webkitgtk
%endif

Name:           gnome-initial-setup
Version:        46.alpha
Release:        %autorelease
Summary:        Bootstrapping your OS

License:        GPL-2.0-or-later
URL:            https://wiki.gnome.org/Design/OS/InitialSetup
Source0:        https://download.gnome.org/sources/%{name}/46/%{name}-%{tarball_version}.tar.xz
Source1:        vendor.conf

# https://gitlab.gnome.org/GNOME/gnome-initial-setup/-/merge_requests/200
Patch: live-user-mode.patch
# Downstream branding
Patch: 0001-RHEL10-style-illustrations.patch

BuildRequires:  desktop-file-utils
BuildRequires:  gcc
BuildRequires:  meson
BuildRequires:  pkgconfig(accountsservice)
BuildRequires:  pkgconfig(fontconfig)
BuildRequires:  pkgconfig(gdm)
BuildRequires:  pkgconfig(geocode-glib-2.0)
BuildRequires:  pkgconfig(gio-2.0) >= %{glib_required_version}
BuildRequires:  pkgconfig(gio-unix-2.0) >= %{glib_required_version}
BuildRequires:  pkgconfig(glib-2.0) >= %{glib_required_version}
BuildRequires:  pkgconfig(gnome-desktop-4)
BuildRequires:  pkgconfig(gsettings-desktop-schemas)
BuildRequires:  pkgconfig(gstreamer-1.0)
BuildRequires:  pkgconfig(gtk4) >= %{gtk_required_version}
BuildRequires:  pkgconfig(gweather4)
BuildRequires:  pkgconfig(ibus-1.0)
BuildRequires:  pkgconfig(iso-codes)
BuildRequires:  pkgconfig(json-glib-1.0)
BuildRequires:  pkgconfig(krb5)
BuildRequires:  pkgconfig(libadwaita-1)
BuildRequires:  pkgconfig(libgeoclue-2.0) >= %{geoclue_version}
BuildRequires:  pkgconfig(libnma-gtk4) >= %{nma_version}
BuildRequires:  pkgconfig(libnm) >= %{nm_version}
BuildRequires:  pkgconfig(libsecret-1)
BuildRequires:  pkgconfig(packagekit-glib2)
BuildRequires:  pkgconfig(pango)
BuildRequires:  pkgconfig(polkit-gobject-1)
BuildRequires:  pkgconfig(pwquality)
BuildRequires:  pkgconfig(rest-1.0)
%if %{with webkitgtk}
BuildRequires:  pkgconfig(webkitgtk-6.0)
%endif

# gnome-initial-setup is being run by gdm
Requires: gdm
Requires: geoclue2-libs%{?_isa} >= %{geoclue_version}
Requires: glib2%{?_isa} >= %{glib_required_version}
Requires: gnome-desktop4%{?_isa} >= %{gnome_desktop_version}
# we install a rules file
Requires: polkit-js-engine
Requires: /usr/bin/tecla

Requires(pre): shadow-utils

Provides: user(%name)

# https://fedoraproject.org/wiki/Changes/EncourageI686LeafRemoval
ExcludeArch: %{ix86}

%description
GNOME Initial Setup is an alternative to firstboot, providing
a good setup experience to welcome you to your system, and walks
you through configuring it. It is integrated with gdm.

%prep
%autosetup -p1 -n %{name}-%{tarball_version}

%build
%meson \
  -Dparental_controls=disabled \
%if !%{with webkitgtk}
  -Dwebkitgtk=disabled \
%endif
  %{nil}
%meson_build

%install
%meson_install

desktop-file-validate %{buildroot}%{_sysconfdir}/xdg/autostart/gnome-initial-setup-copy-worker.desktop
desktop-file-validate %{buildroot}%{_datadir}/applications/gnome-initial-setup.desktop

mkdir -p %{buildroot}%{_datadir}/gnome-initial-setup
cp %{SOURCE1} %{buildroot}%{_datadir}/gnome-initial-setup/

%find_lang %{name}

%pre
# we do not use sysusers yet because we need /var/lib/gnome-initial-setup
# to be owned by the gnome-initial-setup user. please do not convert
# to sysusers without making sure this is handled, maybe by tmpfiles
useradd -rM -d /run/gnome-initial-setup/ -s /sbin/nologin %{name} &>/dev/null || :

%files -f %{name}.lang
%license COPYING
%doc NEWS README.md
%attr(-, gnome-initial-setup, gnome-initial-setup) %dir %{_localstatedir}/lib/gnome-initial-setup
%ghost %{_localstatedir}/gnome-initial-setup/state
%{_libexecdir}/gnome-initial-setup
%{_libexecdir}/gnome-initial-setup-copy-worker
%{_sysconfdir}/xdg/autostart/gnome-initial-setup-copy-worker.desktop
%{_sysconfdir}/xdg/autostart/gnome-initial-setup-first-login.desktop
%{_datadir}/applications/gnome-initial-setup.desktop
%{_datadir}/dconf/profile/gnome-initial-setup
%dir %{_datadir}/gnome-initial-setup
%{_datadir}/gnome-initial-setup/initial-setup-dconf-defaults
%{_datadir}/gnome-initial-setup/vendor.conf
%{_datadir}/gnome-session/sessions/gnome-initial-setup.session
%{_datadir}/gnome-shell/modes/initial-setup.json
%{_datadir}/polkit-1/rules.d/20-gnome-initial-setup.rules
%{_sysusersdir}/gnome-initial-setup.conf
%{_userunitdir}/*

%changelog
%autochangelog
