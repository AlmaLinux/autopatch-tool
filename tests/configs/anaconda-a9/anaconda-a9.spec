Summary: Graphical system installer
Name:    anaconda
Version: 34.25.5.9
Release: 1%{?dist}
License: GPLv2+ and MIT
URL:     http://fedoraproject.org/wiki/Anaconda

# To generate Source0 do:
# git clone https://github.com/rhinstaller/anaconda
# git checkout -b archive-branch anaconda-%%{version}-%%{release}
# ./autogen.sh
# make dist
Source0: https://github.com/rhinstaller/%{name}/releases/download/%{name}-%{version}/%{name}-%{version}.tar.bz2

# Versions of required components (done so we make sure the buildrequires
# match the requires versions of things).

%if ! 0%{?rhel}
%define blivetguiver 2.1.12-1
%endif
%define dasbusver 1.3
%define dbusver 1.2.3
%define dnfver 3.6.0
%define dracutver 034-7
%define fcoeutilsver 1.0.12-3.20100323git
%define gettextver 0.19.8
%define gtk3ver 3.22.17
%define helpver 9.0.0-1
%define isomd5sumver 1.0.10
%define langtablever 0.0.54
%define libarchivever 3.0.4
%define libblockdevver 2.1
%define libreportanacondaver 2.0.21-1
%define libtimezonemapver 0.4.1-2
%define libxklavierver 5.4
%define mehver 0.23-1
%define nmver 1.0
%define pykickstartver 3.32.11-1
%define pypartedver 2.5-2
%define pythonblivetver 1:3.6.0-13
%define rpmver 4.10.0
%define simplelinever 1.8.3-1
%define subscriptionmanagerver 1.29.31
%define utillinuxver 2.15.1
%define rpmostreever 2023.2

BuildRequires: audit-libs-devel
BuildRequires: libtool
BuildRequires: gettext-devel >= %{gettextver}
BuildRequires: gtk3-devel >= %{gtk3ver}
BuildRequires: gtk-doc
BuildRequires: gtk3-devel-docs >= %{gtk3ver}
BuildRequires: glib2-doc
BuildRequires: gobject-introspection-devel
BuildRequires: glade-devel
BuildRequires: libgnomekbd-devel
BuildRequires: libxklavier-devel >= %{libxklavierver}
BuildRequires: make
BuildRequires: pango-devel
BuildRequires: python3-devel
BuildRequires: systemd
# rpm and libarchive are needed for driver disk handling
BuildRequires: rpm-devel >= %{rpmver}
BuildRequires: libarchive-devel >= %{libarchivever}
%ifarch s390 s390x
BuildRequires: s390utils-devel
%endif
BuildRequires: libtimezonemap-devel >= %{libtimezonemapver}

# Tools used by the widgets resource bundle generation
BuildRequires: gdk-pixbuf2-devel
BuildRequires: libxml2

Requires: anaconda-gui = %{version}-%{release}
Requires: anaconda-tui = %{version}-%{release}

%description
The anaconda package is a metapackage for the Anaconda installer.

%package core
Summary: Core of the Anaconda installer
Requires: python3-libs
Requires: python3-dnf >= %{dnfver}
Requires: python3-blivet >= %{pythonblivetver}
Requires: python3-blockdev >= %{libblockdevver}
Requires: python3-meh >= %{mehver}
Requires: libreport-anaconda >= %{libreportanacondaver}
Requires: libselinux-python3
Requires: python3-rpm >= %{rpmver}
Requires: python3-pyparted >= %{pypartedver}
Requires: python3-requests
Requires: python3-requests-file
Requires: python3-requests-ftp
Requires: python3-kickstart >= %{pykickstartver}
Requires: python3-langtable >= %{langtablever}
Requires: util-linux >= %{utillinuxver}
Requires: python3-gobject-base
Requires: python3-dbus
Requires: python3-pwquality
Requires: python3-systemd
Requires: python3-productmd
Requires: python3-dasbus >= %{dasbusver}
Requires: flatpak-libs
# dependencies for rpm-ostree payload module
Requires: rpm-ostree >= %{rpmostreever}
Requires: ostree
# used by ostree command for native containers
Requires: skopeo
%if %{defined rhel} && %{undefined centos}
Requires: subscription-manager >= %{subscriptionmanagerver}
%endif

# pwquality only "recommends" the dictionaries it needs to do anything useful,
# which is apparently great for containers but unhelpful for the rest of us
Requires: cracklib-dicts

Requires: python3-pytz
Requires: teamd
%ifarch s390 s390x
Requires: openssh
%endif
Requires: NetworkManager >= %{nmver}
Requires: NetworkManager-libnm >= %{nmver}
Requires: NetworkManager-team
Requires: kbd
Requires: chrony
Requires: systemd
Requires: python3-pid

# Required by the systemd service anaconda-fips.
Requires: crypto-policies
Requires: /usr/bin/update-crypto-policies

# required because of the rescue mode and VNC question
Requires: anaconda-tui = %{version}-%{release}

# Make sure we get the en locale one way or another
Requires: (glibc-langpack-en or glibc-all-langpacks)

# anaconda literally runs its own dbus-daemon, so it needs this,
# even though the distro default is dbus-broker in F30+
Requires: dbus-daemon

# Ensure it's not possible for a version of grubby to be installed
# that doesn't work with btrfs subvolumes correctly...
Conflicts: grubby < 8.40-10

Obsoletes: anaconda-images <= 10
Provides: anaconda-images = %{version}-%{release}
Obsoletes: anaconda-runtime < %{version}-%{release}
Provides: anaconda-runtime = %{version}-%{release}
Obsoletes: booty <= 0.107-1

%description core
The anaconda-core package contains the program which was used to install your
system.

%package live
Summary: Live installation specific files and dependencies
BuildRequires: desktop-file-utils
# live installation currently implies a graphical installation
Requires: anaconda-gui = %{version}-%{release}
Requires: usermode
Requires: zenity

%description live
The anaconda-live package contains scripts, data and dependencies required
for live installations.

%package install-env-deps
Summary: Installation environment specific dependencies
Requires: udisks2-iscsi
Requires: libblockdev-plugins-all >= %{libblockdevver}
# active directory/freeipa join support
Requires: realmd
Requires: isomd5sum >= %{isomd5sumver}
%ifarch %{ix86} x86_64
Recommends: fcoe-utils >= %{fcoeutilsver}
%endif
# likely HFS+ resize support
%ifarch %{ix86} x86_64
%if ! 0%{?rhel}
Requires: hfsplus-tools
%endif
%endif
# kexec support
Requires: kexec-tools
# needed for proper driver disk support - if RPMs must be installed, a repo is needed
Requires: createrepo_c
# run's on TTY1 in install env
Requires: tmux
# install time crash handling
Requires: gdb
# support for installation from image and live & live image installations
Requires: rsync
# External tooling for managing NVMe-FC devices in the installation environment
Recommends: nvme-cli

%description install-env-deps
The anaconda-install-env-deps metapackage lists all installation environment dependencies.
This makes it possible for packages (such as Initial Setup) to depend on the main Anaconda package without
pulling in all the install time dependencies as well.

%package install-img-deps
Summary: Installation image specific dependencies
# This package must have no weak dependencies.
Requires: udisks2-iscsi
Requires: libblockdev-plugins-all >= %{libblockdevver}
# active directory/freeipa join support
Requires: realmd
Requires: isomd5sum >= %{isomd5sumver}
%ifarch %{ix86} x86_64
Requires: fcoe-utils >= %{fcoeutilsver}
%endif
# likely HFS+ resize support
%ifarch %{ix86} x86_64
%if ! 0%{?rhel}
Requires: hfsplus-tools
%endif
%endif
# kexec support
Requires: kexec-tools
# needed for proper driver disk support - if RPMs must be installed, a repo is needed
Requires: createrepo_c
# run's on TTY1 in install env
Requires: tmux
# install time crash handling
Requires: gdb
# support for installation from image and live & live image installations
Requires: rsync
# only WeakRequires elsewhere and not guaranteed to be present
Requires: device-mapper-multipath
Requires: zram-generator
# External tooling for managing NVMe-FC devices in the installation environment
Requires: nvme-cli

%description install-img-deps
The anaconda-install-img-deps metapackage lists all boot.iso installation image dependencies.
Add this package to an image build (eg. with lorax) to ensure all Anaconda capabilities are supported in the resulting image.

%package gui
Summary: Graphical user interface for the Anaconda installer
Requires: anaconda-core = %{version}-%{release}
Requires: anaconda-widgets = %{version}-%{release}
Requires: python3-meh-gui >= %{mehver}
Requires: adwaita-icon-theme
Requires: tigervnc-server-minimal
Requires: libxklavier >= %{libxklavierver}
Requires: libgnomekbd
Requires: libtimezonemap >= %{libtimezonemapver}
Requires: nm-connection-editor
Requires: keybinder3
%ifnarch s390 s390x
Requires: NetworkManager-wifi
%endif
Requires: anaconda-user-help >= %{helpver}
Requires: yelp
%if ! 0%{?rhel}
Requires: blivet-gui-runtime >= %{blivetguiver}
%endif
Requires: system-logos

# Needed to compile the gsettings files
BuildRequires: gsettings-desktop-schemas

%description gui
This package contains graphical user interface for the Anaconda installer.

%package tui
Summary: Textual user interface for the Anaconda installer
Requires: anaconda-core = %{version}-%{release}
Requires: python3-simpleline >= %{simplelinever}

%description tui
This package contains textual user interface for the Anaconda installer.

%package widgets
Summary: A set of custom GTK+ widgets for use with anaconda
Requires: %{__python3}

%description widgets
This package contains a set of custom GTK+ widgets used by the anaconda installer.

%package widgets-devel
Summary: Development files for anaconda-widgets
Requires: glade
Requires: %{name}-widgets%{?_isa} = %{version}-%{release}

%description widgets-devel
This package contains libraries and header files needed for writing the anaconda
installer.  It also contains Python and Glade support files, as well as
documentation for working with this library.

%package dracut
Summary: The anaconda dracut module
Requires: dracut >= %{dracutver}
Requires: dracut-network
Requires: dracut-live
Requires: xz
Requires: python3-kickstart
Requires: iputils

%description dracut
The 'anaconda' dracut module handles installer-specific boot tasks and
options. This includes driver disks, kickstarts, and finding the anaconda
runtime on NFS/HTTP/FTP servers or local disks.

%prep
%autosetup -p 1

%build
# use actual build-time release number, not tarball creation time release number
%configure ANACONDA_RELEASE=%{release}
%{__make} %{?_smp_mflags}

%install
%{make_install}
find %{buildroot} -type f -name "*.la" | xargs %{__rm}

# Create an empty directory for addons
mkdir %{buildroot}%{_datadir}/anaconda/addons

# required for live installations
desktop-file-install --dir=%{buildroot}%{_datadir}/applications %{buildroot}%{_datadir}/applications/liveinst.desktop

# If no langs found, keep going
%find_lang %{name} || :


# main package and install-env-deps are metapackages
%files

%files install-env-deps

# Allow the lang file to be empty
%define _empty_manifest_terminate_build 0

%files install-img-deps

# Allow the lang file to be empty here too
%define _empty_manifest_terminate_build 0

%files core -f %{name}.lang
%license COPYING
%{_unitdir}/*
%{_prefix}/lib/systemd/system-generators/*
%{_bindir}/instperf
%{_bindir}/anaconda-disable-nm-ibft-plugin
%{_bindir}/anaconda-nm-disable-autocons
%{_sbindir}/anaconda
%{_sbindir}/handle-sshpw
%{_datadir}/anaconda
%{_prefix}/libexec/anaconda
%exclude %{_datadir}/anaconda/gnome
%exclude %{_datadir}/anaconda/pixmaps
%exclude %{_datadir}/anaconda/ui
%exclude %{_datadir}/anaconda/window-manager
%exclude %{_datadir}/anaconda/anaconda-gtk.css
%exclude %{_prefix}/libexec/anaconda/dd_*
%{python3_sitearch}/pyanaconda
%exclude %{python3_sitearch}/pyanaconda/rescue.py*
%exclude %{python3_sitearch}/pyanaconda/__pycache__/rescue.*
%exclude %{python3_sitearch}/pyanaconda/ui/gui/*
%exclude %{python3_sitearch}/pyanaconda/ui/tui/*
%{_bindir}/analog
%{_bindir}/anaconda-cleanup
%dir %{_sysconfdir}/%{name}
%config %{_sysconfdir}/%{name}/*
%dir %{_sysconfdir}/%{name}/conf.d
%config %{_sysconfdir}/%{name}/conf.d/*
%dir %{_sysconfdir}/%{name}/product.d
%config %{_sysconfdir}/%{name}/product.d/*

%files live
%{_bindir}/liveinst
%{_sbindir}/liveinst
%config(noreplace) %{_sysconfdir}/pam.d/*
%config(noreplace) %{_sysconfdir}/security/console.apps/*
%{_libexecdir}/liveinst-setup.sh
%{_datadir}/applications/*.desktop
%{_datadir}/anaconda/gnome
%{_sysconfdir}/xdg/autostart/*.desktop

%files gui
%{python3_sitearch}/pyanaconda/ui/gui/*
%{_datadir}/anaconda/pixmaps
%{_datadir}/anaconda/ui
%if 0%{?rhel}
# Remove blivet-gui
%exclude %{_datadir}/anaconda/ui/spokes/blivet_gui.*
%exclude %{python3_sitearch}/pyanaconda/ui/gui/spokes/blivet_gui.*
%endif
%{_datadir}/anaconda/window-manager
%{_datadir}/anaconda/anaconda-gtk.css

%files tui
%{python3_sitearch}/pyanaconda/rescue.py
%{python3_sitearch}/pyanaconda/__pycache__/rescue.*
%{python3_sitearch}/pyanaconda/ui/tui/*

%files widgets
%{_libdir}/libAnacondaWidgets.so.*
%{_libdir}/girepository*/AnacondaWidgets*typelib
%{python3_sitearch}/gi/overrides/*

%files widgets-devel
%{_libdir}/libAnacondaWidgets.so
%{_libdir}/glade/modules/libAnacondaWidgets.so
%{_includedir}/*
%{_datadir}/glade/catalogs/AnacondaWidgets.xml
%{_datadir}/gtk-doc

%files dracut
%dir %{_prefix}/lib/dracut/modules.d/80%{name}
%{_prefix}/lib/dracut/modules.d/80%{name}/*
%{_prefix}/libexec/anaconda/dd_*

%changelog
* Wed Aug 21 2024 Martin Kolman <mkolman@redhat.com> - 34.25.5.9-1
- network: ignore kickstart configuration of nBFT devices (rvykydal)
  Resolves: RHEL-30149
  Resolves: RHEL-34235
  Resolves: RHEL-32146
- network: do not dump configurations of nBFT devices (rvykydal)
  Resolves: RHEL-30149
  Resolves: RHEL-34235
  Resolves: RHEL-32146
- network: ignore nBFT devices connections in network configuration (rvykydal)
  Resolves: RHEL-30149
  Resolves: RHEL-34235
  Resolves: RHEL-32146
- network: add a test for ignoring ifname=nbft* for device renaming (rvykydal)
  Resolves: RHEL-30149
  Resolves: RHEL-34235
  Resolves: RHEL-32146
- network: do not create empty dir for only ifname=nbft* options (rvykydal)
  Resolves: RHEL-30149
  Resolves: RHEL-34235
  Resolves: RHEL-32146
- network: Avoid creating link files for 'nbft' interfaces (tbzatek)
  Resolves: RHEL-30149
  Resolves: RHEL-34235
  Resolves: RHEL-32146
- Update translations from Weblate for rhel-9 (github-actions)

* Wed Aug 14 2024 Martin Kolman <mkolman@redhat.com> - 34.25.5.8-1
- Use proxy server also for FTP .treeinfo download (jkonecny)
  Resolves: RHEL-27938
- Update translations from Weblate for rhel-9 (github-actions)

* Wed Aug 07 2024 Radek Vykydal <rvykydal@redhat.com> - 34.25.5.7-1
- Fix source spoke being inaccessible if payload thread errors out (mkolman)
  Resolves: RHEL-4721
- Do not create default wired connections for bond ports (rvykydal)
  Resolves: RHEL-38451
- Consolidate code for dumping network connections (rvykydal)
  Related: RHEL-38451

* Mon Jul 01 2024 Katerina Koukiou <kkoukiou@redhat.com> - 34.25.5.6-1
- Update translations from Weblate for rhel-9
- Change location of rescue mode flag file (jstodola)
  Resolves: RHEL-4794

* Mon May 20 2024 Katerina Koukiou <kkoukiou@redhat.com> - 34.25.5.5-1
- Update translations from Weblate for rhel-9
- Do not rewrite logs in rescue mode (jstodola)
  Resolves: RHEL-4794
- Write a warning rescue selinux (akankovs)
  Resolves: RHEL-14005
- Fix kickstart --dhcpclass option application (rvykydal)
  Resolves: RHEL-30406

* Mon Apr 15 2024 Katerina Koukiou <kkoukiou@redhat.com> - 34.25.5.3-1
- Fix Source0 in spec to point to upstream source URL (kkoukiou)
- Do not try to load sha256 module in intramfs (rvykydal)
  Resolves: RHEL-4747
- Do not try to load the floppy kernel module (jstodola)
  Resolves: RHEL-4747
- anaconda-modprobe: don't try and load cramfs (awilliam)
  Resolves: RHEL-4747

* Fri Apr 12 2024 Katerina Koukiou <kkoukiou@redhat.com> - 34.25.5.2-1
- network: do not crash on destroyed device object in GUI (rvykydal)
  Resolves: RHEL-20891

* Tue Apr 09 2024 Katerina Koukiou <kkoukiou@redhat.com> - 34.25.5.1-1
- anaconda-diskroot: wait before dying on media check fail (awilliam)
  Resolves: RHEL-4790
- Add ping tool to Dracut (jkonecny)
  Resolves: RHEL-5719
- gui:Fix index error for _remove_treeinfo_repositories() (liuwenyu.0311)
  Resolves: RHEL-29561

* Thu Mar 14 2024 Radek Vykydal <rvykydal@redhat.com> - 34.25.4.9-1
- Do not initialize kernel features in init (jkonecny)
  Resolves: RHEL-27076

* Mon Mar 04 2024 Radek Vykydal <rvykydal@redhat.com> - 34.25.4.8-1
- Update translations
  Resolves: RHEL-24945

* Fri Feb 16 2024 Jiri Konecny <jkonecny@redhat.com> - 34.25.4.7-1
- Lower log file permission in /tmp (jkonecny)
  Resolves: RHEL-23345
- Add utility function to set file mode (jkonecny)
  Related: RHEL-23345

* Wed Feb 07 2024 Martin Kolman <mkolman@redhat.com> - 34.25.4.6-1
- Disable bug reporting to Bugzilla from anaconda (kkoukiou)
  Resolves: RHEL-24419
- Fixed file-write operation to a public directory (ataf)
  Resolves: RHEL-23345

* Thu Feb 01 2024 Martin Kolman <mkolman@redhat.com> - 34.25.4.5-1
- bootupd: Use --write-uuid (walters)
  Related: RHEL-17205
- bootloader: Detect bootupd and skip regular install (vslavik)
  Related: RHEL-17205
- ostree: Use bootupd if installed by payload (vslavik)
  Resolves: RHEL-17205
- bootloader: Create an installation task for collecting kernel arguments
  (vponcova)
  Related: RHEL-17205
- bootloader: Add the collect_arguments method (vponcova)
  Related: RHEL-17205
- bootloader: Remove the install_boot_loader function (vponcova)
  Related: RHEL-17205
- Apply the bootloader options before the installation (vponcova)
  Related: RHEL-17205

* Mon Jan 29 2024 Martin Kolman <mkolman@redhat.com> - 34.25.4.4-1
- rpm-ostree: Setup readonly sysroot for ostree & rw karg (tim)
  Related: RHEL-2250

* Wed Jan 24 2024 Martin Kolman <mkolman@redhat.com> - 34.25.4.3-1
- Fix missing emit of zfcp kickstart statements (maier)
  Related: RHEL-11384
- DeviceTreeViewer: Add path-id attribute to zfcp-attached SCSI disks (maier)
  Related: RHEL-11384
- Fix missing WWID values for multipath devices in advanced storage UI
  (#2046654) (maier)
  Resolves: RHEL-11384
- rescue: Don't allow to mount systems without a root device (vponcova)
  Resolves: RHEL-14696
- Do not crash on default None values of ostreecontainer command (rvykydal)
  Related: RHEL-2250
- Fix wrong dracut timeout message (jkonecny)
  Resolves: RHEL-5638
- Move rpm-ostree deps from Lorax to Anaconda (#2125655) (jkonecny)
  Related: RHEL-2250
- Implement needs_network for rpm_ostree_container (#2125655) (jkonecny)
  Related: RHEL-2250
- Add tests for RPM Ostree payload with source from container (#2125655)
  (rvykydal)
  Related: RHEL-2250
- Enable RPM OSTree from container source in payload (#2125655) (rvykydal)
  Resolves: RHEL-2250
- Add RPM OSTree source from container (#2125655) (rvykydal)
  Related: RHEL-2250

* Tue Jan 09 2024 Martin Kolman <mkolman@redhat.com> - 34.25.4.2-1
- tests: Add a test case for the NVMe module (vtrefny)
  Resolves: RHEL-11543
  Resolves: RHEL-11544
- Add a simple NVMe module for NVMe Fabrics support (vtrefny)
  Resolves: RHEL-11543
  Resolves: RHEL-11544
- network: ignore BOOTIF connections when creating device configurations
  (rvykydal)
  Resolves: RHEL-4766
- network: ignore BOOTIF connections when looking for initramfs bond ports
  (rvykydal)
  Resolves: RHEL-4766

* Thu Dec 07 2023 Jiri Konecny <jkonecny@redhat.com> - 34.25.4.1-1
- Fix versioning on RHEL 9.4 (jkonecny)

* Wed Dec 06 2023 Jiri Konecny <jkonecny@redhat.com> - 34.25.3.9-1
- timezone: for kickstart allow also timezones not offered by GUI (rvykydal)
  Resolves: jira#RHEL-13150
- Rename Organization to Organization ID on subscription screen (mkolman)
  Resolves: jira#RHEL-11167

* Wed Aug 09 2023 Jiri Konecny <jkonecny@redhat.com> - 34.25.3.8-1
- iscsi: Allow changing iSCSI initiator name once set (vtrefny)
  Resolves: rhbz#2223977
- Missing translation for button labels in Beta dialog
  Resolves: rhbz#2225450

* Wed Jul 12 2023 Jiri Konecny <jkonecny@redhat.com> - 34.25.3.7-1
- Allow showing passphrase when unlocking LUKS device (jstodola)
  Resolves: rhbz#2013190
- Be more indulgent when reclaiming disk space (jstodola)
  Resolves: rhbz#2187371
- Do not print error on inst.ks=cdrom|hd (jkonecny)
  Resolves: rhbz#2077045

* Fri Jun 30 2023 Jiri Konecny <jkonecny@redhat.com> - 34.25.3.6-1
- Remove unused variable in TUI software selection (ozobal)
  Related: rhbz#2214266
  Related: rhbz#2164819
- Fix aarch64 architecture detection (jstodola)
  Resolves: rhbz#2164819

* Mon Jun 26 2023 Jiri Konecny <jkonecny@redhat.com> - 34.25.3.5-1
- Add option for installing RedHat kernel (ozobal)
  Related: rhbz#2164819
  Resolves: rhbz#2214266
- Add TUI for installing non-standard kernels (ozobal)
  Resolves: rhbz#2214266
  Resolves: rhbz#2164819
- Add GUI option for installing 64k ARM kernel (ozobal)
  Resolves: rhbz#2214266
  Resolves: rhbz#2164819
- Add match_available_packages to dnf_manager (ozobal)
  Related: rhbz#2214266
  Related: rhbz#2164819

* Tue Jun 20 2023 Jiri Konecny <jkonecny@redhat.com> - 34.25.3.4-1
- Warn about deprecated inst.geoloc=provider_... (vslavik)
  Resolves: rhbz#2127473
- Improve doc strings for geolocation (vslavik)
  Related: rhbz#2127473
- Do not run geolocation for TUI (vslavik)
  Resolves: rhbz#2127473
- gui: Simplify invalid timezone handling. (vslavik)
  Related: rhbz#2127473
- Try to set timezone from language on welcome spoke (vslavik)
  Resolves: rhbz#2127473
- Always set timezone with priority (vslavik)
  Resolves: rhbz#2127473
- Add timezone priority to module backend and interface (vslavik)
  Resolves: rhbz#2127473
- Use existing locale in welcome spoke (vslavik)
  Resolves: rhbz#2127473
- Apply geolocation in main process (vslavik)
  Related: rhbz#2127473
- Add back waiting for geolocation (vslavik)
  Related: rhbz#2127473
- Add wait_for_task() to wait for a Task with timeout (vslavik)
  Related: rhbz#2127473
- Don't fall back to default timezone in welcome spoke (vslavik)
  Related: rhbz#2127473
- Use directly URLs in conf geoloc provider field (vslavik)
  Related: rhbz#2127473
- Remove unmodularized geolocation (vslavik)
  Related: rhbz#2127473
- Use modularized geolocation instead of unmodularized (vslavik)
  Related: rhbz#2127473
- Hide the geolocation task in Timezone's interface (vslavik)
  Related: rhbz#2127473
- Add GeolocationTask to the Timezone module (vslavik)
  Related: rhbz#2127473
- Add a D-Bus structure for geolocation data (vslavik)
  Related: rhbz#2127473
- Add conf option for geolocation provider (vslavik)
  Related: rhbz#2127473
- Retranslate welcome screen more simply (vslavik)
  Related: rhbz#2127473
- Fix translations of the pre-release warning dialog (vponcova)
  Resolves: rhbz#2165762
  Related: rhbz#2127473
- Split Timezone module tests for tasks to new file (vslavik)
  Related: rhbz#2127473
- Make check for geolocation start a standalone helper (vslavik)
  Related: rhbz#2127473
- Keep Timezone proxy in Welcome spoke (vslavik)
  Related: rhbz#2127473
- Split starting locales in welcome spoke to a helper (vslavik)
  Related: rhbz#2127473
- Rename constant to reflect its usage (vslavik)
  Related: rhbz#2127473
- Fix "proxy" boot option is printing inst. warning (jkonecny)
  Related: rhbz#2177219
- Allow showing proxy passwords on the installation source spoke (jstodola)
  Resolves: rhbz#2013190
- Allow showing passwords on the subscription spoke (jstodola)
  Resolves: rhbz#2013190
- Always hide the user password by default (jstodola)
  Related: rhbz#2013190
- Always hide the root password by default (jstodola)
  Related: rhbz#2013190

* Mon Jun 12 2023 Vladimír Slávik <vslavik@redhat.com> - 34.25.3.3-1
- Stop infinite wait for CDROM when KS is processed (jkonecny)
  Resolves: rhbz#2209599
- Apply --noverifyssl option for liveimg kickstart command (jstodola)
  Resolves: rhbz#2157921

* Mon Jun 05 2023 Vladimír Slávik <vslavik@redhat.com> - 34.25.3.2-1
- Fix kickstart proxy cmd in stage1 (jkonecny)
  Resolves: rhbz#2177219
- Check minimal LUKS passphrase length in FIPS mode for Kickstart (vslavik)
  Resolves: rhbz#2163497
- GUI: Require 8 chars of LUKS passwords in FIPS mode (vslavik)
  Resolves: rhbz#2163497
- Use inst.proxy in stage1 (jkonecny)
  Resolves: rhbz#2177219
- Change driver_updates exit info messages to debug (jkonecny)
  Related: rhbz#2154906

* Thu May 11 2023 Radek Vykydal <rvykydal@redhat.com> - 34.25.3.1-1
- Add DNS search and ignore options from kickstart (vslavik)
  Resolves: rhbz#2065754
- driver_updates: migrate driver_updates.py to pep8 format (jkonecny)
  Related: rhbz#2154906
- driver_updates: adding tests for the new logging solution (jkonecny)
  Related: rhbz#2154906
- driver_updates: add lot of debug logs for easier debugging (jkonecny)
  Related: rhbz#2154906
- driver_updates: extend where we print log messages (jkonecny)
  Resolves: rhbz#2154906
- Add missing documentation about OEMDRV (jkonecny)
  Related: rhbz#2171811
- oemdrv: wait up to 5 seconds for disks to be handled (rmetrich)
  Resolves: rhbz#2171811

* Wed Mar 22 2023 Martin Kolman <mkolman@redhat.com> - 34.25.2.10-1
- Update translations
  Resolves: rhbz#2139640

* Wed Feb 15 2023 Vendula Poncova <vponcova@redhat.com> - 34.25.2.9-1
- Fix network configuration from kickstart in intramfs (rvykydal)
  Resolves: rhbz#2153361

* Thu Feb 09 2023 Jiri Konecny <jkonecny@redhat.com> - 34.25.2.8-1
- Show only usable devices in custom partitioning (jstodola)
  Resolves: rhbz#2052938

* Thu Feb 02 2023 Jiri Konecny <jkonecny@redhat.com> - 34.25.2.7-1
- Show an error message when subscription token transfer fails (mkolman)
  Resolves: rhbz#2057472
- Bump blivet version for NVMe-oF support (vslavik)
  Resolves: rhbz#2164343
- Make text in custom_storage_helper more accurate (ozobal)
  Resolves: rhbz#2133046
- Fix infobar colors in GTK GUI (ozobal)
  Resolves: rhbz#2074827

* Wed Jan 11 2023 Vladimír Slávik <vslavik@redhat.com> - 34.25.2.6-1
- Add a NVMe-FC tab to the Advanced Storage screen (vslavik)
  Resolves: rhbz#2107346
- Update the .glade file for the Advanced Storage screen (vponcova)
  Related: rhbz#2107346
- Filter out NVMe over Fibre Channel from local disks (vslavik)
  Resolves: rhbz#2107346
- Install nvme-cli on boot.iso (vslavik)
  Resolves: rhbz#2107346

* Mon Jan 09 2023 Jiri Konecny <jkonecny@redhat.com> - 34.25.2.5-1
- payload: fix repo --includepkgs option (rvykydal)
  Resolves: rhbz#2158210
- bootloader/zipl.py: update for zipl >= 2.25.0 (dan)
  Resolves: rhbz#2157916

* Tue Jan 03 2023 Jiri Konecny <jkonecny@redhat.com> - 34.25.2.4-1
- Delegate auto-attach handling to RHSM (mkolman)
  Resolves: rhbz#2083319
- Use RHEL9_SshKeyData to fix sshkey quoting problem (bcl)
  Resolves: rhbz#2149362
- Test the InstallerStorage.copy method (vponcova)
  Related: rhbz#2093793
- Show multiple bootloader devices on the Manual Partitioning screen (vponcova)
  Resolves: rhbz#2093793
- Implement the Root.copy method (vponcova)
  Related: rhbz#2093793
- Redefine the Blivet.roots attribute (vponcova)
  Related: rhbz#2093793
- Redefine the Blivet.copy method (vponcova)
  Related: rhbz#2093793
- Use correct hint for VNC password boot option (jstodola)
  Resolves: rhbz#2124818

* Mon Nov 28 2022 Radek Vykydal <rvykydal@redhat.com> - 34.25.2.3-1
- Disable the concurrency check in the error dialog in TUI (vponcova)
  Resolves: rhbz#2070920
- Support bond device activated in initramfs from kickstart (rvykydal)
  Resolves: rhbz#2133053

* Thu Nov 10 2022 Martin Kolman <mkolman@redhat.com> - 34.25.2.2-1
- Initialize empty disks on the Manual Partitioning screen (vponcova)
  Resolves: rhbz#2127100
- infra: Set test vars from templates (vslavik)
- infra: Port check for matching templates from master (vslavik)
- infra: Port templating mechanism from master (vslavik)
- dracut: read filename dhcp option from dhcpopts file (rvykydal)
  Related: rhbz#1991843

* Thu Oct 27 2022 Martin Kolman <mkolman@redhat.com> - 34.25.2.1-1
- network: fix doc string of add_connection_sync (rvykydal)
  Related: rhbz#2125256
- network: use separate main conext for NM client in threads (rvykydal)
  Resolves: rhbz#2125256

* Thu Sep 08 2022 Vendula Poncova <vponcova@redhat.com> - 34.25.1.14-1
- Do not crash on network --device link with wireless device (rvykydal)
  Resolves: rhbz#2063127

* Tue Sep 06 2022 Radek Vykydal <rvykydal@redhat.com> - 34.25.1.13-1
- gui: fix summary hub layout for Japanese translations (rvykydal)
  Resolves: rhbz#2120293

* Wed Aug 17 2022 Martin Kolman <mkolman@redhat.com> - 34.25.1.12-1
- Improve Register button click feedback (mkolman)
  Resolves: rhbz#2074636

* Thu Aug 04 2022 Vladimir Slavik <vslavik@redhat.com> - 34.25.1.11-1
- Disable the Unregister button during unregistration (mkolman)
  Resolves: rhbz#2068192
- Install rdma-core if infiniband network device is found (rvykydal)
  Resolves: rhbz#2050331

* Tue Jul 19 2022 Jiri Konecny <jkonecny@redhat.com> - 34.25.1.10-1
- Communicate media verification result clearly (vslavik)
  Related: rhbz#2057469
- Media verification dialog button reflects state (vslavik)
  Resolves: rhbz#2057469
- Add tooltip to the Insights checkbox (jkonecny)
  Resolves: rhbz#2071665
- Increase the minimal suggested size for /boot (vslavik)
  Resolves: rhbz#2042431

* Thu Jul 14 2022 Martin Kolman <mkolman@redhat.com> - 34.25.1.9-1
- Allow to omit WWPN and LUN for NPIV-enabled zFCP devices (jstodola)
  Resolves: rhbz#1937032
- Reduce the width of the zFCP dialog (jstodola)
  Related: rhbz#1937032
- Fix product config product_name for Rocky Linux (tucklesepk)
  Resolves: rhbz#2096046
- Add Circle Linux profile to Anaconda(rhel-9) (bella)
  Resolves: rhbz#2095351

* Tue Jun 28 2022 Radek Vykydal <rvykydal@redhat.com> - 34.25.1.8-1
- bootloader: do not consider non-ibft iscsi disk as usable for bootloader
  (rvykydal)
  Resolves: rhbz#2003519
- Fix kickstart command order in new version (vslavik)
  Resolves: rhbz#2100463
- TUI software spoke is ready with failing repos, too (vslavik)
  Resolves: rhbz#2020299

* Thu Jun 16 2022 Radek Vykydal <rvykydal@redhat.com> - 34.25.1.7-1
- tests: update the order of commands (rootpw) in generated kickstart
  (rvykydal)
  Related: rhbz#2033849
- dnf: apply the /etc/dnf/dnf.conf configuration file in the installer
  (rvykydal)
  Resolves: rhbz#2053710
- Add support for rootpw --allow-ssh (rvykydal)
  Resolves: rhbz#2033849

* Fri Jun 10 2022 Radek Vykydal <rvykydal@redhat.com> - 34.25.1.6-1
- Report registration errors from kickstart (mkolman)
  Resolves: rhbz#2000652
- GUI: Show the dialog for a missing passphrase in an enlight box (vponcova)
  Related: rhbz#2087218
- GUI: Ask for a missing passphrase during automated installations (vponcova)
  Resolves: rhbz#2087218
- Create functions for a missing passphrase in pyanaconda.ui.lib (vponcova)
  Related: rhbz#2087218
- Add missing period when concatenating password error strings (jkonecny)
  Resolves: rhbz#2075417
- Enable bootloader hiding on RHEL (rharwood)
  Resolves: rhbz#2059414

* Wed Jun 01 2022 Radek Vykydal <rvykydal@redhat.com> - 34.25.1.5-1
- Run FixZIPLBootloader task after FIPS setup (rvykydal)
  Resolves: rhbz#2022841

* Thu May 26 2022 Radek Vykydal <rvykydal@redhat.com> - 34.25.1.4-1
- Cleanup unneeded NFS repo with rd.live.ram parameter (mmatsuya)
  Resolves: rhbz#2082132

* Tue May 24 2022 Radek Vykydal <rvykydal@redhat.com> - 34.25.1.3-1
- Run restorecon in chroot when handling home dirs (vslavik)
  Resolves: rhbz#2072426
- Move restorecon calls in Tasks to a helper function (vslavik)
  Related: rhbz#2072426
- Add Virtuozzo Linux profile to Anaconda (dsilakov)
  Resolves: rhbz#2067195

* Wed Apr 20 2022 Radek Vykydal <rvykydal@redhat.com> - 34.25.1.2-1
- ovirt: move /var/tmp to its own partition (sbonazzo)
  Resolves: rhbz#2058538

* Thu Mar 17 2022 Radek Vykydal <rvykydal@redhat.com> - 34.25.1.1-1
- Make failure in generating of dracut arguments for iSCSI device non-fatal.
  (rvykydal)
  Resolves: rhbz#2065171
- Do not generate dracut arguments multiple times for some storage devices
  (rvykydal)
  Related: rhbz#2065171
- Skip /etc/machine-info during live installs (awilliam)
  Resolves: rhbz#2065170

* Thu Feb 24 2022 Vendula Poncova <vponcova@redhat.com> - 34.25.0.27-1
- Use cache when fetching organization data from the GUI (mkolman)
  Resolves: rhbz#2044258
- Bump subscription-manager version (mkolman)
  Related: rhbz#2048449
- Improve UX in Simple Content Access mode (mkolman)
  Resolves: rhbz#2048449
- Add IsSimpleContentAccessEnabled property (mkolman)
  Related: rhbz#2048449
- Add support for SCA mode detection from registration data (mkolman)
  Related: rhbz#2048449

* Thu Feb 03 2022 Vladimir Slavik <vslavik@redhat.com> - 34.25.0.26-1
- Write all PVs to LVM devices file (vslavik)
  Resolves: rhbz#2040302
- Fix the status of the root configuration screen (vponcova)
  Related: rhbz#2026916
- Fix the condition for entering the root configuration (vponcova)
  Resolves: rhbz#2026916
- Move tests for pyanaconda.ui.lib.users to a new file (vponcova)
  Related: rhbz#2026916

* Tue Jan 18 2022 Vladimir Slavik <vslavik@redhat.com> - 34.25.0.25-1
- Hide the help button on the progress spoke (vponcova)
  Related: rhbz#1995945
- Enable the built-in help content (vponcova)
  Resolves: rhbz#1995945
- Remove the provides_web_browser property (vponcova)
  Related: rhbz#1995945
- Cache the parsed content of the help mapping files (vponcova)
  Related: rhbz#1995945
- Remove the default_help_pages configuration option (vponcova)
  Related: rhbz#1995945
- Remove the helpFile attribute (vponcova)
  Related: rhbz#1995945
- Implement the unified help support (vponcova)
  Related: rhbz#1995945
- Define a unique id in the main spokes and hubs (vponcova)
  Related: rhbz#1995945
- Add the Screen class (vponcova)
  Related: rhbz#1995945
- Enable Closest mirror on CentOS Stream 9 (jkonecny)
  Related: rhbz#1955331
- Do not modify boot order on UEFI if asked (vslavik)
  Resolves: rhbz#2025953

* Tue Jan 11 2022 Vladimir Slavik <vslavik@redhat.com> - 34.25.0.24-1
- Create the LVM devices file (vslavik)
  Resolves: rhbz#2011329
- Update outdated system purpose related strings (mkolman)
  Related: rhbz#2015059
- Always set system purpose from GUI (mkolman)
  Resolves: rhbz#2015059

* Thu Dec 09 2021 Martin Kolman <mkolman@redhat.com> - 34.25.0.23-1
- Fix boot options generated by the dracut module (vponcova)
  Resolves: rhbz#2003217

* Thu Dec 02 2021 Martin Kolman <mkolman@redhat.com> - 34.25.0.22-1
- Add base repo name for CentOS Stream after repository renaming (jkonecny)
  Resolves: rhbz#1955331
- The OPAL compatibility with XFS features is mandatory (vponcova)
  Resolves: rhbz#2008792

* Fri Nov 26 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.21-1
- Wait for all background threads to finish before filling installation task
  queue (mkolman)
  Resolves: rhbz#2017428
- Check the support for the Subscription module on startup (vponcova)
  Resolves: rhbz#1957063
- Activate DBus modules based on the new configuration options (vponcova)
  Related: rhbz#1957063
- Add new configuration options for the DBus module activation (vponcova)
  Related: rhbz#1957063
- Add product config for Rocky Linux (tucklesepk)
  Resolves: rhbz#2019995

* Fri Nov 05 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.20-1
- Fix application of network --mtu kickstart option in Anaconda (rvykydal)
  Resolves: rhbz#2019813
- Print progress dots on one line in TUI (honza.stodola)
  Resolves: rhbz#1998668
- Roll back Satellite provisioning if subscription attempt fails with error
  (mkolman)
  Resolves: rhbz#2010865

* Wed Oct 20 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.19-1
- Unify GUI & TUI root spoke completeness conditions (vslavik)
  Resolves: rhbz#1999646
- Make network spoke GUI more robust in cases of missing NM Client. (rvykydal)
  Resolves: rhbz#2014241
- Do not crash on missing NM Client on --vnc installations (rvykydal)
  Related: rhbz#2014241
- In installer environment set static, not transient hostname (rvykydal)
  Resolves: rhbz#2009403
- Add AlmaLinux product support (andrew.lukoshko)
  Resolves: rhbz#2004653

* Wed Oct 06 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.18-1
- Fix Satellite provisioning rollback after unregistration (mkolman)
  Resolves: rhbz#2006718
- Payload should wait for all storage related threads to finish (mkolman)
  Resolves: rhbz#2006786
- Make organization fetching errors non-fatal (mkolman)
  Resolves: rhbz#2006375

* Thu Sep 23 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.17-1
- Verify the OPAL compatibility with XFS features (vponcova)
  Resolves: rhbz#2000923
- Generate LVM device file after installation (vslavik)
  Resolves: rhbz#2005034

* Wed Sep 15 2021 Martin Kolman <mkolman@redhat.com> - 34.25.0.16-1
- Support multi-org accounts in the GUI (mkolman)
  Resolves: rhbz#1965105
- Pass error instance directly to error callback (mkolman)
  Related: rhbz#1965105
- Add the RetrieveOrganizationsTask task (mkolman)
  Related: rhbz#1965105
- Unit test adjustments - asynchronous handler (mkolman)
  Related: rhbz#1951709
- Unit test adjustments - subscription module (mkolman)
  Related: rhbz#1951709
- Unit test adjustments - DBus tasks (mkolman)
  Related: rhbz#1951709
- Split system purpose tests to a separate file (mkolman)
  Related: rhbz#1951709
- Add tests for the new Satellite helper module (mkolman)
  Related: rhbz#1951709
- Reflect Satellite use in source spoke (mkolman)
  Related: rhbz#1951709
- Report registration to Satellite in the GUI (mkolman)
  Related: rhbz#1951709
- Rename "Custom server URL" to "Satellite URL" (mkolman)
  Related: rhbz#1951709
- Add Satellite support to asynchronous registration handler (mkolman)
  Resolves: rhbz#1951709
- Add handler for install time Satellite provisioning error (mkolman)
  Related: rhbz#1951709
- Use target system Satellite provisioning DBus task (mkolman)
  Related: rhbz#1951709
- Satellite related changes in the Subscription DBus module (mkolman)
  Related: rhbz#1951709
- Add Satellite related DBus tasks (mkolman)
  Related: rhbz#1951709
- Add Satellite support module (mkolman)
  Related: rhbz#1951709
- Remove misleading warning about inst.ks.device replacing ksdevice (rvykydal)
  Resolves: rhbz#2000140
- Create shared constants file for subscription module (mkolman)
  Related: rhbz#1951709
- Move USER_AGENT to core/constants.py (mkolman)
  Related: rhbz#1951709

* Thu Aug 26 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.15-1
- Add dependency for bugzilla reporting plugin (vslavik)
  Resolves: rhbz#1992991

* Tue Aug 24 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.14-1
- Check source type directly, not via DBus (mkolman)
  Resolves: rhbz#1955311
- Move post installation scripts to the end of queue (lveyde)
  Resolves: rhbz#1983922

* Wed Aug 11 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.13-1
- Fix dependency on zram-generator (rvykydal)
  Resolves: rhbz#1991617

* Mon Aug 02 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.12-1
- Make critical warnings from Dracut more visible (jkonecny)
  Resolves: rhbz#1983098
- Print Dracut errors encountered during boot after Anaconda starts (jkonecny)
  Resolves: rhbz#1983098
- Add function to print critical warnings more visible during boot (jkonecny)
  Related: rhbz#1983098
- Add new error reporting hook when Dracut timeout (jkonecny)
  Resolves: rhbz#1983098
- Disable built-in help system on RHEL 9 for now (mkolman)
  Resolves: rhbz#1949073
- Make it possible to disable the built-in help system (mkolman)
  Related: rhbz#1949073
- Add a mechanism to hide help button per page (vslavik)
  Related: rhbz#1949073
- Make sure parent class initialize() method is run in spokes (mkolman)
  Related: rhbz#1949073
- Disable anaconda-core's requirement on subscription-manager on CentOS (carl)
  Resolves: rhbz#1984959

* Tue Jul 20 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.11-1
- Run installation tasks from ConfigureBootloaderWithTasks (vponcova)
  Related: rhbz#1977348
- Add the CollectConfigureBootloaderTasks method (vponcova)
  Related: rhbz#1977348
- Add the ConfigureBootloaderWithTasks method (vponcova)
  Resolves: rhbz#1977348
- Show suggestions for an error caused by inconsistent sector sizes (vponcova)
  Resolves: rhbz#1955514
- Configure the multilib policy of the target system (vponcova)
  Resolves: rhbz#1962026
- Enable the zram-generator service again (vponcova)
  Resolves: rhbz#1975881
- Enable NM autoconnections only if inst.ks and ip= is not used (rvykydal)
  Resolves: rhbz#1978264
- Disable NM autoconnections in Anaconda (rvykydal)
  Resolves: rhbz#1978264

* Mon Jun 28 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.10-1
- Remove kickstart btrfs support (mkolman)
  Related: rhbz#1961087
- Use RHEL9 versions of commands from RHEL9 handler (mkolman)
  Related: rhbz#1961087
- Use RHEL 9 handler (mkolman)
  Resolves: rhbz#1961087

* Tue Jun 22 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.9-1
- Update the pixel depth of xvnc server from 16 to 24 (rvykydal)
  Resolves: rhbz#1973607
- Clean up the initialization of PartTypeSpoke (vponcova)
  Resolves: rhbz#1938677
- Use C.UTF-8 if the requested locale is unsupported (vponcova)
  Resolves: rhbz#1958876
- Don't match a non-POSIX locale with a POSIX langcode (vponcova)
  Related: rhbz#1958876
- Fix potential use of uninitialized variable (vslavik)
  Resolves: rhbz#1938677
- Fix potential use of uninitialized variable (vslavik)
  Resolves: rhbz#1938677
- Make it possible to skip install time Insights errors (mkolman)
  Resolves: rhbz#1955296
- Fix literal curly braces in dracut scripts (vslavik)
  Resolves: rhbz#1938677
- Fix logging messages (vslavik)
  Resolves: rhbz#1938677
- Fix broken hashbang (vslavik)
  Resolves: rhbz#1938677

* Tue Jun 08 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.8-1
- Add unit test for biosdevname package requirement (rvykydal)
  Related: rhbz#1964455
- Require biosdevname package if biosdevname=1 boot option is set (rvykydal)
  Resolves: rhbz#1964455
- Replace the deprecated syspurpose CLI tool with SetSysrpose DBus call
  (mkolman)
  Resolves: rhbz#1939708

* Wed Jun 02 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.7-1
- Revert "Revert "Add tests for the inst. prefix requirement"" (jkonecny)
  Related: rhbz#1947376
- Revert "Revert "Do not support no inst. Anaconda boot args in systemd
  services"" (jkonecny)
  Resolves: rhbz#1947376
- Revert "Do not require inst. prefixes for Anaconda boot arguments" (jkonecny)
  Resolves: rhbz#1947376
- Revert "Revert "Remove support for boot arguments without 'inst.' prefix from
  Dracut"" (jkonecny)
  Resolves: rhbz#1947376

* Tue May 25 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.6-1
- Revert "Drop the "Allow SSH root login with password" checkbox (mkolman)"
  Resolves: rhbz#1855736
- Add a log message for successful installation (vslavik)
  Resolves: rhbz#1955312
- Remove support for metacity (rvykydal)
  Resolves: rhbz#1961104
- Drop the "Allow SSH root login with password" checkbox (mkolman)
  Resolves: rhbz#1855736

* Wed May 19 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.5-1
- Avoid a race condition during Connect to Red Hat spoke initialization
  (mkolman)
  Resolves: rhbz#1959383

* Mon May 17 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.4-1
- Support also gnome-kiosk window manager (rvykydal)
  Related: rhbz#1960682

* Tue May 11 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.3-1
- Add RHEL-specific advice to X timeout message (vslavik)
  Related: rhbz#1955306
- Fix AskVNCSpoke call (vslavik)
  Related: rhbz#1955306
- Improve X startup error messages (vslavik)
  Related: rhbz#1955306
- Terminate X server after timeout and restore crash test handler (vslavik)
  Related: rhbz#1955306
- Reorganize control flow in startX (vslavik)
  Related: rhbz#1955306
- Handle SIGUSR1 correctly after Xorg timeout (vslavik)
  Resolves: rhbz#1955306
- Refactor minor details in startX (vslavik)
  Related: rhbz#1955306
- subscription: allow dates in ISO 8601 format (ptoscano)
  Resolves: rhbz#1947447

* Mon May 10 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.2-1
- Revert "Add tests for the inst. prefix requirement" (rvykydal)
  Related: rhbz#1947376
- Do not require inst. prefixes for Anaconda boot arguments (jkonecny)
  Related: rhbz#1947376
- Revert "Do not support no inst. Anaconda boot args in systemd services"
  (jkonecny)
  Related: rhbz#1947376
- Revert "Remove support for boot arguments without 'inst.' prefix from Dracut"
  (jkonecny)
  Related: rhbz#1947376
- The kernel boot argument sshd is removed and should warn user (jkonecny)
  Resolves: rhbz#1954672

* Tue May 04 2021 Radek Vykydal <rvykydal@redhat.com> - 34.25.0.1-1
- Remove support for boot arguments without the "inst." prefix (jkonecny)
  Resolves: rhbz#1947376

* Mon Apr 12 2021 Martin Kolman <mkolman@redhat.com> - 34.24.9-1
- Allow to exclude the kernel-lpae package (vponcova)

* Wed Mar 31 2021 Martin Kolman <mkolman@redhat.com> - 34.24.8-1
- ostree: ignore exit code 65 for systemd-tmpfiles (vponcova)
- Turn off wrapping of the scale values (vponcova)
- Make the scale visible by default (#1943370) (vponcova)

* Tue Mar 30 2021 Martin Kolman <mkolman@redhat.com> - 34.24.7-1
- network: match also connections named by MAC created by NM in initramfs
  (rvykydal)
- Create /tmp with the right permissions (#1937626) (vponcova)
- Don't recommend zram-generator-defaults (#1938132) (vponcova)
- Don't automatically execute the default partitioning (vponcova)
- Fix the warning about working NTP servers (#1889180) (vponcova)
- Remove implicit dependencies (vponcova)
- Don't install anaconda-install-env-deps by default (vponcova)

* Mon Mar 22 2021 Martin Kolman <mkolman@redhat.com> - 34.24.6-1
- Check if the mount point exists before calling statvfs (#1824357) (vponcova)
- Do not follow symlinks when copying /etc/resolv.conf (#1933454) (rvykydal)
- Use the volume UUID to search for the GRUB config in btrfs partitions
  (javierm)
- Drop python3-syspurpose dependency (mkolman)
- Fix copypaste typo in github owner tests (vslavik)
- Modify owner tests for this f34-release branch (vslavik)
- Fix running tests for the f34-devel branch (vslavik)
- Wrap text in spoke title labels, if needed (vslavik)
- Wrap welcome spoke title if needed (vslavik)
- Choose the best locale more carefully (#1933384) (vponcova)
- Make the user interface context safe for the initial setup (vponcova)
- The network spoke should be visible in live spins (#1932961) (vponcova)
- Ignore Pylint errors on DNF API (vslavik)
- Ignore Pylint errors for PropertiesChanged.connect (vslavik)
- Silence false Pylint warning (vslavik)
- Ignore false Pylint errors for Enum subclasses (vslavik)
- Determine GRUB directory relative path to use in config file (javierm)

* Mon Feb 22 2021 Martin Kolman <mkolman@redhat.com> - 34.24.5-1
- Add the "Encrypt my data" checkbox to the custom partitioning spoke
  (vponcova)
- Don't translate prompt keys (#1892830) (vponcova)
- Fix RHEL zram conditional in spec file (mkolman)
- Remove interactive parameter from container-rpm-test (jkonecny)
- Add container push for rpm containers (jkonecny)
- Enable our and blivet COPR repositories for rpm tests (jkonecny)
- vconsole font selection to cover more langs (suanand)

* Thu Feb 18 2021 Martin Kolman <mkolman@redhat.com> - 34.24.4-1
- [Storage] add btrfs_compression option (#1928857) (michel)
- Correct branch config after merge (vslavik)
- Enable Makefiles and Dockerfiles for branched Fedora (vslavik)
- packit: make tests ⊂ builds for the chroot set (ttomecek)
- packit: run all actions in a single action (ttomecek)
- configure.ac: make the Copyright up to date (ttomecek)
- ovirt: rebase on CentOS Stream (sbonazzo)
- Use a custom stylesheet to define RHEL-specific stylesheet data (vponcova)
- Remove unused variables from Makefile (vslavik)
- Drop astroid hotfix patch (jkonecny)
- Don't block the start of the Network module by the hostname service
  (vponcova)
- Remove unused variables related to mock (vslavik)
- Save lorax-packages.log to installed system (rvykydal)

* Mon Feb 15 2021 Martin Kolman <mkolman@redhat.com> - 34.24.3-1
- Do not hard-require zram-generator-default on RHEL just yet (mkolman)
- Improve Packit configuration to use fedora-development (jkonecny)
- Add a kickstart specification for the main process (vponcova)
- Adapt Packit configuration to a newly branched Fedora (jkonecny)
- Create swap by default in RHEL-based installations (#1915297) (vponcova)
- Add missing space to a message (vslavik)
- Use Linux HOST_NAME_MAX hostname length limit (xiaqirong1)

* Fri Feb 12 2021 Martin Kolman <mkolman@redhat.com> - 34.24.2-1
- Rename pyanaconda.modules.common.typing (vponcova)

* Thu Feb 11 2021 Martin Kolman <mkolman@redhat.com> - 34.24.1-1
- Adjust configuration options for Fedora 34 (mkolman)
- Add dependabot support for GitHub actions (jkonecny)
- Set volume id for iso built for kickstart test (rvykydal)
- Guess the default product name from the os-release files (vponcova)
- Apply overrides for the anaconda widgets only in the test environment
  (vponcova)
- Create real updates images (vponcova)
- Remove deprecated support for add-ons (vponcova)
- Don't run installation tasks of add-ons in a meta task (vponcova)
- network: wrap IP addresses showed in GUI for wireless devices (#1925781)
  (rvykydal)
- Install support for non-ascii keyboard layouts (#1919483) (vponcova)

* Mon Feb 08 2021 Martin Kolman <mkolman@redhat.com> - 34.24-1
- Modify spec file to add patches required on rhel-9 rebuild (#1907566)
  (jkonecny)
- Unify GRUB configuration file location across all platforms (javierm)
- Do not use redirector for rawhide repository for iso building on PR
  (rvykydal)
- Move finding flatpak size to a task (vslavik)
- Move flatpak installation code to a task (vslavik)
- Move and rename FlatpakPayload (vslavik)
- Abort with a message on invalid host name in kickstart (vslavik)
- Use redirector for rawhide repository for iso building on PR (rvykydal)
- Add tests for the inst. prefix requirement (#1912502) (jkonecny)
- Do not support no inst. Anaconda boot args in systemd services (#1912502)
  (jkonecny)
- Remove check to avoid process of help and version boot args (#1912502)
  (jkonecny)
- Remove Anaconda boot arguments without inst. prefix from stage2 (#1912502)
  (jkonecny)
- Add support for non-critical installation errors (vponcova)
- Don't run a canceled task (vponcova)
- Fix exclude arguments of tar payload extracting. (rvykydal)
- Remove support for boot arguments without 'inst.' prefix from Dracut
  (#1912502) (jkonecny)
- Cache flatpak size instead of persistent instance (vslavik)

* Fri Feb 05 2021 Martin Kolman <mkolman@redhat.com> - 34.23-1
- Add a metapackage for image (boot.iso) dependencies (vslavik)
- Take dnf substitutions from installer environment configuration (rvykydal)
- Fix getting kernel version list for liveimg (rvykydal)

* Wed Feb 03 2021 Martin Kolman <mkolman@redhat.com> - 34.22-1
- Don't initialize the software selection if the payload is not set up
  (#1916114) (vponcova)
- Unify the ready methods of the software selection spokes (vponcova)
- Deprecate the interactive-defaults.ks file (vponcova)
- Deprecate the %%anaconda section and the pwpolicy command (vponcova)
- Apply the pwpolicy kickstart command (vponcova)
- Upate repo url for kickstart tests run on PR (rvykydal)
- Adjust RHV-H product config to match real implementation (sbonazzo)
- Add DBus support for the password policies (vponcova)
- Don't use the pwpolicy kickstart command (vponcova)
- Create a DBus structure for the password policy (vponcova)
- Add the password_policies configuration option (vponcova)
- Move Users module tests to a directory (vslavik)
- Move Security module tests to a directory (vslavik)
- Move partitioning specification test to directory (vslavik)
- Move Payloads module and source tests to a directory (vslavik)
- Move Network module tests to a directory (vslavik)
- Add the configuration options can_change_root and can_change_users (vponcova)
- Remove some unused methods from the FSSet class (vponcova)
- Mount the /tmp of the installed system as a tmpfs (#1306452) (vponcova)
- Create the get_system_filesystems function (vponcova)
- Create the collect_filesystems method (vponcova)
- Do not use cache for container build (jkonecny)
- Update list of projects to test after move from Zanata to Weblate (vtrefny)
- Ignore fallback ITS rule warning from gettext (vtrefny)
- Switch the license to LGPL (dshea)

* Thu Jan 28 2021 Martin Kolman <mkolman@redhat.com> - 34.21-1
- Allow to disable the Security module (vponcova)
- Add important files for container build to rebuild check (jkonecny)
- Avoid using DockerHub because of limits (jkonecny)
- anaconda should add only s390utils-core (dan)
- Fix root password and LUKS passphrase visibility toggle (#1911360) (mkolman)
- Fix the should_run methods of the network spoke (vponcova)
- Prevent shell injection from a /kickstart-test comment (jkonecny)
- network: validate bond options on our side after change in NM (#1918744)
  (rvykydal)
- network: fix bond confiuration for empty bond options (#1918744) (rvykydal)
- Allow to disable the Services module (vponcova)

* Fri Jan 22 2021 Martin Kolman <mkolman@redhat.com> - 34.20-1
- Add master unit-tests to contributors (gated) workflow (jkonecny)
- Add master test execution for owners for this repository (jkonecny)
- Rename validate-rhel-8 workflow to tests-contributors (jkonecny)
- Specify version 3 of GTK+ and GDK for fedora-welcome (awilliam)

* Thu Jan 21 2021 Martin Kolman <mkolman@redhat.com> - 34.19-1
- Fix nose tests execution command when installed from pip (jkonecny)
- Add missing nose test dependency back from pip (jkonecny)
- Use RHEL help content for RHV/Ovirt (mkolman)
- Remove build-time dependencies for nose tests (vslavik)
- Allow to disable the Localization module (vponcova)
- Rename kickstart status reporting to kickstart-test (jkonecny)
- Skip storage-related spokes in the initial setup (#1918048) (vponcova)
- Support should_run for standalone GUI spokes (vponcova)
- GH workflow: do not fail all matrix jobs on failure of one (jkonecny)
- Update versions of the kickstart commands (vponcova)
- network: handle wireless configure button sensitiveness (rvykydal)
- Allow to disable the network installation (vponcova)
- Allow to disable the Users module (vponcova)
- Allow to disable the Timezone module (vponcova)
- Select disks for implicit partitions (vponcova)
- Extend the PartSpec class (vponcova)
- for non-ascii keyboard layouts, set 'native' to the virtual console
  explicitly Resolves: rhbz#1912609 (suanand)

* Mon Jan 18 2021 Martin Kolman <mkolman@redhat.com> - 34.18-1
- Skip payload-related spokes in the initial setup (#1915541) (vponcova)
- Always show pykickstart parse warnings (vslavik)
- Grab GitHub notifications for periodic workflows (jkonecny)
- Split OSTree sysroot-setting to a task (vslavik)
- Split OSTree pull to a task (vslavik)
- Split OSTree deployment to a task (vslavik)
- Stop the timer that calls a callback for clicking on the continue button
  (vponcova)
- Formatting fixes (vslavik)
- Split OSTree bootloader configuration to a task (vslavik)
- Split OSTree remote changes to a task (vslavik)
- Split OSTree fs and repo initialization to a task (vslavik)
- Split OSTree bootloader data copying to a task (vslavik)
- Split OStree mount target preparation to a task (vslavik)
- Move the RPM OSTree test to a directory (vslavik)
- Move the safe_exec_with_redirect function (vslavik)
- Save logs correctly after container update GH action run (jkonecny)

* Mon Jan 11 2021 Martin Kolman <mkolman@redhat.com> - 34.17-1
- Always report IPMI events from the exit dialog windows (vponcova)
- Always report IPMI events from the exception handler (vponcova)
- Always log IPMI events (vponcova)
- Add a new handler for PayloadSetupError and SourceSetupError (vponcova)
- Remove the error handlers for removed or unused DNF errors (vponcova)
- Refactorize the code for handling marking errors (vponcova)
- Don't run the error handler in the installation code (vponcova)
- Don't run the error handler if there is no callback (vponcova)
- Reorganize the mapping of error handlers (vponcova)
- Remove the error handler for no such group (vponcova)
- Remove the error handler for invalid image size (vponcova)
- Flush stdout during the TUI installation (vponcova)
- Set the PR status ASAP for kickstart tests (jkonecny)
- Always update container images before running workflow (jkonecny)
- Solve problem with missing loop device for kstest run (jkonecny)
- Remove the error handler for the missing image (vponcova)
- Remove the error handler for the unsupported algorithm (vponcova)
- Handle errors in the installation tasks (vponcova)
- Initialize librepo logger (#1908286) (pkratoch)
- Add rpm-tests support for external contributors (jkonecny)
- Don't run the execute method in the kickstart installation in TUI by default
  (vponcova)
- Don't run spokes that don't support live payloads (vponcova)
- Don't run spokes that don't support dir installations (vponcova)
- Don't run spokes that don't support non-package payloads (vponcova)
- Create a user interface context (vponcova)
- Add how to run a subset of nosetests to tests README (jkonecny)
- Fix warning when running a subset of nosetests (jkonecny)
- network: fix double-free using libnm function filter_connections() (rvykydal)
- Provide a hint for the desired capacity (vponcova)
- Fix python3 rpm package name in spec file (jkonecny)
- Allow to interrupt media verification (#1349152) (honza.stodola)
- Use correct identity for ELN (sgallagh)
- virtualization: add missing /var/crash (sbonazzo)

* Mon Jan 04 2021 Martin Kolman <mkolman@redhat.com> - 34.16-1
- Enable rpm-tests on Fedora ELN (mpitt)
- Fix create_rpm_test on Fedora ELN/RHEL (mpitt)
- Fix container-rpm-test log output (mpitt)
- Define container for running rpm-tests (mpitt)
- Move to official fedora ELN container image (mpitt)
- Remove 'firstboot --enable' from interactive defaults (vponcova)
- Build real boot.iso for /kickstart-tests runs (mpitt)
- Fix artifact name in kickstart-tests.yml workflow (mpitt)
- Import imp on demand (vponcova)
- Adapt UI and tests to localhost.localdomain setting removal (rvykydal)
- Stop trying to set the default hostname (zbyszek)
- Document how to run kickstart tests in anaconda PRs (mpitt)
- Update the GitHub workflow documentation (mpitt)
- Add description of our GH workflow to tests/README file (jkonecny)
- Remove the support for updates on a floppy disk (vponcova)
- Fix list of Anaconda tests (jkonecny)
- Disable the debug solver debugging (vponcova)
- Select groups from a kickstart file in GUI (vponcova)
- Remove kickstart packages from GUI (vponcova)
- Remove kickstart packages from TUI (vponcova)
- Remove kickstart packages from the DNF payload class (vponcova)
- Remove kickstart packages from the installation tasks (vponcova)
- Remove kickstart packages from the DNF utilities (vponcova)
- Remove kickstart packages from the DNF manager (vponcova)
- Handle the %%packages section in the DBus module (vponcova)
- Add the PackagesSeen property (vponcova)
- Add CentOS Stream config (riehecky)
- Deprecate the level option of the logging kickstart command (vponcova)

* Mon Dec 07 2020 Martin Kolman <mkolman@redhat.com> - 34.15-1
- Drop old WiFi & geocoding based geolocation support (mkolman)
- Add bot PR comment to run kickstart tests (mpitt)
- Migrate Anaconda daily COPR builds to Packit (jkonecny)
- Fix missing inst. prefixes for bootloader options in documentation (jkonecny)
- network: make generating of kickstart more robust (#1897832) (rvykydal)
- Fixup category sorting (mkolman)
- Place the user tasks into the right task queue (rvykydal)
- Lower geolocation connection timeout to 5 seconds (#1774873) (mkolman)
- Remove unused hubQ messages (vponcova)
- Remove the justUpdate argument (vponcova)
- Don't run the execute method in the kickstart installation in GUI by default
  (vponcova)
- Don't use an empty string as a system root (vponcova)
- Fix logs from the get_os_release_value function (vponcova)
- Don't enter spokes after we leave the Summary hub (vponcova)
- network: rename Gtk cell renderer to prevent name collision (rvykydal)
- network: add unit tests for SecretsAgent (rvykydal)
- network: make SecretAgentDialog a bit more robust (rvykydal)
- network: move wireless secret agent bits into a separate file (rvykydal)
- Fix the logic for enabling latest updates (vponcova)
- Add better explanation what the `make admin user` means (#1803251) (jkonecny)
- Define the updates repositories in the Anaconda configuration files
  (#1642513) (vponcova)
- Migrate User spoke glade file to 3.38 version (jkonecny)
- network: migrate SecretAgent from python-dbus to dasbus (rvykydal)
- Translate spoke category title directly at runtime (mkolman)
- Add description and links for bug keyword searches (vslavik)
- Apply pylint excessive memory usage fix (mpitt)
- Set shorter workflow timeouts (mpitt)
- Fix issue when ns_info cannot be retrieved for NVDimm namespace (jkonecny)
- Allow encryption of thin logical volumes (vponcova)
- Fix error in initrd: shift count out of range (honza.stodola)

* Tue Nov 24 2020 Martin Kolman <mkolman@redhat.com> - 34.14-1
- Set workflow temp mail and user to GH actions rebase (jkonecny)
- Rebase test pull request also for rhel-8 contributors (jkonecny)
- Build Anaconda for ELN (jkonecny)
- Create the get_kernel_version_list function for the DNF payload (vponcova)
- Create the sort_kernel_version_list function (vponcova)
- Move the unit tests for the payload base utils to a new file (vponcova)
- Remove the duplicate code for kernel version lists (vponcova)
- Move the get_kernel_version_list function to the Live OS utilities (vponcova)
- network: do not use dialog for just single wireless connection to configure
  (rvykydal)
- Add the apply_specs function (vponcova)
- Add the get_installation_specs function (vponcova)
- Add the get_default_environment function (vponcova)
- Add the environments property to the DNF manager (vponcova)
- Set the RPM macros with an installation task (vponcova)
- network: fix configuration of wireless networks (rvykydal)
- Rebase branches to current master before testing (mpitt)
- network: use dialog instead of combobox to select wireless network (rvykydal)
- network: deal with obsolete ssid when configuring wireless (rvykydal)
- network: use function instead of assigned lambda in wireless activation
  (rvykydal)
- network: do not update wireless AP combo active item when not necessary
  (rvykydal)
- network: do not use obsolete access points in wireless configuration
  (rvykydal)
- Add upstream tag hint for Packit (jkonecny)
- Create an installation task for import of RPM keys (vponcova)
- Remove leftover bootloader-related code from the Payloads service (vponcova)
- Add workflow for daily RHEL COPR build (mpitt)
- Remove the storage logger (vponcova)
- Remove the loglevel option (vponcova)
- Remove the support for changing the log level (vponcova)
- Handle missing spice-vdagent (#1897153) (vponcova)
- rhbz#1888697 list important major languages (suanand)
- Run master tests on Fedora ELN (mpitt)
- Fix handling of empty $CI_TAG (mpitt)
- Skip blivet-gui tests on Fedora ELN (mpitt)
- Drop obsolete id: from validate workflow (mpitt)
- Create the get_download_size method (vponcova)
- Create the get_installation_size method (vponcova)
- Create the dump_configuration method (vponcova)
- Create the configure_base function (vponcova)
- Create the configure_proxy method (vponcova)
- Create an abstraction of the DNF base (vponcova)
- Create the configure_dnf_logging function (vponcova)
- Create the get_os_release_value function (vponcova)
- Create the get_product_release_version function (vponcova)
- Drop testing in mock (mpitt)
- Remove the method command (vslavik)
- Fix incomplete configuration of repositories loaded from treeinfo (#1745064)
  (honza.stodola)
- Fix checking ssl certificate for metadata (#1745064) (honza.stodola)
- Root password is mandatory if there is *not* admin user. (rvykydal)

* Thu Nov 12 2020 Martin Kolman <mkolman@redhat.com> - 34.13-1
- Skip add-on modules that failed to start (vponcova)
- Return the exit status of a Python module that failed to start (vponcova)
- Fix the priority of the ostreesetup kickstart command (#1896761) (vponcova)
- Drop obsolete dependency_solver.py script from rpm-tests (mpitt)
- Run a DBus task to configure FIPS on the installed system (vponcova)
- Run a DBus task to set up FIPS for the payload installation (vponcova)

* Thu Nov 12 2020 Martin Kolman <mkolman@redhat.com> - 34.12-1
- Use podman for pushing the nightly container update (mpitt)
- Robustify container-autoupdate workflow (mpitt)
- Disable seccomp profile when running containers on Ubuntu host (mpitt)
- Use podman in GitHub workflows (mpitt)
- Remove deviceprobe and install commands (vslavik)
- Change handling of UID and GID values (vslavik)
- Send UID and GID over D-Bus as UInt32 (vslavik)
- Correct limits for UIDs and GIDs in GUI (vslavik)
- Rename Subscription module tests (vslavik)
- Rename common module tests (vslavik)
- Rename Boss module tests (vslavik)
- Remove autostep functionality (vslavik)
- Don't include unknown files in the updates image (vponcova)
- Clean up the code for the platform-specific partitioning requirements
  (vponcova)
- Use a property for the platform-specific stage1 constraints (vponcova)
- Use a property for the stage1 device descriptions (vponcova)
- Use a property to provide a suggestion for the stage1 device (vponcova)
- Use a property to define non-linux format types (vponcova)
- Use a property to define platform-specific packages (vponcova)
- Do not fail user check job in rhel-8 validate workflow (jkonecny)
- Move the code that sets up the default disklabel type from platform.py
  (vponcova)
- Add unit tests for platform.py (vponcova)
- Revert "Standardize calls to parent via super()" in platform.py (#1858649)
  (vponcova)

* Thu Nov 05 2020 Martin Kolman <mkolman@redhat.com> - 34.11-1
- Fix user permission checking for rhel-8 validate task (jkonecny)
- Adjust rhel-8 log retrieval for changed container volume handling (mpitt)
- Don't clobber host checkout on `make container-ci` (mpitt)
- Drop anaconda-ci container entrypoint (mpitt)
- workflows: Add manual triggering of tests (mpitt)
- Fix and robustify validate workflow (mpitt)
- Mock os.stat in the unit tests (vponcova)
- Fix traceback when starting installation with inst.console (no args)
  (jkonecny)
- Add container image build badge (jkonecny)
- Rename our GH action for container build to a better name (jkonecny)
- Improve the documentation of inst.variant (vponcova)
- Add selinux=0 boot parameter when SELinux is set to disabled (#1882464)
  (omosnace)
- Clean up the Payload class (vponcova)
- Update the NVDIMM actions before we generate the output kickstart (vponcova)
- Make the storage available to the NVDIMM module (vponcova)
- Remove the execWithCaptureBinary function (vponcova)
- Remove unused getters from the Subscription spoke (vponcova)
- Remove an unused getter from the NetworkControlBox class (vponcova)
- Remove the URLType enum (vponcova)
- Remove the method_type property from the source classes (vponcova)
- Remove the subscription-related unused code (vponcova)
- Remove the DBus method GetPartitioned (vponcova)
- Remove the active attribute from the FSSet class (vponcova)
- Remove the short_label attribute from the BootLoaderImage class (vponcova)
- Remove the can_dual_boot attribute from the Bootloader class (vponcova)
- Remove the langcode_matches_locale function (vponcova)
- Remove unused properties from the GeocodingResult class (vponcova)
- Remove payload-related unused code (vponcova)
- Remove unused code (vponcova)
- kickstart.py: fix typo (kai.kang)
- Remove the debug flag (vponcova)
- Add workaround to fix support for installtree without repo (jkonecny)
- Build container image only if the container files changed (jkonecny)
- Names of signal handlers should have the on_ prefix (vponcova)
- Move UI test to a directory (vslavik)
- Move Storage module tests to directories (vslavik)
- Move Localization module tests to directory (vslavik)
- Change documentation - it's not required to build the container (jkonecny)
- Push also latest tag just for master container (jkonecny)
- Push new image only if unit tests went well (jkonecny)
- Add GH workflow to build and push master container to registry (jkonecny)
- Add anaconda-ci-push to Makefile to push container (jkonecny)
- Use our container registry to tag anaconda-ci container (jkonecny)
- Rename ci-tasks container to anaconda-ci (jkonecny)

* Fri Oct 23 2020 Martin Kolman <mkolman@redhat.com> - 34.10-1
- Move the code for the kernel package selection to new functions (vponcova)
- Remove the support for PAE (vponcova)
- Move Timezone module tests to a directory (vslavik)
- Move Subscription module tests to a directory (vslavik)
- Move Boss module tests to a directory (vslavik)
- Move common module tests to a directory (vslavik)
- Add directory for module tests (vslavik)
- Move UI tests to a directory (vslavik)
- Move core tests to directory (vslavik)
- Do not exclude English from available languages (vslavik)
- Add ELN support (sgallagh)
- Fix testing target branch instead of PR branch (jkonecny)
- Remove the old support for the requirements (vponcova)
- Move the code for the requirements of the DBus modules to the Boss module
  (vponcova)
- Move the requirements for FIPS to the Security module (vponcova)
- Move the code for the driver disk requirements to a new function (vponcova)
- Move the code for platform requirements to a new function (vponcova)
- Move the code for language requirements to new functions (vponcova)
- Remove the support for language groups (vponcova)
- Use constants for the types of requirements (vponcova)
- Move constants to prevent circular dependency (vslavik)
- Hardening of our GH action event trigger (jkonecny)
- network: handle None values of team configuration correctly (rvykydal)
- Verify RPM exists before running it (vslavik)
- Relabel the anaconda logs after copying them to the installed system
  (jstodola)
- post-scripts need to be sorted (honza.stodola)
- Fix ci-tasks container shell instructions (mpitt)
- Collect pylint and nosetests logs in validate workflow (mpitt)
- Clean up s390 partitioning check (#1855724) (vslavik)
- Show test-suite.log in validate workflow on failure (mpitt)
- More aggressive pylint downscaling (mpitt)
- Fix pylint downscaling (mpitt)
- fix “0 storage devices selected”abnormality (69908158+xqrustc2020)

* Wed Oct 14 2020 Martin Kolman <mkolman@redhat.com> - 34.9-1
- Add link to metacity enums schema (mpitt)
- Fix local tests run inside of container (jkonecny)
- Clean up the live image payload module (vponcova)
- Calculate required space from sources (vponcova)
- Provide the set-up and tear-down tasks of the live image source (vponcova)
- Use sources in the live image payload (vponcova)
- Create a DBus structure for the live image (vponcova)
- Create a basic file structure for the live image source (vponcova)
- Restrict pylint parallelism to available RAM (mpitt)
- Fix crash on nonexisting network config directories (mpitt)
- Allow running tests with docker (mpitt)
- Clean up container build/run rules and variables (mpitt)
- Robustify GitHub actions runner download in ci-tasks container (mpitt)
- Add variable for extra labels to GitHub action runner entry point (mpitt)
- Don't stop unit tests when the tests failed (jkonecny)
- Document possibility to run container tests without autotools (jkonecny)
- Make it possible to call make -f Makefile.am (jkonecny)
- Don't ignore the timezone kickstart command in the tests (vponcova)
- Run validate workflow in ci-tasks container (mpitt)
- Fix SECTION headers in docstrings (mpitt)
- Add GitHub actions runner to ci-tasks container (martin)
- Make it easier to run make commands (jkonecny)
- Remove support for the nfsiso: pseudo-protocol (vslavik)
- Fix formatting of contribution guidelines document (jkonecny)
- Fix missing space in Makefile (jkonecny)
- Add more options how to start the tests container (jkonecny)
- Fix dependency_solver to not require spec file for pip dependencies
  (jkonecny)
- Add container workflow to tests README file (jkonecny)
- Add Makefile target to run tests in container (jkonecny)
- Add Makefile target to build container (jkonecny)
- Add Dockerfile for anaconda unit-tests (jkonecny)
- Allow to format selected DASDs (vponcova)
- Test for wrong spellings of OSTree (vslavik)
- network: remove function that is not used anymore (rvykydal)
- network: do not create ifcfg files in initramfs (rvykydal)
- network: handle special binding for ifname= also when updating a connection
  (rvykydal)
- network: update comments in method for dumping default connections (rvykydal)
- network: update apply kickstart for everything applied in stage2 (rvykydal)
- network: remove task for consolidating of initramfs connections (rvykydal)
- network: remove task for setting real ONBOOT values (rvykydal)
- Run rpm tests in a GitHub action (martin)
- Separate RPM installability test from rpm_tests (martin)
- Define make targets for building source and binary rpms (martin)
- Drop superfluous build in `make run-rpm-tests-only` (martin)
- Fix spelling/name of OSTree (vslavik)
- Remove the inst.singlelang boot option (vslavik)
- Set up proxy environmental variables with a function (vponcova)
- Show in the first screen only translated locales (vslavik)
- Run unit tests in a GitHub action (martin)
- Mark the ostreesetup kickstart command as useless (vponcova)
- Use the RPM OSTree module in the UI (vponcova)
- Implement SetUpSourcesWithTask and TearDownSourcesWithTask (vponcova)
- Finalize the code that sets up and tear downs the RPM OS Tree source
  (vponcova)
- Improve the string representation of the RPM OSTree source (vponcova)
- Implement network_required of the RPM OSTree source (vponcova)
- Mock system operations in MountFilesystemsTask task (martin)
- Add missing "rpm-build" test dependency (martin)
- Add missing "make" BuildRequires (martin)
- Fix mock installation/usage instructions (martin)
- Fix nosetests name in tests/README.rst (martin)
- Fix tests/README.rst syntax (martin)
- Stop passing rd.{dm,md,lvm,luks}=0 in installer environment (awilliam)

* Thu Oct 01 2020 Martin Kolman <mkolman@redhat.com> - 34.8-1
- fix remove unkown partition in sda failed (69908158+xqrustc2020)
- Fix show missing inst. prefix warning appropriately (#1875561) (jkonecny)
- Fix unit test dependency installation for boolean expressions (martin)
- Drop obsolete Py_Initialize link check in configure (martin)
- Document the mount points of the target system (vponcova)
- fix remove unkown partition in sda failed (69908158+xqrustc2020)
- Import RPM certificates at end of installation (vslavik)

* Tue Sep 29 2020 Martin Kolman <mkolman@redhat.com> - 34.7-1
- Remove the Packages module (vponcova)
- Handle the %%packages section in the DNF module (vponcova)
- Create the DBus property Packages (vponcova)
- Create the DBus structure for the packages configuration (vponcova)
- network: commit changes synchronously when dumping autoconnections (rvykydal)
- Run the user instance of systemd (vponcova)
- network: do not bind virtual devices to mac (rvykydal)

* Fri Sep 25 2020 Martin Kolman <mkolman@redhat.com> - 34.6-1
- network: split add_and_activate_connection_sync function (rvykydal)
- network: add support for bridged bond to stage 2 kickstart (%%pre) (rvykydal)
- Never mount partitions on a disk with the iso9660 filesystem (vponcova)
- packit: use tar-pax instead of tar-ustar (ttomecek)
- Change default Packit jobs (#1697339) (jkonecny)
- Enable Packit for Anaconda (#1697339) (jkonecny)
- Change text on the Reset All button in custom part. (vslavik)
- Add a rule for translated strings to code conventions (#1619530) (vponcova)
- Never convert translated strings to uppercase (vponcova)
- Never change first letters of translated strings to uppercase (vponcova)
- network: update docstring of clone_connection_async (rvykydal)
- network: add support for vlan over bond to stage 2 kickstart (pre) (rvykydal)
- Move the execute method of the logging command (vponcova)

* Thu Sep 17 2020 Martin Kolman <mkolman@redhat.com> - 34.5-1
- Fix the combo box for an URL type of additional repositories (#1879127)
  (vponcova)
- Add DBus support for the ostreesetup kickstart command (vponcova)
- Create the structure for RPM OSTree configuration (vponcova)
- Create the RPM OSTree source module (vponcova)
- Create the RPM OSTree module (vponcova)
- network: clone connections from intramfs to persistent config (rvykydal)
- network: set addr-gen-mode of Anaconda default connections to eui64
  (rvykydal)
- network: default to addr-gen-mode eui64 (rvykydal)
- network: do not reset ipv6.addr-gen-mode in tui network configuration
  (rvykydal)
- network: get hwadddr when binding to mac more robustly (rvykydal)
- Improve the error dialog for storage reset (vponcova)
- Remove the needs_storage_configuration property (vponcova)
- Remove the is_hmc_enabled property (vponcova)
- Remove the install_device attribute (vponcova)
- Move the proxy property to the base payload class (vponcova)
- Fix CDN button visibility (mkolman)
- subscription: Assure payload restart on DVD install after registration
  (mkolman)
- Remove the handles_bootloader_configuration property (vponcova)
- Run the CreateBLSEntriesTask task (vponcova)
- Add the CreateBLSEntriesTask task (vponcova)
- Call the DBus method InstallBootloaderWithTasks (vponcova)
- Add the CreateRescueImagesTask task (vponcova)
- Call the DBus method GenerateInitramfsWithTasks (vponcova)
- Add the RecreateInitrdsTask task (vponcova)
- network: set addr-gen-mode of Anaconda default connections to eui64
  (rvykydal)
- network: default to addr-gen-mode eui64 (rvykydal)
- network: do not reset ipv6.addr-gen-mode in tui network configuration
  (rvykydal)
- network: get hwadddr when binding to mac more robustly (rvykydal)
- subscription: Only restart payload when needed (mkolman)
- Document the restart_payload argument of subscription helper functions
  (mkolman)
- network: fix missing log message argument (rvykydal)
- Propagate verify_ssl to RHSM (mkolman)
- Check if original partitions are mounted, too (vslavik)
- network: do not add superfluous quotes to inst.dhcpclass identifier
  (rvykydal)
- Add the DBus method IsDeviceShrinkable (#1875677) (vponcova)
- Show warning message when entered size is not valid (vslavik)
- Extend unit tests for generate_device_factory_request (vponcova)
- Differentiate between RAID levels of a device and its container (vponcova)
- Don't generate container data for non-container device types (vponcova)
- network: fix parsing of hostname from ip= if mac is defined in dhcp
  (rvykydal)
- network: fix inst.dhcpclass boot option (rvykydal)
- Do not push pot files just tell user that he should update (jkonecny)
- Add support for booting installation media with plain SquashFS (bkhomuts)
- Do not check ro mount in Dracut for overlay (jkonecny)
- network: apply kickstart network --nodefroute also from stage2 (rvykydal)
- list major common keyboard layouts first (suanand)

* Mon Sep 07 2020 Martin Kolman <mkolman@redhat.com> - 34.4-1
- Apply onboot policy even when network was configured in UI. (rvykydal)
- network: fix kickstart network --dhcpclass option (rvykydal)
- network: use constants instead of enum to hold stirng values of connection
  type (rvykydal)
- network: fix using of values of NMConnectionType enum (rvykydal)
- Always clear treeinfo metadata (#1872056) (jkonecny)
- Do not check ro mount in Dracut for overlay (jkonecny)
- Propagate a lazy proxy of the storage model (vponcova)
- Add TODO to check if biospart support is required for DUD (jkonecny)
- Remove failure messages about not supported biospart (jkonecny)
- Switch to a new HardDrive command version with removed biospart (jkonecny)
- Make custom storage summary dialog resizeable (1626555) (mkolman)
- network: add constants for NM connection types (rvykydal)
- Recognize systemd.unit=anaconda.target in anaconda-generator (m.novosyolov)
- The underline character should not be displayed (honza.stodola)
- network: create default connection also for slave devices (rvykydal)
- network: remove ONBOOT hack for slave connections (rvykydal)
- network: replace ifcfg module with config_file module (rvykydal)
- network: remove unused functions from ifcfg module (rvykydal)
- network: generate kickstart via NM API (connections) (rvykydal)
- network: get master slaves via NM API (rvykydal)
- network: use NM API to look for config files for DeviceConfigurations
  (rvykydal)
- network: use NM API to look for config files when setting final ONBOOT
  (rvykydal)
- network: use NM API to look for config files when setting real ONBOOT
  (rvykydal)
- network: use NM API to look for config files when applying kickstart
  (rvykydal)
- network: use NM API to look for config files when consolidating connections
  (rvykydal)
- network: check for missing device config via NM api (rvykydal)
- network: use underscore in the names of slave devices created from kickstart
  (rvykydal)
- network: log also content of keyfiles (rvykydal)
- We won't support inst.ks=bd: (jkonecny)
- network: do not enforce network standalone spoke on default source (rvykydal)

* Tue Sep 01 2020 Martin Kolman <mkolman@redhat.com> - 34.3-1
- Move slower part of Subscription spoke initialization to a thread (mkolman)
- Add test to detect every RW mount command in Dracut (jkonecny)
- subscription: Convert the RHSM default config values to expected format
  (mkolman)
- Implement get_source_proxy() in payload base class (mkolman)
- Use spec file macros for all requires version specifications (jkonecny)
- Fix spec macro for version name (jkonecny)
- Correctly work with package boolean logic in our setup scripts (jkonecny)
- Wait for payload initialization to finish in Subscription spoke (mkolman)
- Unify usage of BootLoaderArguments add() & update() (vslavik)
- Rename Arguments to BootLoaderArguments (vslavik)
- Remove usage of OrderedSet (vslavik)
- Add tests for the boot loader Arguments class (vslavik)
- Do not mount as RW in Dracut (jkonecny)
- network: do not crash when updating a connection without wired settings
  (rvykydal)
- Fix traceback when removing additional repository (jkonecny)
- subscription: Handle cases where CDN should not be the default (mkolman)
- subscription: Set DNF payload source via config file option (mkolman)
- subscription: Manual CDN selection support (mkolman)
- subscription: Handle source switching at registration/unregistration
  (mkolman)
- subscription: Introduce the default_source configuration option (mkolman)
- Use "raise from" to link exceptions (vslavik)
- Fix branching documentation (mkolman)
- Change keyboard ordering to US layout first, 'native' second. Resolves:
  rhbz#1039185 (suanand)
- Remove docs where we tell users that inst. prefix is not required (jkonecny)
- Print warning for boot options without inst. prefix (jkonecny)
- Add missing dracut commands as missing inst. prefix warning (jkonecny)
- Enable warning when inst. prefix is not used (jkonecny)
- Reset the state of the custom partitioning spoke (vponcova)
- Reset the RAID level of the device request (#1828092) (vponcova)
- Protect all devices with the iso9660 file system (vponcova)
- Don't ignore NVDIMM devices with the iso9660 file system (vponcova)
- Add tests for the DBus method FindOpticalMedia (vponcova)
- Fix everything in payload should be mounted as read only (jkonecny)
- Add support for mount options to device_tree.MountDevice (jkonecny)
- Adapt tests for CDRom for the new inst.stage2 discovery (jkonecny)
- CDRom source should prioritize stage2 device during discover (jkonecny)

* Fri Aug 21 2020 Martin Kolman <mkolman@redhat.com> - 34.2-1
- Fix dependency_solver failure with spec file boolean logic syntax (jkonecny)
- Avoid unnecessarily pulling in glibc-langpack-en (sgallagh)
- Set up the ignored_device_names variable (vponcova)

* Thu Aug 20 2020 Martin Kolman <mkolman@redhat.com> - 34.1-1
- network: do not try to activate connection that has not been found (rvykydal)
- network: add timeout for synchronous activation of a connection (rvykydal)
- network: fix configuration of virtual devices by boot options (rvykydal)
- Handle exceptions from threads without new instances (vslavik)
- Do not use disabled --install-scripts command of pip (jkonecny)
- Use bootlist command to update the PowerPC-64 Boot Order (javierm)
- Discard current boot list when updating the boot-device NRVAM variable
  (javierm)
- Automatically break lines in labels in software selection spoke (vslavik)
- Set up FIPS in the target system (vponcova)
- Update the service anaconda-sshd (vponcova)
- Set up FIPS in the installation environment (vponcova)
- Add Blivet version to generated kickstart (vslavik)
- Add Anaconda version to saved kickstart (vslavik)
- Fix kickstart file error with user groups (kai.kang)
- Get rid of add_disable_repo (jkonecny)
- Move parts together in the DNF repo (jkonecny)
- Fix issue that treeinfo repositories were never disabled (jkonecny)
- Keep treeinfo repositories disabled after payload reset (jkonecny)
- Fix crash on first entering of source spoke (jkonecny)
- Remove treeinfo repositories instead of disabling (jkonecny)
- Reload treeinfo repositories on every payload reset (jkonecny)

* Mon Aug 10 2020 Martin Kolman <mkolman@redhat.com> - 33.25-1
- Fix our tests with a newer rpmfluff library (jkonecny)
- network: pass also keyfile NM configuration to target system (#1858439)
  (rvykydal)
- Unify the indentation in the Anaconda configuration files (vponcova)
- Remove the DBus method ConfigureNTPServiceEnablementWithTask (vponcova)
- Create ssh user using only existing fields (#1860058) (vslavik)
- Fix the position of the info bar in standalone spokes (vponcova)
- Add the function is_service_installed (vponcova)
- Drop the dependency on python3-ntplib (vponcova)
- Remove Blivet's tests (vponcova)
- Remove gui tests (vponcova)
- Generate the coverage report for tests (vponcova)
- Fix the util tests (vponcova)
- Simplify the regex tests (vponcova)
- Fix the module tests (vponcova)
- Clean up the driver tests (vponcova)
- Fix the kickstart dispatcher tests (vponcova)
- Fix the localization tests (vponcova)
- drop workarounds for the TLS exhaustion issue on aarch64 and ppc64le (dan)

* Fri Jul 31 2020 Martin Kolman <mkolman@redhat.com> - 33.24-1
- Run actions of the Resize dialog in the reversed order (#1856496) (vponcova)
- Reset repositories from the main thread (vponcova)
- Initialize the closest mirror from the main thread (vponcova)
- Remove the mirrors_available property (vponcova)
- Rename ActivateFilesystemsTask (vponcova)
- Document the Anaconda configuration files (vponcova)
- Remove the encrypted attribute (vponcova)
- subscription: Fix rhsm --proxy kickstart command usage with no username
  specified (mkolman)
- subscription: Fix RHSM HTTP proxy configuration crash in the GUI (mkolman)
- Log the information about the original exception (vponcova)
- Update the documentation of the Anaconda sysconfig file (vponcova)
- Make spoke tiles stack more tightly (vslavik)
- Add NTS support to time sources in GUI (mlichvar)
- Add connection test for NTS (mlichvar)
- Parse NTP server options from config file (mlichvar)
- Run bash instead of sh in rescue mode (vslavik)

* Thu Jul 16 2020 Martin Kolman <mkolman@redhat.com> - 33.23-1
- Mangle Fedora IoT Edition product identifier to "Fedora-IoT" (ngompa13)
- Fix creating cached LVs on encrypted PVs (vtrefny)
- Add Fedora IoT product override (ngompa13)

* Tue Jul 14 2020 Martin Kolman <mkolman@redhat.com> - 33.22-1
- Add support for the timesource kickstart command (vponcova)
- Use the structure for time sources in GUI (vponcova)
- Use the structure for time sources in TUI (vponcova)
- Add support for generating a summary of the NTP servers (vponcova)
- Add support for the NTP server status cache (vponcova)
- Use the structure for time sources in network.py (vponcova)
- Use the structure for time sources in anaconda.py (vponcova)
- Use the structure for time sources in the Timezone module (vponcova)
- Use the structure for time sources in ntp.py (vponcova)
- Create a new DBus structure for time sources (vponcova)
- Replace the zram service (vponcova)
- Fix software spoke message when source changes (mkolman)
- ostree: set rootflags when installing on btrfs (#1753485) (dcavalca)
- Only pass one initrd image to kexec (javierm)
- Prevent crash on unregistration (mkolman)
- Add LVM with inconsistent sector size disks to common bugs (jkonecny)
- Don't create swap by default (vponcova)
- Don't require fcoe-utils (vponcova)
- Temporarily ignore the new timezone kickstart command (vponcova)
- Schedule timed actions with the right selector (#1851647) (vponcova)
- Reconfigure DNF payload after options are set (vslavik)
- Fix displaying of empty software group description (rvykydal)
- Fix passing of arguments when creating dracut arguments for FCoE (rvykydal)
- network: fix obtaining of s390 options of a wired connection (rvykydal)
- Exclude stderr from returned output when executing powerpc-utils tools
  (javierm)
- Fix imports of Blivet-GUI in unit tests (vponcova)
- Don't mount DBus sources at /run/install/source (vponcova)
- Always specify the boot disk (vponcova)
- Create the initial storage model during the initialization (vponcova)
- Use LUKSDevice.raw_device instead of LUKSDevice.slave (vtrefny)
- Use modinfo to check ko before modprobe (t.feng94)
- Fix EFI bootloader install (#1575957) (butirsky)

* Wed Jul 08 2020 Martin Kolman <mkolman@redhat.com> - 33.21-1
- Use Btrfs for all Fedora variants installed by Anaconda except Server
  (ngompa13)
- Remove the support for language filtering (vponcova)
- Remove the support for locale filtering (vponcova)
- Don't override the eula command with the same command (vponcova)
- Improve logs for validation of stage1 and stage2 devices (vponcova)
- Document an issue with invalid partitioning in the output kickstart file
  (vponcova)
- Remove support for check_supported_locales (vponcova)
- Remove the support for Fedora Atomic Host (vponcova)
- Move Subscription spoke under Software (vslavik)
- Update the function get_default_partitioning (vponcova)
- Update the property default_partitioning (vponcova)
- Change the default_partitioning option (vponcova)
- Fix hiding of network device activation switch (#1847493) (rvykydal)
- Typo fix (sh.yaron)

* Mon Jun 22 2020 Martin Kolman <mkolman@redhat.com> - 33.20-1
- Add test for NFS URL with ISO in path (#1848718) (jkonecny)
- Fix issue when NFS path is pointing directly to ISO (#1848718) (jkonecny)
- Rename function for a simple check for DNF repository (jkonecny)
- Add tests for verify_valid_installtree function (#1844287) (jkonecny)
- Move verify_valid_installtree to source module utils (#1844287) (jkonecny)
- Do not test if repo is valid based on .treeinfo file (#1844287) (jkonecny)
- Relabel whole /etc instead of only some parts (vslavik)
- Clean up lists of files and directories to relabel (vslavik)
- Use allowlist and blocklist in the Anaconda configuration file (vponcova)
- Correctly set up the LUKS version when we click on a mount point (#1689699)
  (vponcova)
- Fix the mock function for DBus.get_proxy (vponcova)
- Fix the mock function for DBus.get_proxy (vponcova)
- Simplify the workaround for the RHSM configuration proxy (vponcova)
- Show pylint version in logs (vslavik)
- Don't use the private attribute for a message bus (vponcova)
- Ignore unknown variable (vslavik)
- Split storage spoke dialogs to a separate module (vslavik)
- Fix more SElinux contexts (vslavik)
- Fix regression reading kernel list when collecting configurations (#1846156)
  (jkonecny)

* Mon Jun 15 2020 Martin Kolman <mkolman@redhat.com> - 33.19-1
- Document common issues and bugs (vponcova)
- Add logging messages to %%post scripts (vslavik)
- Don't prompt the user to ssh in VNC installations (vponcova)
- Extend the function prompt_for_ssh (vponcova)
- Allow having /boot on a btrfs volume (i.gnatenko.brain)
- network: do not parse IPADDR0 anymore (rvykydal)
- Do not use kwargs when creating network_data from ifcfg file (rvykydal)
- Extend unit tests for generating network data from ifcfg file (rvykydal)
- Fix updating of user gid/uid value checkbox in gui (rvykydal)
- Fix crash on user uid/gid unchecked in gui (rvykydal)
- Add daily build status badge (jkonecny)
- Fix the pylint warning in the Payloads module (vponcova)
- Add pointer to kickstart tests to tests README (rvykydal)
- resolved a user created password verification issue that could not exit
  (57519382+huzunhao)
- Don't use data.method.proxy (vponcova)
- Use sshd_config drop in directory to allow root login (jjelen)
- localization: do not crash on failed parsing of X layout (#1836047)
  (rvykydal)
- Catch Blivet's exceptions when we reset a device (#1843278) (vponcova)
- Fix wireless network configuration on get_ssid() returning None (#1838357)
  (rvykydal)
- Unify definition of directory for ifname and prefixdevname config (rvykydal)
- Use constants when mocking paths for network installation test (rvykydal)
- Create /etc/systemd/network dir for ifname= renaming if needed. (rvykydal)
- Use the Blivet's property is_empty (vponcova)

* Wed Jun 03 2020 Martin Kolman <mkolman@redhat.com> - 33.18-1
- Set up LD_PRELOAD for the Payloads module (vponcova)
- Extend the start-module script (vponcova)
- subscription: Fix authentication method switching in GUI (mkolman)
- subscription: Make sure CDN repos are loaded and usable (mkolman)
- Add NFS ISO support back to the NFS SetupSourceTask (jkonecny)
- Add NFS ISO support to the NFSSourceModule (jkonecny)
- Tear down HDD device mount if no valid installation source is found
  (jkonecny)
- Extract ISO find algorith from harddrive (jkonecny)

* Mon Jun 01 2020 Martin Kolman <mkolman@redhat.com> - 33.17-1
- Update required ack in makebumpver script for rhel > 7 (rvykydal)
- Close responses from session.get (vponcova)
- Improve the documentation of the SetUpMountTask class (vponcova)
- Raise an exception if the source's mount point is not unmounted (vponcova)
- Change the default source to CDROM (vponcova)
- Don't set up sources in the refresh method of the Source spoke (vponcova)
- Make cppcheck ignore the G_DEFINE_TYPE macros (vslavik)
- Fix issue that unified ISO from URL is not loaded (jkonecny)
- Add split_protocol payload helper function (jkonecny)
- Fix string based on translator comments (vslavik)

* Mon May 25 2020 Martin Kolman <mkolman@redhat.com> - 33.16-1
- subscription: Only require Insights package if subscribed (mkolman)
- subscription: Do not pass payload to unregister() helper function (mkolman)
- subscription: Fix typos related to ParseAttachedSubscriptions task (mkolman)
- subscription: Make sure /etc/yum.repos.d exists (mkolman)
- subscription: Fix disconnect() for RHSM observer (mkolman)
- subscription: Fix SystemPurposeData equality checking (mkolman)
- subscription: Set RHSM configuration before registration attempt (mkolman)
- subscription: Initial CDN source switching (mkolman)
- subscription: Fix Insights configuration in GUI (mkolman)
- subscription: Fix setting username to SubscriptionRequest in GUI (mkolman)
- Change connection flags for the RHSM private bus (vponcova)
- Create a proxy of the RHSM Config object for a specific interface (vponcova)
- Skip the btrfs command if deprecated (vponcova)
- Use a specific kickstart version in handle-sshpw (vponcova)
- Avoid concatenation of iso name twice (jkonecny)
- Do not mount harddrive sources as RO (jkonecny)
- Fix the access to a DBus proxy of the Subscription module (vponcova)
- Set up LANG for tests (vponcova)
- Resolve traceback when HDD ISO is not found (jkonecny)
- Don't set up the HMC source again (vponcova)
- Remove the changed property of the Source spoke in GUI (vponcova)
- Specify the default source type for the DNF payload (vponcova)
- Support all source types based on repo files (vponcova)
- Use the closest mirror source in UI (vponcova)
- Add a new source for the closest mirror (vponcova)
- Change the description of the repo files source (vponcova)
- Fix adding to the protected devices list (jkonecny)
- Remove not used API of dnf payload (jkonecny)
- Rename GetISOPath to GetIsoPath which is correct API name (jkonecny)
- Fix python3 requires in spec file (rvykydal)
- Use the source proxy to get the device name (vponcova)
- Collect package requirements of the Subscription module (vponcova)
- Add ignored field to rpm_tests (rvykydal)
- Require subscription manager on rhel (rvykydal)
- Remove the property is_iso_mounted (vponcova)
- Run the set-up tasks of sources with signals enabled (vponcova)
- Set default url type combobox value (jkonecny)
- Fix lang_locale_handler have payload property from parents (jkonecny)
- Remove kickstart sources from GUI (vponcova)
- Remove kickstart sources from TUI (vponcova)
- Log the result of the HDD set-up task (vponcova)
- Always try to unmount the HDD ISO (vponcova)
- Fix typo resulting to use mirrorlist instead of metalink (jkonecny)
- Handle DBus errors of the task returned by SetUpSourcesWithTask (vponcova)
- Remove useless attributes from the class Anaconda (vponcova)
- Remove kickstart sources from anaconda.py (vponcova)
- Remove kickstart sources from the class DNFPayload (vponcova)
- Call nose python module instead of nosetests binary (jkonecny)
- root spoke: set value of root ssh login checkbox from module (rvykydal)
- users module: fix check of existence of admin user (rvykydal)
- Always clear kickstarted status for GUI time&date spoke (vslavik)
- Always protect CD-ROM devices (vponcova)
- Fix the DBus task that sets up the SE/HMC source (vponcova)
- Move lxml test dependency from pip to RPM (jkonecny)
- subscription: Show data about attached subscriptions (mkolman)
- Setup RHEL rebuilds to exclude
  org.fedoraproject.Anaconda.Modules.Subscription (riehecky)
- Tear down sources before setting new one in SourceSwitchHandler (jkonecny)
- Remove unused properties from SourceSwitchHandler (jkonecny)
- Migrate set Closest mirror of SourceSwitchHandler (jkonecny)
- Migrate set HMC of SourceSwitchHandler to source modules (jkonecny)
- Migrate set CDROM of SourceSwitchHandler to source modules (jkonecny)
- Migrate set NFS of SourceSwitchHandler to source modules (jkonecny)
- Migrate set URL of SourceSwitchhandler to source modules (jkonecny)
- Implement the DBus methods SetUpSourcesWithTask and TearDownSourcesWithTask
  (vponcova)
- Move removal of blivet-gui in rhel upstream (rvykydal)
- Migrate set HDD of SourceSwitchHandler to source modules (jkonecny)
- Migrate SourceSwitchHandler to use module for cleanups (jkonecny)
- Add payload property to SourceSwitchHandler (jkonecny)
- Avoid imports from blivet.devicefactory (vponcova)
- Mark kickstart commands of RPM sources as useless (vponcova)
- Generate kickstart from the Payloads module (vponcova)

* Tue May 19 2020 Martin Kolman <mkolman@redhat.com> - 33.15-1
- Update the bootloader configuration after live installation (javierm)
- subscription: Registration button sensitivity handling (mkolman)
- subscription: Make credential checking functions usable in GUI (mkolman)
- Add exclude to the dependency_solver (jkonecny)
- Add the method is_complete to the class DNFPayload (vponcova)
- Add the property source_type to the class DNFPayload (vponcova)
- Add the method get_source_proxy to the class DNFPayload (vponcova)
- Fix call to super() with missing parameters (vslavik)
- Change string according to translator comments (vslavik)
- Remove gjs dependency exclude which is no more needed with anaconda-live
  (rvykydal)
- Remove sphinx test dependency (jkonecny)
- Extend the objects for parsing the cmdline installation method (vponcova)
- Add functions to set up and tear down of DBus sources (vponcova)
- Switch call of pip3 to python3 -m pip (jkonecny)
- Move for_publication as second method in sources (jkonecny)
- Move sources private methods on top of the file (jkonecny)
- Fix RPMSourceMixin class documentation (jkonecny)
- Switch MountingSourceBase to MountingSourceMixin (jkonecny)
- Remove tear_down_with_tasks from MountingSourceBase (jkonecny)
- Do not implement get_state in MountingSourceBase (jkonecny)
- Change gui test relative imports to absolute (vslavik)
- Disable spurious pylint warning (vslavik)
- Add CDN source (vslavik)
- Test the DBus method IsNetworkRequired (vponcova)
- Add the DBus method IsNetworkRequired (vponcova)
- Detect HTTPS as a protocol that requires the network (michel)
- Remove unused variable (vslavik)

* Thu May 14 2020 Martin Kolman <mkolman@redhat.com> - 33.14-1
- subscription: Hook up state update methods (mkolman)
- subscription: Make it possible to register/unregister from the GUI (mkolman)
- subscription: Register & subscribe during automated installation (mkolman)
- subscription: Add asynchronous registration helper functions (mkolman)
- subscription: Add IsRegistered property (mkolman)
- Add functions for DBus sources (vponcova)
- Implement DeviceName API for CDrom payload source (jkonecny)
- Return device name from SetUpCdromSourceTask (jkonecny)
- Add GetISOPath HardDrive payload source API (jkonecny)
- subscription: Add the ParseAttachedSubscriptionsTask (mkolman)
- Add new Hard drive source property to tell that iso is used (jkonecny)
- Change return of SetUpHardDriveSourceTask (jkonecny)
- Add __repr__ to payload sources (vslavik)
- Create a DBus proxy of the DNF module (vponcova)
- Work around pylint 2.5.0 issue with _ in warning id (vslavik)
- subscription: Add network connectivity check to the Subscription spoke
  (mkolman)
- Split find_and_mount_iso_image source helper func (jkonecny)
- subscription: Add main Subscription spoke structure (mkolman)
- Add the DBus method ActivatePayload (vponcova)
- Add the DBus property CreatedPayloads (vponcova)
- Replace the DBus method GetActivePayload with a property (vponcova)
- subscription: Add helper functions for Subscription spoke (mkolman)
- Remove the DBus method IsPayloadSet (vponcova)
- subscription: Add glade file for Subscription spoke (mkolman)
- subscription: Simplify system purpose configuration (mkolman)
- subscription: Implement equality testing for SystemPurposeData (mkolman)
- subscription: Add check_system_purpose_set() helper function (mkolman)
- Add generate_repo_configuration for URL payload source (jkonecny)
- Add gererate_repo_configuration for all mount sources (jkonecny)
- Add GetRepoConfigurations API for DNF payload (jkonecny)
- Create ABC class declaring interface for RPM sources (jkonecny)
- Add the combo box for choosing a LUKS version in the container dialog
  (#1714120) (vponcova)
- Use the combo box for choosing a LUKS version only for encrypted devices
  (vponcova)
- Provide the LUKS version of the encrypted container (vponcova)
- Add the function set_container_data (vponcova)

* Thu May 07 2020 Martin Kolman <mkolman@redhat.com> - 33.13-1
- Remove a missed use of has_source() to fix tests (vslavik)
- Change string to new format (vslavik)
- Add DBus property Description for all sources (vslavik)
- subscription: Add AttachedSubscription DBus structure (mkolman)
- Pre-select disk initialization mode in TUI (honza.stodola)
- Remove the HasSource D-Bus function (vslavik)
- Add kickstart support to URL payload source (jkonecny)
- Add NFS source kickstart support (jkonecny)
- Add function to create NFS from components (jkonecny)
- Move ProxyString to core.payload (jkonecny)
- Move parse_nfs_url to the new core/payload file (jkonecny)
- Fail on harddrive --biospart in HDD payload source (jkonecny)
- Add kickstart support for HDD payload source (jkonecny)
- Add SE/HMC payload source kickstart support (jkonecny)
- Add CDROM payload source kickstart support (jkonecny)
- Pick HMC as the last DNF source when processing KS data (jkonecny)
- Add DNF module kickstart processing for sources (jkonecny)
- subscription: Run installation tasks of the Subscription module (mkolman)
- subscription: Add is_module_available() utility function (mkolman)
- Ignore the required package dmraid in RHEL (honza.stodola)
- subscription: Attach subscription task (mkolman)
- subscription: Add unregistration task (mkolman)
- Activate the set/remove buttons in the "Select disks and boot loader" window
  only when a disk is selected (honza.stodola)
- Properly update UI after removing the boot device (honza.stodola)
- Do not offer disk selection when encrypting existing partition
  (honza.stodola)
- Destroy the disk selection dialog on escape (honza.stodola)
- Add the DBus method GetModules to the Boss service (vponcova)
- subscription: Fix registration tasks docstring typo (mkolman)
- Add payload source __repr__ support to improve logging (jkonecny)
- Fix calling payloads service with empty kickstart (jkonecny)
- Rename check_set_sources to set_and_check_sources (jkonecny)
- Create two parts of the set_check_sources payload test (jkonecny)
- Add payload base add_source() module scope API (jkonecny)
- Fix payload log message (jkonecny)
- Add new commands for DNF payload recognition (jkonecny)
- Disable %%packages from DNF module (jkonecny)
- Add new supported sources to DNF payload (jkonecny)
- Add kickstart commands for DNF payload (jkonecny)
- Use new F33 Repo command from pykickstart (jkonecny)
- subscription: Add subscription related package requirements (mkolman)
- subscription: Add registration tasks (mkolman)
- subscription: Add RegistrationError exception (mkolman)
- network: don't try to use DeviceConfigurations on live cd (#1827999)
  (rvykydal)
- subscription: Add TransferSubscriptionTokensTask (mkolman)
- subscription: Add RestoreRHSMLogLevelTask (mkolman)

* Wed Apr 29 2020 Martin Kolman <mkolman@redhat.com> - 33.12-1
- Add tests for ReadKickstart (vponcova)
- Remove pyanaconda.storage (vponcova)
- Move the initialization functions from pyanaconda.storage (vponcova)
- Move create_storage from pyanaconda.storage (vponcova)
- Move the model from pyanaconda.storage (vponcova)
- Move the utils from pyanaconda.storage (vponcova)
- Move the installation functions from pyanaconda.storage (vponcova)
- Move the storage checker from pyanaconda.storage (vponcova)
- Move pyanaconda.platform (vponcova)
- Move PartSpec from pyanaconda.storage (vponcova)
- Don't use pyanaconda.platform in UI (vponcova)
- Separate the "Reset All" button from the edge of the screen (honza.stodola)
- Fix the warning messages from ReadKickstart (vponcova)
- Unify module source test variable names (vslavik)
- Add resolv.conf to log-capture (riehecky)
- Reload NTP server list in dialog on every run (vslavik)
- Fix the line number in the kickstart message data (vponcova)
- Remove TODO to solve is_ready for payload sources (jkonecny)
- Use the new task class with the harddrive source (vslavik)
- Detect the live OS image automatically (vponcova)
- Add constants for the source types (vponcova)
- Exclude liveimg from the kickstart command method (vponcova)
- Access the kickstart command liveimg directly (vponcova)
- Create a base class for live payloads (vponcova)
- Remove pyanaconda.payload.livepayload (vponcova)
- Run %%onerror and %%traceback scripts for all types of exceptions (vponcova)
- gui source spoke: fix the key used to check proxy for additional repo
  (rvykydal)
- Respect changesok password policy for root password (#1584145) (rvykydal)
- rootpw gui: make root spoke insensitive if rootpw is set in ks (#1584145)
  (rvykydal)
- subscription: RHSM runtime configuration support (mkolman)
- Move the bootloader-related code to the module (vponcova)
- Add the is_ready method to the Payload class (vponcova)
- Rename NOT_SUPPORTED to NOT_APPLICABLE (jkonecny)
- subscription: Add missing declaration for rhsm_observer property (mkolman)
- subscription: Fixup a docstring (mkolman)
- Remove payload tests for empty sources (jkonecny)
- Improve HDD payload source test (jkonecny)
- Change tests for new payload ready states (jkonecny)
- Use new source states in payload sources (jkonecny)
- Create source state enum (jkonecny)
- date time gui: no empty space in combo for day and month selection (#1823130)
  (rvykydal)
- Reset the partitioning of Blivet-GUI (#1826286) (vponcova)
- Remove the logic with sources from the network standalone spoke (vponcova)
- Move remaining DNF-related code to the DNF payload (vponcova)
- subscription: Add SystemPurposeConfigurationTask (mkolman)
- Rename payload source is_ready to get_state (jkonecny)
- Remove the tip about the user name (#1823015) (vponcova)
- Add payload base tests (jkonecny)
- Improve payload shared test source creation (jkonecny)
- Fix exception string when incompatible payload source (jkonecny)
- Translate names of OS installations on demand (#1823126) (vponcova)
- subscription: Add helper function to SystemPurposeData DBus structure
  (mkolman)
- network tui: fix getting of network device configurations (#1823011)
  (rvykydal)

* Tue Apr 21 2020 Martin Kolman <mkolman@redhat.com> - 33.11-1
- Reset the partitioning of Blivet-GUI (#1826286) (vponcova)
- Fix the validation of a device label (#1823221) (vponcova)
- Use the new base classes in sources (vslavik)
- Add base classes for mounting sources (vslavik)
- Add test if the spokes ordering is correct (jkonecny)
- Fix ordering of spokes with the same priority (jkonecny)
- Fix TUI Kernel and Unsupported HW spokes ordering (jkonecny)
- Switch collecting & ordering action classes to static (jkonecny)
- Add TUI/GUI tests for standalone spokes priority (jkonecny)
- Use join_paths instead of os.path.join in sources (vslavik)
- Get ui/__init__.py closer to pep8 (jkonecny)
- Allow to remove incomplete devices (#1823232) (vponcova)
- subscription: RHSMObserver & StartRHSMTask (mkolman)
- Make sure that the summary button is really hidden (#1823467) (vponcova)
- Use default priority in the GUI spokes (jkonecny)
- Fix TUI spokes priorities (jkonecny)
- Add back default priority for standalone spokes (jkonecny)
- subscription: Add initial RHSM DBus API identifiers (mkolman)
- Install scripts at /usr/bin (vponcova)
- Remove mock from the test dependencies (vponcova)
- Install test dependencies from pip when possible (vponcova)
- Fix the indentation of the test dependencies (vponcova)
- Expand the selector with swap (#1823127) (vponcova)
- Fix default value for pwpolicy emptyok (#1664704) (mkolman)
- Only quit GTK mainloop on GUI quit request (#1643111) (mkolman)
- Print correct message if no linux partitions were found in rescue mode
  (#1823222) (honza.stodola)
- Use black color for errors in bottom bar (#1823004) (honza.stodola)

* Thu Apr 16 2020 Martin Kolman <mkolman@redhat.com> - 33.10-1
- subscription: Implement install_with_tasks() method (mkolman)
- subscription: Add the IsSubscriptionAttached property (mkolman)
- subscription: Add ConnectToInsights task (mkolman)
- Create product configuration files for Red Hat Virtualization (vponcova)
- Create the configuration section Storage Constraints (vponcova)
- Extend tests for the default storage checker (vponcova)
- Represent the constraint STORAGE_MIN_RAM by an instance of Size (vponcova)
- Remove the constraint STORAGE_MIN_ROOT (vponcova)
- Extend support for custom storage checking (vponcova)
- Add a new type of the default partitioning for virtualizations (vponcova)
- Add the configuration option default_scheme (vponcova)
- Add the configuration option help_directory (vponcova)
- Accept `harddrive --dir` without absolute paths (jkonecny)
- Make the kickstart support for the btrfs command optional (vponcova)
- Fix non-root dir of install tree HD installation (#1689194) (jkonecny)
- subscription: Add missing pieces for the Subscription DBus module (mkolman)
- Add UI support for the ZIPL Secure boot (vponcova)
- Add DBus support for the ZIPL Secure Boot (vponcova)
- Add code convention to prefer join_paths over os.path.join (jkonecny)
- Add helper function force_path_join (jkonecny)
- Fix get anaconda version test after test file rename (vponcova)
- Rename iutil_test to util_test (jkonecny)

* Wed Apr 08 2020 Martin Kolman <mkolman@redhat.com> - 33.9-1
- Fix bad import of general errors (jkonecny)
- Improve code convention code formatting (jkonecny)

* Wed Apr 08 2020 Martin Kolman <mkolman@redhat.com> - 33.8-1
- Fix the indentation of false positives (vponcova)
- Don't try to format FBA DASD devices (#1715303) (vponcova)
- Disable the SMT warning by default (vponcova)
- Detect and warn if SMT is enabled (#1684056) (vponcova)
- Use constants to check the type of the payload object (#1820418) (vponcova)
- Provide the DBus types of the payloads (vponcova)
- Add Harddrive (HDD, HDISO) source (vslavik)
- Add utility functions for sources (vslavik)
- subscription: SubscriptionRequest DBus structure (mkolman)
- Remove the abstraction for the event loop (vponcova)
- Upgrade findFirstIsoImage (vslavik)
- Make sure that all Anaconda's DBus errors are registered (vponcova)
- Remove the mapping to a DBus error for KickstartError (vponcova)
- Don't use the default error register (vponcova)
- Set new repo configuration after validation is done (jkonecny)
- Add packaging constrains to URL payload source (jkonecny)
- Add repo cost to the URL payload source (jkonecny)
- Add proxy url to URL payload source (jkonecny)
- Add ssl configuration structure to URL payload source (jkonecny)
- Add ssl verification flag to URL payload source (jkonecny)
- Add Name to the URL payload source (jkonecny)
- Add URL repo configuration to the url source (jkonecny)
- Add empty repository configuration DBus structure (jkonecny)
- Add install_repo_enabled flag to URL payload source (jkonecny)
- Add tests for set up and tear down for url source (jkonecny)
- Add is_ready tests for URL source module (jkonecny)
- Add simple tests for a new URL payload source (jkonecny)
- Add payload URL source base structure (jkonecny)

* Fri Apr 03 2020 Martin Kolman <mkolman@redhat.com> - 33.7-1
- Don't clear errors by expanding pages in the custom spoke (vponcova)
- Fix the permission for changing a mount point (#1818500) (vponcova)
- Allow to use an existing unlocked LUKS in one special case (#1772902)
  (vponcova)
- Fix the encryption checkbox in the custom spoke (#1819360) (vponcova)
- Don't manually trigger a device encryption change (vponcova)

* Thu Apr 02 2020 Martin Kolman <mkolman@redhat.com> - 33.6-1
- Fix the test for complex data with secrets (vponcova)
- Update generate_request_description (vponcova)
- Add support for secrets in DBus structures (vponcova)
- Rename _test_dbus_property to _check_dbus_property (jkonecny)
- Fix text color on info bars (mkolman)
- Add NFS source (vslavik)

* Tue Mar 31 2020 Martin Kolman <mkolman@redhat.com> - 33.5-1
- Don't call the DBus method IsNodeFromIbft from the Storage module (#1817529)
  (vponcova)
- Use the right partitioning method in the storage spoke (vponcova)
- Improve logging of storage spokes in GUI and TUI (vponcova)
- Don't log an empty string (vponcova)
- Handle translation of an empty string in widgets (#1815461) (vponcova)
- Replace lambda by partial (jkonecny)
- Implement updating changed Anaconda files in a mock (jkonecny)
- Add possibility to add/remove specific dir in mock (jkonecny)
- Remove prepare parameter disable when running tests (jkonecny)
- Add missing arguments from the main command check (jkonecny)
- Move check for required setup-mock commands (jkonecny)
- Simplify test calling in setup-mock-test-env script (jkonecny)
- storage gui: keep expanded mountpoints info on actions in UI by default
  (#1210944) (rvykydal)
- Support updating Anaconda files in the mock (jkonecny)
- Handle invalid disk selection (vponcova)
- Set up advanced storage on the right device tree (#1812561) (vponcova)
- Remove storage tests (jkonecny)
- Use the right field of DiskStoreRow (#1816256) (vponcova)
- Add Repo files source (vslavik)
- Clean up and rename parseNfsUrl (vslavik)
- Do not show quarterly release part of the version in UI. (rvykydal)
- Add license to the __main__.py file for DBus modules (mkolman)
- Pass nosmt boot option to installed system (rvykydal)
- Adapt makebumpver to rhel-devel -> rhel-8 branch renaming. (rvykydal)
- Revert "Fix PR tests with mock version 2" (jkonecny)
- Remove the class PackagePayload (vponcova)
- Remove pyanaconda.payload.dnfpayload (vponcova)
- Improve help of dd_extract tool (jkonecny)
- Add missing period in iscsi login failure message. (rvykydal)
- Rename add-ons to additional software (#1674011) (rvykydal)
- Fix dd test RPM generation with binary files (jkonecny)
- Enable back skipped DD test (jkonecny)
- Fix translation of one nvdimm related GUI string (rvykydal)
- Fix memory leak in utils (yubihong)
- Fix code formatting of DUD tests (jkonecny)
- Fix dud test names (jkonecny)
- Small optimization in setup-mock-test-env script (jkonecny)
- Fix setup-test-env for other than pyanaconda tests (jkonecny)
- Create pyanaconda.payload.dnf (vponcova)
- Create pyanaconda.payload.__init__ (vponcova)
- Rename pyanaconda.payload.__init__ (vponcova)
- subscription: add system purpose support (mkolman)
- subscription: run Subscription module on RHEL (mkolman)
- subscription: add initial subscription module structure (mkolman)
- Wrap iscsi login error messages in GUI (#1811382) (rvykydal)
- Add tests for CD-ROM source (vslavik)
- Add CD-ROM source (vslavik)
- Add tests for the new utils file (vslavik)
- Move verifyMedia to sources as is_valid_install_disk (vslavik)
- Add the DBus module for SE/HMC (vponcova)
- Don't return anything from setup_kickstart (vponcova)
- Fix fd leak while fchmod failed (yubihong)

* Tue Mar 17 2020 Martin Kolman <mkolman@redhat.com> - 33.4-1
- Remove the configuration of the Blivet's logger (vponcova)
- Support logging of Anaconda DBus modules to files (#1812380) (vponcova)
- Fix a typo in s390 znet options configuration (rvykydal)
- Remove empty lines at the test source file (jkonecny)
- Source type is already tested by Interface (jkonecny)
- Remove the logging from the method process_kickstart (vponcova)
- Don't override the method generate_kickstart (vponcova)
- Show the help again (#1812896) (vponcova)
- gui: make description column of disk list resizable (#1530410) (rvykydal)
- gui: add tooltip to descriptions in disk list (#1530410) (rvykydal)
- gui: ellipsize description in disk list (#1530410) (rvykydal)
- Fix '\' is correctly forwarded by udev rules (jkonecny)
- Add debug print to dracut driver_updates (jkonecny)
- Escape spaces in dracut partition specifications (bcl)
- Rename the file with unit tests for the Payloads module (vponcova)
- Split the code for the source and payload factories (vponcova)
- Remove BaseFactory (vponcova)
- Simplify kickstart processing in the Payloads module (vponcova)
- Replace stat.ST_SIZE by .st_size (jkonecny)
- Module backport to better handling of sparse images (jkonecny)
- Avoid downloading payload image in set up phase (jkonecny)
- Add fallbacks for the source and payload factories (vponcova)
- Test the source and payload factories for all types (vponcova)
- Rename the file with unit tests for the Live OS module (vponcova)
- Test the LVM storage check. (vslavik)
- Verify that LVM destruction is orderly (vslavik)
- Don't set up the locale if none is selected (#1649956) (vponcova)
- network: fix crash during connections consolidation (#1811649) (rvykydal)
- Execute a kickstarted partitioning (#1811242) (vponcova)
- Remove extra quotes from the doc strings (vponcova)
- Remove unused code (vponcova)
- Remove dead dracut code (jkonecny)
- Set liveimg min_size to be x3 the real size (yturgema)

* Mon Mar 09 2020 Martin Kolman <mkolman@redhat.com> - 33.3-1
- Fix typos, comments and style in the storage-related code (vponcova)
- Don't add None values to a combo box (#1810679) (vponcova)
- Fix the unit tests for BTRFS (vponcova)
- Adjust documentation for new localization solution (jkonecny)
- Check pykickstart imports are correct in branching (jkonecny)
- Be able to disable correct branch in check-branching (jkonecny)
- Add check for branch setting (jkonecny)
- Add localization branch testing (jkonecny)
- Move functions to pyanaconda.core.storage (vponcova)
- Move functions to pyanaconda.ui.lib.storage (vponcova)
- Update action buttons only for the selected row (vponcova)
- Fix action buttons in the resize dialog (#1809950) (vponcova)
- Add branch specific configuration to a separate file (jkonecny)
- Always use the Anaconda's kickstart version (vponcova)
- Remove the Baz module (vponcova)
- Add small badges for Read the Docs and translations (vponcova)
- Remove the temporary workaround for StorageError (vponcova)
- Remove the error handler from the storage-related code (vponcova)
- Handle storage installation errors (vponcova)
- Remove the handler for FSTabTypeMismatchError (vponcova)
- Handle ZIPL errors as a bootloader installation error (vponcova)
- Remove the handler for NoDisksError (vponcova)
- Remove the handler for PartitioningError (vponcova)
- Handle the unusable storage module in UI (#1808650) (vponcova)
- Don't mention new-kernel-pkg anymore in /etc/sysconfig/kernel (rvykydal)
- Don't print warnings for new-kernel-pkg not being present (javierm)
- Handle the unusable storage module in the DBus Storage module (vponcova)
- network: add network module tests for installation tasks (rvykydal)
- Fix incorrect docstrings (vslavik)
- Use the latest kernel version list (#1807252) (vponcova)
- Check free space in the correct device tree (#1807339) (vponcova)
- Change log-capture script date to remove `:` symbol (jkonecny)
- Add missing logs to the log-capture utility (jkonecny)

* Tue Mar 03 2020 Martin Kolman <mkolman@redhat.com> - 33.2-1
- prefixdevname: add to unit tests (rvykydal)
- prefixdevname: pass persistent configuration to installed system (rvykydal)
- Add L10N dir constant to makefile (jkonecny)
- Remove auto-discover of git branch (jkonecny)
- Adapt Makefile to new L10N repository structure (jkonecny)
- prefixdevname: pass net.ifnames.prefix option to installed system (rvykydal)
- prefixdevname: install package to target system if needed (rvykydal)
- prefixdevname: import state from initramfs to stage 2 (rvykydal)
- Handle invalid optical install media (#1806520) (vponcova)
- Start live CD with explicit GUI (#1765650) (vslavik)
- network: fix GUI crash on invalid devices in the list (rvykydal)
- Add translation badge (vslavik)
- Remove -devel and -release for L10N repository (jkonecny)
- Use git url instead of http for pot files creation (jkonecny)
- Fix documentation changes in release.rst (jkonecny)
- Ignore the required package btrfs-progs in RHEL (vponcova)

* Mon Feb 24 2020 Martin Kolman <mkolman@redhat.com> - 33.1-1
- Fix the multiselection in the custom spoke (vponcova)
- Handle installation errors from DBus tasks (vponcova)
- Wait for entropy in the DBus Storage module (vponcova)
- Don't remove unknown devices (#1806233) (vponcova)
- Call GetFormatData instead of GetFormatTypeData (vponcova)
- Show progress messages from DBus tasks (vponcova)
- Report Blivet's messages during the storage installation (vponcova)
- Handle a failed bootloader installation (#1806103) (vponcova)
- Fix the exit handler (#1805916) (vponcova)
- Add DBus methods GetDeviceMountOptions and SetDeviceMountOptions (vponcova)
- Don't show the disk free space in bytes (vponcova)
- Fix the default disk selection (#1805553) (vponcova)

* Thu Feb 20 2020 Martin Kolman <mkolman@redhat.com> - 32.24-1
- Initialize disks in interactive and Blivet partitioning modules (vponcova)
- Fix the function get_device_partitions (vponcova)
- Fix the function unlock_device (vponcova)
- Apply extra arguments before the bootloader installation (vponcova)
- Remove configure_storage (vponcova)
- Remove the support for resetting the custom storage data (vponcova)
- Remove the support for on-disk snapshots of storage (vponcova)
- Remove collect_selected_disks (vponcova)
- Remove the local storage object from the custom spoke (vponcova)
- Remove the local storage object from the custom storage helpers (vponcova)
- Update the storage model of device tree modules (vponcova)
- Use the exception DeviceSetupError (vponcova)
- Change the task MountExistingSystemTask (vponcova)
- Change the task AddDeviceTask (vponcova)
- Extend the task ChangeDeviceTask (vponcova)
- Add the container specification to the device factory request (vponcova)
- Extend the DBus method ValidateContainerName (vponcova)
- Add the DBus method UpdateContainerData (vponcova)
- Add the DBus method GenerateContainerData (vponcova)
- Add the DBus method GenerateContainerName (vponcova)
- Add the method reset_container_data to the device factory request (vponcova)
- Add the DBus method GetContainerFreeSpace (vponcova)
- Add the DBus method CollectContainers (vponcova)
- Add permissions for changing the container (vponcova)
- Filter unsupported disklabel devices (vponcova)
- Add the DBus method IsDeviceEditable (vponcova)
- Add the DBus method CheckCompleteness (vponcova)
- Add the DBus method IsDeviceLocked (vponcova)
- Add a new permission for changing a list of disks (vponcova)
- Update the permission for the device encryption (vponcova)
- Add the DBus method ResetDevice (vponcova)
- Add the DBus method DestroyDevice (vponcova)
- Add the DBus method SchedulePartitionsWithTask (vponcova)
- Remove the local storage object from the accordion (vponcova)
- Remove the local storage object from the source spoke in GUI (vponcova)
- TUI: Use get_hdiso_source_description (vponcova)
- Remove the local storage object from the storage spoke (vponcova)
- Remove the local storage object from the advanced storage spoke (vponcova)
- Use the Blivet partitioning module in Blivet-GUI (vponcova)
- Remove the local storage object from the resize dialog (vponcova)
- Remove the local storage object from the action dialog (vponcova)
- Extend the class DeviceActionData (vponcova)
- Remove the local storage object from the selected disks dialog (vponcova)
- Remove the local storage object from the refresh dialog (vponcova)
- Remove the local storage object from dialogs for specialized disks (vponcova)
- Remove the local storage object from run_installation (vponcova)
- Remove the local storage object from FileSystemSpaceChecker (vponcova)
- TUI: Use create_partitioning (vponcova)
- TUI: Extend apply_disk_selection (vponcova)
- TUI: Simplify default disk selection in Storage spoke (vponcova)
- Move is_local_disk to pyanaconda.ui.lib (vponcova)
- Use apply_partitioning from pyanaconda.ui.lib (vponcova)
- Move try_populate_devicetree to pyanaconda.ui.lib (vponcova)
- Move the UI support for device protection to pyanaconda.ui.lib (vponcova)
- Move get_disks_summary to pyanaconda.ui.lib (vponcova)
- Move apply_disk_selection to pyanaconda.ui.lib (vponcova)
- Move the UI support for storage initizalization to pyanaconda.ui.lib
  (vponcova)
- Remove the storage argument from the storage initialization (vponcova)
- Move the UI support for DASD formatting to pyanaconda.ui.lib (vponcova)
- Remove the storage and data arguments from DasdFormatting (vponcova)
- Add the function find_partitioning (vponcova)
- Remove the static partitioning modules (vponcova)
- Remove the Enabled property from the partitioning modules (vponcova)
- Mark storage kickstart commands as useless (vponcova)
- Remove the UI workaround for storage kickstart data (vponcova)
- Remove the UI code for the storage configuration (vponcova)
- Remove the local storage object from TUI (vponcova)
- Don't use the local storage object in storage utils (vponcova)
- Don't use the local storage object for the installation (vponcova)
- Don't use the local storage object for formatting DASDs from UI (vponcova)
- Remove automatic push of pot files during release (jkonecny)
- Remove zanata from release.rst (jkonecny)
- Remove deprecated translations.txt document (jkonecny)
- Update Readme link to translation project (jkonecny)
- Remove Zanata from translation canary (jkonecny)
- Remove zanata from setup test env scripts (jkonecny)
- Remove zanata from makebumpver (jkonecny)
- Remove zanata configuration file (jkonecny)
- Remove Zanata from po/Makefile (jkonecny)
- Remove zanata from Makefile (jkonecny)
- Remove unnecessary sed from configure.ac (jkonecny)
- Use l10n repository for pushing changed pot file (jkonecny)
- Pull po files from our l10n repo instead of Zanata (jkonecny)
- Offer only supported sector sizes in NVDIMM reconfiguration dialog (rvykydal)
- Fix PR tests with mock version 2 (jkonecny)
- Don't use the local storage object for the storage initialization (vponcova)
- Don't use device objects in the payload classes (vponcova)
- Remove the attribute for storage from the payload classes (vponcova)
- Don't use local storage objects in the image utils (vponcova)
- Don't use the local storage objects in the payload utils (vponcova)
- Run a DBus task to create the pre-installation snapshot (vponcova)
- Don't set up the local storage checker object (vponcova)
- Don't use the local storage object during the start of anaconda (vponcova)
- Remove the local storage object from the rescue mode (vponcova)
- Don't use the local storage object to initialize time (vponcova)
- Don't reset the local storage object (vponcova)
- Don't create the local storage object (vponcova)
- Don't modify the list of device names (vponcova)

* Thu Feb 13 2020 Martin Kolman <mkolman@redhat.com> - 32.23-1
- Test kickstart warnings from modules (vslavik)
- Use kickstart parsing warnings coming from boss (vslavik)
- Log kickstart warnings in modules (vslavik)
- Disable package download to / /tmp (#1781517) (jkonecny)
- Handle the variant in SetConstraint (vponcova)
- Handle the variant from GetResult (#1798392) (vponcova)
- Fix the function _del_xdg_runtime_dir (vponcova)
- Do not crash on adding fcoe device in gui when there are no nics (#1798402)
  (rvykydal)
- Fix checking of network device type in Add FCoE gui dialog (#1798876)
  (rvykydal)
- Use check_task_creation_task in timezone tests (rvykydal)
- Move timezone setup kickstart method to dbus module (rvykydal)
- Do not restart NTP service during its installation (rvykydal)
- Add fixme to ntp from dhcp setting (rvykydal)
- Change "not...in" to "...not in" (vslavik)
- Line length fixes (PEP8) + typos (vslavik)
- Add the DBus method GenerateDeviceFactoryPermissions (vponcova)
- Generate the device factory permissions (vponcova)
- Add the DBus structure DeviceFactoryPermissions (vponcova)
- Move the class DeviceFactoryRequest to a new file (vponcova)
- Set up the environment for pylint (vponcova)
- Unify geoloc logging and enable/disable decision logic (vslavik)
- Disable geoloc by opts.geoloc instead of kernel cmdline (vslavik)
- Add a fallback for a disk of the live device (vponcova)
- If no usable boot drive is found, raise an exception (vponcova)

* Mon Feb 03 2020 Martin Kolman <mkolman@redhat.com> - 32.22-1
- Don't set the device names (#1797274) (vponcova)
- Fix line spacing in UI (vslavik)
- Fix line spacing in pyanaconda (vslavik)
- Extend the start-module script (vponcova)
- Remove start() from pylint defining attrs methods (jkonecny)
- Refactor pylintrc file a bit (jkonecny)
- Remove pylint CVS ignore directory (jkonecny)
- Add TODO to enable C and R in pylint (jkonecny)
- Remove bad-option-value disables from pylint (jkonecny)
- Add TODO for future work (jkonecny)
- Remove use of eval from pylint disabled (jkonecny)
- Ignore attributes of Namespace class (jkonecny)
- Fix GError message False positive (jkonecny)
- Move unnecessary pass statement from false positives (jkonecny)
- Add mock to the list of pylint deprecated modules (jkonecny)
- Fix pylint errors (jkonecny)
- Adapt runpylint to use pocketlint replacement (jkonecny)
- Add pylint censorship - replacement of pocketlint (jkonecny)

* Wed Jan 29 2020 Martin Kolman <mkolman@redhat.com> - 32.21-1
- Add the path-id attribute to the DBus structure for device data (vponcova)
- Use id_path as a long identifier of a disk (vponcova)
- Migrate authselect to dbus tasks (mkolman)
- Remove pyanaconda.flags.cmdline and KernelArguments.getbool() (vslavik)
- Remove duplicated definition of PayloadContainer (vslavik)
- Fix typos in docstrings (vslavik)
- Fix setup-mock-test-env with multiple test commands (jkonecny)
- Add support to run pylint only check (jkonecny)
- Fix most of pep8 issues in pyanaconda/modules subfolder (rvykydal)
- Convert VG reserved_space to Size (vtrefny)
- Do not set default fstype for blivet-gui (vtrefny)

* Mon Jan 20 2020 Martin Kolman <mkolman@redhat.com> - 32.20-1
- Add the DBus method ChangeDevice (vponcova)
- Add the task ChangeDeviceTask (vponcova)
- Add pep8 check (rvykydal)
- Fix max-line-length setting for pep8speaks (rvykydal)
- Extend PayloadFactory tests (jkonecny)
- Add test for payload type DBus API (jkonecny)
- Rename payload shared testing objects (jkonecny)
- Add type property to payloads (jkonecny)
- Rename payload dnf tests to packages tests (jkonecny)
- Add FIXME/TODO about GetActivePayload (jkonecny)
- Move Publishable to PayloadBase (jkonecny)
- Adapt tests to a new Payload publishing (jkonecny)
- Generate %%packages only when DNF module was used (jkonecny)
- Fix payloads shared testing class (jkonecny)
- Move payload Packages kickstart processing to Payloads (jkonecny)
- Change GetActivePayloadPath to GetActivePayload (jkonecny)
- Publish payload instead of payload path (jkonecny)
- Change payloads objects to interfaces (jkonecny)
- Migrate LiveOS payload to dynamic publishing (jkonecny)
- Migrate LiveImage payload to dynamic publishing (jkonecny)
- Migrate DNF payload for dynamic publishing (jkonecny)
- Use container to publish payloads (jkonecny)
- Add payload container (jkonecny)
- Rename PAYLOAD_BASE to PAYLOAD (jkonecny)
- Remove unnecessary space (jkonecny)
- Remove DNF DBus namespace (jkonecny)
- Move Packages module publishing to Payloads service (jkonecny)
- Move payload packages out of DNF module (jkonecny)
- Add basic configuration for pep8speaks github app (rvykydal)
- Be more strict when checking for mounted dvd source (rvykydal)
- Protect cdroms during tree population for image installs (rvykydal)
- Finish code conventions rules migration to upstream (jkonecny)
- Require new pykickstart version (jkonecny)
- Revert "Revert "Fix Timezone pykickstart command version"" (jkonecny)
- Add the task AddDeviceTask (vponcova)
- Add the DBus method ValidateDeviceFactoryRequest (vponcova)
- Add the DBus field 'reformat' to the device factory request (vponcova)
- Add the DBus method GetDeviceTypesForDevice (vponcova)
- Add the DBus method GetFileSystemsForDevice (vponcova)
- Add the DBus method GetRawDevice (vponcova)
- Add the DBus method GenerateDeviceName (vponcova)
- Add the DBus method GetDefaultLUKSVersion (vponcova)
- Add the DBus method GenerateDeviceFactoryRequest (vponcova)
- Add the DBus method ValidateRaidLevel (vponcova)
- Add the DBus method ValidateContainerName (vponcova)
- Add the DBus method AddDevice (vponcova)
- Add the DBus method ValidateMountPoint (vponcova)
- Add the DBus method CollectUnusedMountPoints (vponcova)
- Add the DBus method GetSupportedRaidLevels (vponcova)
- Add the DBus method GetDefaultFileSystem (vponcova)
- Add the DBus method CollectSupportedSystems (vponcova)
- Add the DBus method GetDiskTotalSpace (vponcova)
- Add the DBus method CollectBootLoaderDevices (vponcova)
- Add the DBus method CollectUnusedDevices (vponcova)
- Add the DBus method CollectNewDevices (vponcova)
- Add the DBus method GetPartitioned (vponcova)
- Add the DBus method GenerateSystemData (vponcova)
- Add the DBus method GenerateSystemName (vponcova)
- Create the device tree scheduler (vponcova)
- Always create and publish the DASD and ZFCP modules (vponcova)
- Add the DBus method IsSupported to the zFCP module (vponcova)
- Add the DBus method IsSupported to the NVDIMM module (vponcova)
- Add the DBus method IsSupported to the DASD module (vponcova)
- Add the DBus method IsSupported to the iSCSI module (vponcova)
- Add the DBus method IsSupported to the FCoE module (vponcova)
- Allow arch filtering for comps (jmracek)
- Remove duplicated exception handler usage (vslavik)

* Mon Jan 13 2020 Martin Kolman <mkolman@redhat.com> - 32.19-1
- Revert "Fix Timezone pykickstart command version" (vponcova)
- Improve payload packages test for languages (jkonecny)
- Update payload Packages properties tests (jkonecny)
- Update payload LiveImage properties tests (jkonecny)
- Fix Timezone pykickstart command version (jkonecny)
- Fix failed tests introduced by merging multiple PRs (jkonecny)
- Clean up for PEP257, PEP8, etc. in localization and its tests (vslavik)
- Add tests for the rewritten localization module (vslavik)
- Fix wrong code in localization found while writing tests (vslavik)
- Remove parse_langcode(), LANGCODE_RE, and associated tests (vslavik)
- Fix dosctrings by removing mentions of LANGCODE_RE (vslavik)
- Replace remaining uses of parse_langcode by langtable's parsing (vslavik)
- Add and use a convenience function to get language id (vslavik)
- Add and use a mechanism for aborting early with invalid locale (vslavik)
- Add failure tests for %%packages --ignorebroken (jkonecny)
- Raise error on --ignorebroken when is disabled (jkonecny)
- Fail to set packages IgnoreBroken when disabled (jkonecny)
- Add enable_ignore_broken_packages configuration (jkonecny)
- Add test for the new Packages API (jkonecny)
- Support --ignorebroken by packages module (#1642013) (jkonecny)
- Support possibility to skip broken packages (#1642013) (jkonecny)
- Do not crash on disk.wwn value being None (#1711571) (rvykydal)
- Fix a callback of the PropertiesChanged signal (vponcova)
- Test unwrapped DBus values (vponcova)
- Replace the default DBus error (vponcova)
- Extend check_task_creation_list (vponcova)
- Simplify langtable method calls (vslavik)
- Require langtable 0.0.49 for its new parsing method (vslavik)
- Fix import, add license statement in dracut driver updates test (vslavik)

* Tue Jan 07 2020 Martin Kolman <mkolman@redhat.com> - 32.18-1
- Fix cppcheck problem with undefined macros (jkonecny)
- Fix C variable use before check for NULL (jkonecny)
- Calculate ip address for kickstart URL ending in / (imsedgar)
- Enable /boot on btrfs subvolume with GRUB2 (ngompa13)
- Remove the workaround in the Resize dialog (vponcova)
- Move the support for resizing devices (vponcova)
- Add KernelArguments.is_enabled() as a replacement for getbool() (vslavik)
- Fix tests broken by renamed modules (vslavik)
- keyboard: pass shared module instance of localed wrapper to tasks (rvykydal)
- keyboard: replace safe_dbus with dasbus in LocaledWrapper (rvykydal)
- Add tests for the KernelArguments class (vslavik)
- Stop KernelArguments inheriting from a dictionary (vslavik)
- Change tests to use kernel.cmdline instead of flags.cmdline (vslavik)
- Change all uses of flags.cmdline to kernel.kernel_arguments (vslavik)
- Rename variables to prevent conflict with importing "kernel_arguments"
  (vslavik)
- Change flags.cmdline to use kernel.kernel_arguments (vslavik)
- Add kernel.kernel_arguments providing same functionality as flags.cmdline
  (vslavik)
- Only attempt to open the ibm,max-boot-devices sysfs entry if it exists
  (javierm)
- Don't add more devices in boot-device NVRAM than the maximum allowed
  (javierm)

* Thu Dec 12 2019 Martin Kolman <mkolman@redhat.com> - 32.17-1
- Calculate the space on uninitialized disks (#1782449) (vponcova)
- Define a method required by _schedule_actions (#1782463) (vponcova)
- Split the partitioning code (vponcova)
- Add the attribute children to the device data (vponcova)

* Tue Dec 10 2019 Martin Kolman <mkolman@redhat.com> - 32.16-1
- Add a DBus method for checking resizable devices (vponcova)
- Add DBus methods for partitioned devices (vponcova)
- Add a DBus method for getting device size limits (vponcova)
- Add the attribute protected to the device data (vponcova)
- keyboard: make populating of missing values part of installation task
  (rvykydal)
- keyboard: fix write_x_configuration method (rvykydal)
- Reduce progress spinner repaints to save CPU (rhbz#1204242) (vslavik)
- Document the storage setters (vponcova)
- Rename the file with tests for the Blivet partitioning method (vponcova)
- Change the type of AppliedPartitioning (vponcova)
- Rename the callbacks on_storage_reset (vponcova)
- Add the DBus method ResetPartitioning (vponcova)
- Rename the DBus method for resetting the storage (vponcova)
- Test the boot loader factory (vponcova)
- Set up the boot loader factory (vponcova)
- Create the boot loader factory (vponcova)
- Add a new configuration option for the type of the bootloader (vponcova)
- network: wrap IPv4 addresses showed in GUI (#1777706) (rvykydal)
- keyboard: do not return None value from apply configuration task (rvykydal)
- keyboard: fix reference before assignment in apply keyboard task (rvykydal)
- keyboard: add localization module unit tests for keyboard (rvykydal)
- keyboard: fix return value of LocaledWrapper.layouts_variants property
  (rvykydal)
- keyboard: fix setting from generic keyboard in ks parsing (rvykydal)
- keyboard: move setting of default value into related task (rvykydal)
- Raise MountFilesystemError from DBus methods (vponcova)
- keyboard: make update_settings_from_task private (rvykydal)
- Add the mount point attribute to the device format data (vponcova)
- Change mock imports to use the unittest.mock full import path (vslavik)
- Rename an attribute of the action data structure (vponcova)
- Change service_start_timeout (vponcova)
- keyboard: update a comment for future refactorisations (rvykydal)
- keyboard: remove superfluous call to write_x_configuration (rvykydal)
- Calculate the space on disks with supported disk labels (vponcova)
- keyboard: guard activation of keyboard configuration in the module (rvykydal)
- keyboard: when converting values restore both console and X (#1775712)
  (rvykydal)
- keyboard: do not store generic keyboard setting at all (rvykydal)
- keyboard: split populating of missing keyboard values (rvykydal)
- Fix __all__ in pyanaconda.modules.common.structure.* (vponcova)
- keyboard: do not convert from X value if we have vconsole in apply (#1776148)
  (rvykydal)
- Change the DBus support for collecting ancestors (vponcova)
- Add the attribute removable to the device data (vponcova)
- Extend the attributes of the device data (vponcova)
- keyboard: fix getting options from LocaledWrapper (rvykydal)
- keyboard: move LocaledWrapper into localization module (rvykydal)
- keyboard: apply configuration with a task (rvykydal)
- keyboard: populate missing keyboard items with a task (rvykydal)
- keyboard: write configuration with module task (rvykydal)
- keyboard: split out populating of missing values into separate task
  (rvykydal)
- keyboard: remove doc for unused weight parameter. (rvykydal)
- keyboard: remove keyboard command from anaconda (rvykydal)
- Rename payload sources to source (jkonecny)
- Rename PayloadService to PayloadsService (jkonecny)
- Rename payloads.payloads to payload.payload (jkonecny)
- Rename payload to payloads for DBus services (jkonecny)
- Rename payload module to payloads (jkonecny)
- Publish main payload under Payloads (jkonecny)
- Create PayloadContainer for dynamic provisioning (jkonecny)
- Rename payload base to payload (jkonecny)
- Use a variable when calling Zanata client in makefile (mkolman)
- Clean up the spoke for the advanced storage (vponcova)
- Rename payload DBus constants (jkonecny)
- Remove handler word from payload leftovers (jkonecny)
- Remove handler word from tests (jkonecny)
- Rename LiveOSHandler* classes to LiveOS* (jkonecny)
- Rename LiveImageHandler* classes to LiveImage* (jkonecny)
- Rename DNFHandler* classes to DNF* (jkonecny)
- Rename handlers from DNF internal variables (jkonecny)
- Rename PackagesHandler* classes to Packages* (jkonecny)
- Rename handler to payload in PayloadBase class (jkonecny)
- Rename publish_handler to publish_payload (jkonecny)
- Rename create_handler to create_payload (jkonecny)
- Rename get_active_handler_path to payload path (jkonecny)
- Rename is_handler_set to is_payload_set (jkonecny)
- Rename payload handler getter and setter to payload (jkonecny)
- Rename HandlerFactory to PayloadFactory (jkonecny)
- Rename HandlerType to PayloadType (jkonecny)
- Remove handler from factories variables (jkonecny)
- Rename HandlerNotSetError to PayloadNotSetError (jkonecny)
- Rename handler in logs for payload service class (jkonecny)
- Rename payload handler internals in payload service (jkonecny)

* Mon Nov 18 2019 Martin Kolman <mkolman@redhat.com> - 32.15-1
- Fix wrong kdump boot option in boot options docs (vslavik)
- Remove unused pylint false positive (jkonecny)
- Remove the DBus library (vponcova)
- Remove the extra support for PropertiesChanged (vponcova)
- Normalize the pretty XML output (vponcova)
- Update the unit tests (vponcova)
- Reorganize the DBus library (vponcova)
- Remove signal subscriptions from anaconda (vponcova)
- Add support for disconnection of a DBus proxy (vponcova)
- Clean up the anaconda's signal (vponcova)
- Remove the anaconda's DBus from the DBus library (vponcova)
- Remove the anaconda's signal from the DBus library (vponcova)
- Remove the anaconda's logger from DBus library (vponcova)
- Create the DBus library (vponcova)

* Tue Nov 12 2019 Martin Kolman <mkolman@redhat.com> - 32.14-1
- network: restrict applying of config from ks in initramfs with NM (#1768791)
  (rvykydal)
- network: try to apply kickstart in initramfs only if neeeded (#1768791)
  (rvykydal)
- Use default required space solution for LiveOS payload (jkonecny)
- Fix Live Image module required value default (jkonecny)
- Add defaults to payload required space base (jkonecny)
- Move set up and tear down sources to payload base (jkonecny)
- Move installation task API to base payload (jkonecny)
- Move SpaceRequired API to payload base (jkonecny)
- Add tests payload shared API for sources handling (jkonecny)
- Add payload shared test API for sources (jkonecny)
- Tweak payload_shared test class (jkonecny)
- Use payload base interface for existing payloads (jkonecny)
- Add payload base interface implementation (jkonecny)
- Move payload base to payloads folder (jkonecny)
- Move source base classes to payload.sources (jkonecny)
- Add names to the network tests (vslavik)
- Forbid trailing period (dot) in hostname (#1648107) (vslavik)
- Remove the enum PartitioningMethod from the Storage spoke in GUI (vponcova)
- Collections of callbacks in signals can be changed during emitting (vponcova)
- Run the installation tasks of the DBus addons (vponcova)
- Add DBus support for installation tasks for addons in the Boss (vponcova)
- Provide fake installation tasks for the Baz addon (vponcova)
- Add DBus support for installation tasks for addons (vponcova)
- Add support for running DBus tasks in one task (vponcova)
- Don't enable BLS for Xen machines (javierm)

* Tue Nov 05 2019 Martin Kolman <mkolman@redhat.com> - 32.13-1
- Clean up ancient timezone tests (vslavik)
- Add missing quotation mark to tmux.conf (jkonecny)
- Fix too long lines in timezone module tests for PEP8 compliance (vslavik)
- Add timezone interface tests for creation of timezone and NTP tasks (vslavik)
- Add tests for the NTP D-Bus task (timezone module) (vslavik)
- Add tests for the timezone D-Bus task (timezone module) (vslavik)
- Move timezone and NTP from execute() to D-Bus configuration tasks (vslavik)
- Add Neal Gompa as community feature maintainer (jkonecny)
- Add pure community features documentation (jkonecny)

* Tue Oct 29 2019 Martin Kolman <mkolman@redhat.com> - 32.12-1
- Add a temporary hack to fix installations on ppc64le and aarch64 (#1764666)
  (mkolman)

* Thu Oct 24 2019 Martin Kolman <mkolman@redhat.com> - 32.11-1
- Fix the timeout of DBus calls (vponcova)
- Remove pydbus from the spec file (vponcova)
- Test DBus support with Gio.TestDBus (vponcova)
- Update the support for DBus properties (vponcova)
- Create variants for the signal PropertiesChanged (vponcova)
- Test the extended support for the DBus observer (vponcova)
- Remove PropertiesCache (vponcova)
- Extend the DBus observer (vponcova)
- Test the extended support for DBus connection (vponcova)
- Extend the support for DBus connections (vponcova)
- Don't use pydbus in the function get_object_path (vponcova)
- Test the client support for DBus objects (vponcova)
- Add the client support for DBus objects (vponcova)
- Test the server support for DBus objects (vponcova)
- Add the server support for DBus objects (vponcova)
- Extend DBus constants (vponcova)
- Test the extended support for DBus specification (vponcova)
- Extend the support for DBus specification (vponcova)
- Test the support for parsing the XML specification (vponcova)
- Add support for parsing the XML specification (vponcova)
- Test the DBus signals (vponcova)
- Extend the Signal class (vponcova)
- Don't use signals from pydbus (vponcova)
- Test the DBus error registration (vponcova)
- Don't use DBus error registration from pydbus (vponcova)
- Remove pydbus from the comments (vponcova)
- Test the extended support for DBus typing (vponcova)
- Extend the support for DBus typing (vponcova)
- Don't import Variant from pydbus (vponcova)
- Fix other payload module cyclic imports (vponcova)
- Add code conventions to upstream (jkonecny)
- Fix payload module cyclic imports (jkonecny)
- Enable networking in the testing environment by default (vponcova)
- network: adapt network config via kickstart from disk to NM in initramfs
  (#1757781) (rvykydal)
- network: fix handling of ksdevice=bootif in initramfs (rvykydal)
- Make sure we work with fresh data when trying to do netroot (vpodzime)
- Make our manual triggering on network in dracut work (#1082500) (vpodzime)
- iscsi: do not generate initiator for generated kickstart if iscsi is not used
  (rvykydal)
- network: remove useless function (rvykydal)
- network: remove Network command from anaconda (rvykydal)
- network: remove parse method from Network command (rvykydal)
- network: remove packages attribute from Network command (rvykydal)
- Move payload live_os source under its directory (jkonecny)
- Create an empty payload source live_os folder (jkonecny)
- Move payload service constants to the main dir (jkonecny)
- Remove modules.payload.live folder (jkonecny)
- Move rest of payload utils to live_image utils (jkonecny)
- Move create_rescue_image to payload base utils (jkonecny)
- Move get_kernel_version_list to payload base (jkonecny)
- Move InstallFromTarTask to live_image payload (jkonecny)
- Move InstallFromImageTask to payload.base (jkonecny)
- Move UpdateBLSConfigurationTask to payload base (jkonecny)
- Move DownloadProgress to payload live_image (jkonecny)
- Move TeardownInstallationSourceImageTask to payload (jkonecny)
- Move SetupInstallationSourceImageTask to payload (jkonecny)
- Move CheckInstallationSourceImageTask to payload (jkonecny)
- Fix imports after move of live_image payload (jkonecny)
- Move lime_image code to the payloads folder (jkonecny)
- Fix imports after move of live_os payload (jkonecny)
- Move live_os code to the payloads folder (jkonecny)
- Fix imports after move of DNF payload (jkonecny)
- Move DNF handler to payloads folder (jkonecny)
- Remove useless support for boot loader update (vponcova)

* Fri Oct 18 2019 Martin Kolman <mkolman@redhat.com> - 32.10-1
- Return back AutoPart kickstart command (#1761901) (jkonecny)
- Update pyanaconda/exception.py (japokorn)
- Fix links to a new pykickstart GitHub group (jkonecny)
- Rename main modules to services (vponcova)
- don't treat s390 as headless when selecting UI mode (dan)
- Add link to the blog website to our README (jkonecny)
- Add links on our blog to upstream documentation (jkonecny)
- Add PARTUUID to lsblk_output log (japokorn)
- Fix a unit test for a boot loader task (vponcova)
- Test the DBus method FindFormattable (vponcova)
- Add DBus method that finds DASDs for formatting (vponcova)
- Move tests for the zFCP module (vponcova)
- Move tests for the FCoE module (vponcova)
- Move tests for the ISCSI module (vponcova)
- Move tests for the DASD module (vponcova)

* Tue Oct 15 2019 Martin Kolman <mkolman@redhat.com> - 32.9-1
- Don't mark the network command as removed (vponcova)

* Mon Oct 14 2019 Martin Kolman <mkolman@redhat.com> - 32.8-1
- Do not use module_debsolv_errors DNF method (jkonecny)
- Update pyanaconda/rescue.py (slavik.vladimir)
- Make small fixes in the errors file code (jkonecny)
- Make error string wrap more sane (jkonecny)
- Remove make updates (jkonecny)
- Fix regexp for iscsi initiator iqn name validation (#1750865) (rvykydal)
- Disable kickstart output from the Payload module (vponcova)
- Extend the tests for the Boss module (vponcova)
- Mark the network command as removed (vponcova)
- Generate the complete kickstart using the Boss (vponcova)
- Add DBus support for generating a complete kickstart (vponcova)
- Improve the DBus return value for reading a kickstart file (vponcova)
- Add DBus structure for a kickstart report (vponcova)
- Simplify the DBus support for reading a kickstart file (vponcova)
- Don't reimplement the run method in the Boss (vponcova)
- Start DBus modules in a task (vponcova)
- Remove AnacondaBossInterface (vponcova)
- Don't represent the modules observers by their DBus path (vponcova)
- Use a signal to propagate the module observers in the Boss (vponcova)
- Make the nomount boot option work again (vslavik)
- Skip buildins when processing kernel boot args (#1637472) (jkonecny)
- Remove ldconfig scriptlet from a spec file (jkonecny)
- Switch the makeupdates script to Python 3 (mkolman)
- Fix a couple issues identified by Pylint (mkolman)
- PEP8 for function names (mkolman)
- Remove disused support for automatically fetching packages from Koji
  (mkolman)
- Support basic nested DBus structures (vponcova)
- Support resolving of simple type hints (vponcova)
- Generate DBus fields with DBusFieldFactory (vponcova)
- Fix a missing patch in unit tests (vponcova)
- Increase test coverage for payload sources (jkonecny)
- Improve docstring on payload source (jkonecny)
- Add logging to the payload source ready state (jkonecny)
- Adapt tests to a new is_ready solution (jkonecny)
- Implement is_ready for live os payload source (jkonecny)
- Switch payload source ready property to method (jkonecny)
- Remove payload source ready setter (jkonecny)
- Add tests for payload sources error propagation (jkonecny)
- Raise exception at the end of sources tear down (jkonecny)
- Payload sources can't be set when initialized (jkonecny)
- Fix doc strings in Live OS payload source (jkonecny)
- Fix doc strings in Payload module (jkonecny)
- Adapt tests to a new payload grouping tasks (jkonecny)
- Use TearDownSourcesTask in LiveOS payload (jkonecny)
- Add tear down payload sources task (jkonecny)
- Use SetUpSourcesTask in LiveOS payload (jkonecny)
- Add set up payload sources task (jkonecny)
- Rename Live OS Source specific tasks (jkonecny)
- Change test for Live payload source readiness (jkonecny)
- Adapt tests to new Installation task with source (jkonecny)
- Check source readiness in Payload install task (jkonecny)
- Remove handler check for source readiness (jkonecny)
- Remove payload sources validate API (jkonecny)
- Replace payload attach_source by set_sources (jkonecny)
- Rename kind to type (jkonecny)
- Rename tear down Live OS source task (jkonecny)
- Add source tests to Live OS (jkonecny)
- Adapt tests to the new Live OS source solution (jkonecny)
- Add check_task_creation_list helper function (jkonecny)
- Add source checkers to Live OS handler (jkonecny)
- Use source object in the Live OS handler (jkonecny)
- Add is source set method to payload handler base (jkonecny)
- Adapt Live OS test for detect image migration (jkonecny)
- Move Live OS image detection to source (jkonecny)
- Adapt payload Live OS handler/source tests (jkonecny)
- Migrate image path from Live OS handler to source (jkonecny)
- Live OS source can have only one source attached (jkonecny)
- Fix line longer than 99 characters in payload (jkonecny)
- Add check if payload source is supported (jkonecny)
- Add payload source type tests (jkonecny)
- Implement type to the payload source base (jkonecny)
- Move payload handler/sources types to constants (jkonecny)
- Implement source attach to the payload handlers (jkonecny)
- Add test for payload CreateSource API (jkonecny)
- Wrap payload source creation to DBusContainer (jkonecny)
- Add support for source creation to Payload module (jkonecny)
- Add payload SourceFactory test (jkonecny)
- Add payload source factory (jkonecny)
- Add test for the payload HandlerFactory class (jkonecny)
- Make payload HandlerFactory class more generic (jkonecny)
- Remove required parameter from the Live OS Source (jkonecny)
- Add Live OS source tear down test (jkonecny)
- Use moved tear down task in Live OS source (jkonecny)
- Move Live OS tear down task to Live OS source (jkonecny)
- Add test for Live OS source validation method (jkonecny)
- Learn Live OS source how to validate source (jkonecny)
- Add Validate API to the payload source base (jkonecny)
- Add test for Live OS Source set up task (jkonecny)
- Move and fix Live OS init source test (jkonecny)
- Use set up source task in the Live OS source (jkonecny)
- Rename set up task for live os source (jkonecny)
- Move set up source live os image task to sources (jkonecny)
- Add empty classes for Live OS payload interface (jkonecny)
- Add base payload source module (jkonecny)
- Add a new python module for payload sources (jkonecny)

* Fri Oct 04 2019 Martin Kolman <mkolman@redhat.com> - 32.7-1
- network: split configure hostname task out of network installation task
  (#1757960) (rvykydal)
- Switch to pypi pylint from RPM (jkonecny)
- Allow to handle the return value of subprocess.run (vponcova)
- Remove the unexpected keyword argument 'env' (vponcova)
- Remove the assignment of the same variable to itself (vponcova)
- Remove unused false positives (vponcova)
- Improve updates repo configuration in GUI (#1670471) (mkolman)
- Don't touch storage until it is ready (vponcova)
- Run the manual partitioning task for the given requests (vponcova)
- Set the locale for unit tests (vponcova)
- Deprecate the current kickstart support for addons (vponcova)
- Add kickstart support for the Baz module (vponcova)
- Support the %%addon sections in the kickstart specification (vponcova)
- Handle the bootloader reset in the partitioning task (vponcova)
- Fix the DBus patching functions (vponcova)
- Patch DBus proxies in GUI and TUI simple import tests (vponcova)
- Add DBus method for validation of selected disks (vponcova)
- Enable faulthandler in DBus modules (vponcova)
- Reset the storage and the playground of partitioning modules (vponcova)
- Add support for getting an object path of a DBus proxy (vponcova)
- Remove pointless '../../' to clean up NFS mounts (riehecky)

* Wed Sep 25 2019 Martin Kolman <mkolman@redhat.com> - 32.6-1
- Switch between layouts without confirmation (#1333984) (vponcova)
- Remove the old and broken zram-stats script (#1561773) (mkolman)
- Rename _test_dbus_partitioning and _test_dbus_property (vponcova)
- Remove attributes for the static partitioning modules (vponcova)
- Test the custom partitioning from kickstart (vponcova)
- Test the property AppliedPartitioning (vponcova)
- Test the property CreatedPartitioning (vponcova)
- Test the dynamic partitioning modules (vponcova)
- Test the partitioning factory with kickstart (vponcova)
- Generate kickstart from the applied partitioning (vponcova)
- Create a partitioning module for the kickstart data (vponcova)
- Add tests for the storage installation tasks (vponcova)
- Add the installation task for BTRFS (vponcova)
- Add a simple import test for pyanaconda (vponcova)
- Fix the implementation of patch_dbus_publish_object (vponcova)
- Use the validation report for the storage validation (vponcova)
- Remove get_object_path of TaskInterface (vponcova)
- Add support for validation tasks (vponcova)
- Move the partitioning validation to the base class (vponcova)
- Add the installation task for ZIPL (vponcova)
- Improve installation tasks of the Storage module (vponcova)
- Don't initialize PartTypeSpoke from the Summary hub (vponcova)
- Add DBus support for the device ancestors (vponcova)
- Fix the DBus method GetUsableDisks (vponcova)
- network: split function for generating dracut arguments (#1751189) (rvykydal)
- network: generate dracut arguments from connections (#1751189) (rvykydal)
- network: do not touch iBFT connections created in initramfs (#1751189)
  (rvykydal)
- Increase EFI System Partition (ESP) size to 200-600 MiB (javierm)

* Tue Sep 17 2019 Martin Kolman <mkolman@redhat.com> - 32.5-1
- payload module: update live image tar payload options with --numeric-owner
  (rvykydal)
- payload module: add tests for live image payload interface (rvykydal)
- Only partitions have the is_magic attribute (#1625154) (vponcova)
- network gui: wrap multiple IP addresses in network spoke (#1593561)
  (rvykydal)
- Don't use update_storage_ksdata in tests (vponcova)
- Verify existing unlocked LUKS devices without keys (#1624617) (vponcova)
- network tui: fix addr_str referenced before assignment (#1731415) (rvykydal)
- Fix the second screen of Welcome to Fedora (#1748203) (vponcova)
- Add a space after the comma in the description (junjieyuanxiling)
- Use numbers for user/group names when unpacking tar live image (356889)

* Thu Sep 05 2019 Martin Kolman <mkolman@redhat.com> - 32.4-1
- Add tests for the device factory requests (vponcova)
- Raise an exception if the device type is unsupported (vponcova)
- Fix: Move the code for getting the device LUKS versions (vponcova)
- Use a device factory request to populate the right side (vponcova)
- Improve logging of the custom spoke (vponcova)
- Use the device factory request to change devices (vponcova)
- Generate a device factory request (vponcova)
- Use a device factory request to add a mount point (vponcova)
- Add support for transforming device factory requests to arguments (vponcova)
- Add DBus support for the device factory request (vponcova)
- Fix tests after using flatpak format_ref method (jkonecny)
- Use flatpak API to create ref string (jkonecny)
- network: make sure configuration from boot options has ONBOOT=yes (#1727904)
  (rvykydal)
- network: fix dumping of generic "Wired connection" created in initramfs
  (#1727904) (rvykydal)
- Make clear where repo names are used not objects (jkonecny)
- Remove __main__ functions for testing (vponcova)
- Drop dhclient requirement (pbrobinson)
- Compare normalized XML strings (vponcova)
- Add temporal pylint false positive (jkonecny)
- Make default state of treeinfo repos configurable by product (riehecky)
- Fix pylint test by loading C extensions (jkonecny)
- Drop dhclient requirement (pbrobinson)
- Fall back to a boot drive with a valid stage1 device (#1168118) (vponcova)
- Use test dependencies from Fedora instead of pip (jkonecny)
- Do not crash test env setup in case of empty list (jkonecny)
- Fix parsing of hostname from cmdline for ipv6. (rvykydal)
- dnfpayload: repo in _fetch_md is a dnf repo not ksrepo (awilliam)
- Don't set up a warning label to None (#1745933) (vponcova)
- Add DBus support for shrinking devices (vponcova)
- Add DBus support for removing devices (vponcova)
- Devices to be shrinked are always resizable (vponcova)
- Identify devices by theirs names in the resize dialog (vponcova)
- Refactorize the ResizeDialog (vponcova)
- network module: guard onboot configuration task by environment (rvykydal)
- network: modify autoactivate via NM API with a separate task (rvykydal)
- network: get ONBOOT values from NM connections (rvykydal)
- network: activate connections during initramfs consolidation synchronously
  (rvykydal)
- network: block autoactivation also when updating iniramfs connection
  (rvykydal)
- network: find initramfs connections even without ifcfg files (#1727904)
  (rvykydal)
- network: block autoactivation when adding connection from kickstart
  (rvykydal)
- network: split the function for adding a connection from kickstart (rvykydal)
- network: implement NM connection change commit using Update2() (rvykydal)
- network: fix setting real ONBOOT for inactive vlan devices (rvykydal)
- network: modify ONBOOT via libnm during network initialization (rvykydal)
- network: set autoconnect/ONBOOT to yes for default connection in tui
  (rvykydal)
- network: get rid of ONBOOT workaround in tui (rvykydal)
- More detailed addon logging (riehecky)
- Revert "Keep getSysroot for kdump-anaconda-addon" (vponcova)

* Mon Aug 26 2019 Martin Kolman <mkolman@redhat.com> - 32.3-1
- Use the task container to publish tasks (vponcova)
- Remove publish_task (vponcova)
- Make tasks publishable (vponcova)
- Create and set up the DBus container for tasks (vponcova)
- Add note to fix time consuming live os dbus task (jkonecny)
- Add notes for the future work on the module payloads (jkonecny)
- Move constants specific for copy dd task (jkonecny)
- Add test for updating bls entries task (jkonecny)
- Add test for Live OS post installation task (jkonecny)
- Add test for create_rescue_image function (jkonecny)
- Add Live OS handler test for install with task (jkonecny)
- Add live payload handler test for InstallWithImageTask (jkonecny)
- Improve tests for live os image detection code (jkonecny)
- Add live os test for kernel version list (jkonecny)
- Make consistent imports (jkonecny)
- Replace getSysroot by conf value (jkonecny)
- Move get_dir_size test to the payload module tests (jkonecny)
- Move get_dir_size function to the payload.base.utils (jkonecny)
- Rename GetDirSize to get_dir_size (jkonecny)
- Add sysroot param to the copy DD files task (jkonecny)
- Change write module blacklist to take sysroot param (jkonecny)
- Change create root dir func to take sysroot param (jkonecny)
- Add sysroot param to prepare installation task (jkonecny)
- Rename payload shared to base (jkonecny)
- Add Live OS handler space required test (jkonecny)
- Inline copy driver disk payload function to task (jkonecny)
- Add API for required space to live os payload handler (jkonecny)
- Add copy DD files task to live image payload handler (jkonecny)
- Use new task copy driver disks files to old payload (jkonecny)
- Add copy DD files as post install task to live os handler (jkonecny)
- Add post-installation task to live os payload handler (jkonecny)
- Do a facelift to the old copy driver disk function (jkonecny)
- Moved copy driver disk to the payload module shared (jkonecny)
- Use new shared task in the old payload module (jkonecny)
- Add test for prepare installation payload task (jkonecny)
- Add tests for payload module shared utils (jkonecny)
- Create and use task to prepare installation for LiveOS (jkonecny)
- Move payload shared code for handlers to a directory (jkonecny)
- Move write module blacklist to paylod module (jkonecny)
- Move create root directory to its own function (jkonecny)
- Add install task with API to Live OS handler (jkonecny)
- Add kernel version list support to live os handler (jkonecny)
- Fix noverifyssl when downloading .treeinfo file (#1723811) (jkonecny)
- Add the DBus property PartitioningMethod (vponcova)
- Add support for dynamic partitioning modules (vponcova)
- Make partitioning modules publishable (vponcova)
- Create the partitioning factory (vponcova)
- Use a DBus container for the device trees (vponcova)
- Add support for DBus containers (vponcova)
- Add a simple unit test for TUI and GUI (vponcova)
- Add logic to create flatpaks rpmostree payload (#1734970) (jkonecny)
- Move flatpak code to a new ostree payload class (#1734970) (jkonecny)
- Create flatpak in ostree payload only if available (#1734970) (jkonecny)
- Update tests for new class method is_available (#1734970) (jkonecny)
- Make flatpak is_available() a static method (#1734970) (jkonecny)
- Remove the fixed file:// from the flatpak remote (#1734970) (jkonecny)
- Fix payload prepare mount targets install task (#1734970) (jkonecny)
- Merge rpmostreepayload installation under one task (#1734970) (jkonecny)
- Move progress messaging from flatpak to rpmostree (#1734970) (jkonecny)
- Add test for flatpak change remote for refs (#1734970) (jkonecny)
- Replace remote for installed refs in rpmpayload (#1734970) (jkonecny)
- Use new flatpak replace remote on installed refs (#1734970) (jkonecny)
- Add flatpak remote replace for installed refs (#1734970) (jkonecny)
- Make flatpak ref full format method more generic (#1734970) (jkonecny)
- Create an flatpak base ref list object (#1734970) (jkonecny)
- Use flatpak add/remove remotes in ostree payload (#1734970) (jkonecny)
- Add flatpak tests for adding and removing remotes (#1734970) (jkonecny)
- Implement flatpak adding and removing remotes (#1734970) (jkonecny)
- Adapt flatpak tests to the new changes (#1734970) (jkonecny)
- Change flatpak remote logic (#1734970) (jkonecny)
- Rename flatpak REMOTE_NAME to LOCAL_REMOTE_NAME (#1734970) (jkonecny)
- Make flatpak ref lists object consistent (#1734970) (jkonecny)
- Implement object to get installed flatpak refs (#1734970) (jkonecny)
- Add flatpak error reporting implementation (#1734970) (jkonecny)
- Cleanup temp repository of flatpak before install (#1734970) (jkonecny)
- Add and fix tests for newly added flatpak cleanup (#1734970) (jkonecny)
- Add flatpak cleanup method (#1734970) (jkonecny)
- Split flatpak setup to two initialization methods (#1734970) (jkonecny)
- Fix tests after connecting to flatpak signals (#1734970) (jkonecny)
- Add callbacks to monitor flatpak transactions (#1734970) (jkonecny)
- Install flatpaks as part of ostree installation (#1734970) (jkonecny)
- Add test for the flatpak install method (#1734970) (jkonecny)
- Add support to install all remote flatpaks (#1734970) (jkonecny)
- Add flatpak required space test (#1734970) (jkonecny)
- Add get_required_space to the flatpak payload (#1734970) (jkonecny)
- Add flatpak object to abstract flatpak Ref list (#1734970) (jkonecny)
- Don't configure the default target without systemd (#1744115) (vponcova)
- Change flatpak remote name to constant (#1734970) (jkonecny)
- Use FlatpakPayload from the RPMOStreePayload (#1734970) (jkonecny)
- Add test for the flatpak setup method (#1734970) (jkonecny)
- Add method to setup flatpak objects (#1734970) (jkonecny)
- Add flatpak test for remote availability (#1734970) (jkonecny)
- Add check if flatpak remote repo is available (#1734970) (jkonecny)
- Add libflatpak dependency to the anaconda spec (#1734970) (jkonecny)
- Add an empty class to handle flatpak (#1734970) (jkonecny)
- Look for existing installations on existing devices (vponcova)
- Require a mount point only for mountable formats (vponcova)
- Handle the missing mountpoint attribute (#1743853) (vponcova)

* Mon Aug 19 2019 Jiri Konecny <jkonecny@redhat.com> - 32.2-1
- Set the minimum required entropy only once (vponcova)
- Rename the icon (#1740864) (vponcova)
- Format strings with format in interactive utils (vponcova)
- Rename _get_device_info_description in the custom spoke (vponcova)
- Remove pyanaconda.storage.partitioning (vponcova)
- Use the partitioning request in TUI (vponcova)
- Use the partitioning request in GUI (vponcova)
- Update the storage initialization and configuration (vponcova)
- Use the partitioning request in the tests (vponcova)
- Use the partitioning request in the automatic partitioning module (vponcova)
- Use the partitioning request in the automatic partitioning task (vponcova)
- Exclude mount points from the automatic partitioning (vponcova)
- Create a DBus structure for the partitioning request (vponcova)
- Don't load the repo device path twice in the Payload class (vponcova)
- Rename device_path to repo_device_path in the Payload class (vponcova)
- Rename get_mount_device in payload utils (vponcova)
- Remove a redundant condition in the Payload class (vponcova)
- Specify types of arguments in the payload utils (vponcova)
- Use the payload utils in UI (vponcova)
- Add a new function unmount_device to payload utils (vponcova)
- Add a new function setup_device to payload utils (vponcova)
- Add a new function mount_device to payload utils (vponcova)
- Add a new function teardown_device to payload utils (vponcova)
- Move the support methods for image installations (vponcova)
- Change the method for finding potential HDISO sources (vponcova)
- Change the method for finding a valid optical install media (vponcova)
- Add a new function resolve_device to payload utils (vponcova)
- Rename variables and arguments in the Payload class (vponcova)
- Provide a documentation for the payload utils (vponcova)
- Don't propagate the storage and data to the payload again (vponcova)
- Collect addons after running the %%pre section (vponcova)
- Fix: Merge the code for the device info validation (vponcova)
- Fix: Generate the device info in interactive utils (vponcova)
- Fix: Simplify the code for validating mount points (vponcova)
- Handle a missing value of the mount point attribute (vponcova)
- Improve logging of the device info changes (vponcova)
- Remove the constants for the device type strings (vponcova)
- Move the code for collecting supported RAID levels (vponcova)
- Move the code for the device info validation (vponcova)
- Move the code for the raid level validation (vponcova)
- Simplify the code for validating mount points (vponcova)
- Move the code for validating mount points (vponcova)
- Generate the device info in interactive utils (vponcova)
- Simplify overriding disk set with container's (vponcova)
- Simplify the removal of the device (vponcova)
- Merge the code for changing the size (vponcova)
- Move code to the function revert_reformat (vponcova)
- Change arguments of the method for reformatting (vponcova)
- Merge the code for the device info validation (vponcova)
- Split the code for collecting the new device info (vponcova)
- Move the code for collecting the new device info (vponcova)
- Apply the device info changes in new methods (vponcova)
- Remove the code for comparing the device info (vponcova)
- Remove variables for new device info (vponcova)
- Remove variables for old device info (vponcova)
- Move the code for comparing the device info (vponcova)
- Simplify logging of the device infos (vponcova)
- Move the code for the new device info (vponcova)
- Move the code for the old device info (vponcova)
- Add squashfs+overlayfs base live image detection (bcl)
- liveinst: Add support for plain squashfs root filesystem (bcl)

* Wed Aug 14 2019 Martin Kolman <mkolman@redhat.com> - 32.1-1
- Use append_dbus_tasks() for DBus Task scheduling (mkolman)
- Add append_dbus_task method to TaskQueue (mkolman)
- Replace Firewall and Network command setup() method (mkolman)
- Add support for localization of modules (rvykydal)
- Don't measure code coverage during the installation (vponcova)
- Use the new discovery & join DBUS tasks (mkolman)
- Increase network timeout constant (jkonecny)
- Add DBUS Tasks for realm discovery & joining a realm (mkolman)
- Add the add_requirements() method for PayloadRequirements (mkolman)
- Extend RealmData (mkolman)
- Set timeout for all session.get calls (jkonecny)
- Add support for disabling modules via module --disable (mkolman)
- Don't check the format status in UI (vponcova)
- Fix updating of ifcfg files for ifname= bound devices (#1727904) (rvykydal)
- network module: be more strict when adding physical device configuration
  (#1727904) (rvykydal)
- Adapt to changes caused by NM in initramfs (#1727904) (rvykydal)
- Change the documentation of the 'reason' attribute (vponcova)
- Fix traceback in network module installation task. (rvykydal)
- Remove the connect method of DBusObserver (vponcova)
- Remember which modules are addons (vponcova)
- Simplify the initialization of the module observer (vponcova)
- Remove the support for the object observer (vponcova)
- Move the module manager to a new subpackage (vponcova)

* Wed Jul 31 2019 Martin Kolman <mkolman@redhat.com> - 31.22-1
- Fix pylint warning (vponcova)
- Keep getSysroot for kdump-anaconda-addon (vponcova)
- Specify sizes of nonexistent devices in tests (vponcova)
- network tui: fix a typo concerning inifiniband device configuration
  (rvykydal)
- Remove the object observers from UI (vponcova)
- Remove the method changed (vponcova)
- Move the preserved arguments to the Anaconda configuration file (vponcova)
- Remove system root from DBus methods (vponcova)
- Rename setSysroot (vponcova)
- Replace getSysroot (vponcova)
- Replace getTargetPhysicalRoot (vponcova)
- Replace publisher patches with the new solution (jkonecny)
- Handle disk selection errors in get_candidate_disks (vponcova)
- Don't verify mounted partitions of protected disks (vponcova)
- Always protect the live backing device (#1706335) (vponcova)
- Don't change the storage if the reset fails (vponcova)
- Remove support for teardown before storage reset (vponcova)

* Thu Jul 25 2019 Jiri Konecny <jkonecny@redhat.com> - 31.21-1
- Always schedule the installation task for joining realm (#1732620) (vponcova)
- Fix issue raised by giving publisher as last parameter (jkonecny)
- Use the new publisher patch decorator in a tests (jkonecny)
- Add decorator as shortcut for a publisher patching (jkonecny)
- Add test for creating invalid payload handler (jkonecny)
- Fix tests after removing handlers publish method (jkonecny)
- Remove _publish_handler method from payload module (jkonecny)
- Fix tests because of new payload API change (jkonecny)
- Remove get_handler_path from payload handlers (jkonecny)
- Return path from payload handler publish methods (jkonecny)
- Join all the payload handler create methods (jkonecny)
- Publish payload handler after KS data are parsed (jkonecny)
- Add handler factory and use that in payload module (jkonecny)
- Add tests for new payload API (jkonecny)
- Do not create payload handler if already set (jkonecny)
- Add API to test if there is a payload handler set (jkonecny)
- Do not set default payload handler (jkonecny)
- Don't prune and sort actions in the partitioning task (vponcova)
- Fix imports in the tests (jkonecny)
- Adapt payload tests to a new task check function (jkonecny)
- Adapt network tests to a new task check function (jkonecny)
- Adapt localization tests to a new task check function (jkonecny)
- Adapt bootloader test to a new task check function (jkonecny)
- Adapt storage tests to a new check task function (jkonecny)
- Make a new test func to check task creation (jkonecny)
- Add test for new payload API on live image creation (jkonecny)
- Add new payload API to create live image handler (jkonecny)
- Add tests for new payload handlers solution (jkonecny)
- Fix tests after payload handler logic change (jkonecny)
- Add support to create DNF payload handler (jkonecny)
- Improve payload handler creation abstraction (jkonecny)
- Publish payload handler before it is set (jkonecny)
- Fix payload generate_kickstart with no handler (jkonecny)
- Add payload module API to get active handler (jkonecny)
- Publish handler in the creation method call (jkonecny)
- Propagate DBus path when creating handler (jkonecny)
- Use base handler class by the handler modules (jkonecny)
- Add payload handler base class (jkonecny)
- Change main payload handlers to property (jkonecny)
- Add root password SSH login override checkbox (#1716282) (mkolman)

* Mon Jul 22 2019 Jiri Konecny <jkonecny@redhat.com> - 31.20-1
- Move code to exctract kernel version from tar to utils (jkonecny)
- Add link for our translations to README (#1729788) (jkonecny)
- Change Makefile zanata client check from pkg to bin (jkonecny)
- Add recommendation to release process guide (jkonecny)
- Remove unnecessary step from release in mock doc (jkonecny)
- Fix mock release dependency in a mock (jkonecny)
- Fix: Simplify the code for creating container store rows (vponcova)
- Fix a docstring of add_device (vponcova)
- Get the current device type only once (vponcova)
- Move the code for getting the name of the new root (vponcova)
- LiveImagePayload: move some functions to utils.py (rvykydal)
- LiveImagePayload: replace PostInstallTask with UpdateBLSConfigurationTask
  (rvykydal)
- LiveImageHandler: make API and implementation method names consistent
  (rvykydal)
- LiveImageHandler: use more descriptive names for installation tasks
  (rvykydal)
- LiveImagePayload: Do not provide API for setting of required space (rvykydal)
- LiveImageHandler: prevent reusing of DownloadProgress instance (rvykydal)
- LiveImageHandler: simplify using of SetupInstallationSourceImageTask result
  (rvykydal)
- LiveImageHandler: simplify using of CheckInstallationSourceImageTask result
  (rvykydal)
- LiveImageHandler: remove interfaces for task results we don't need (rvykydal)
- Add logging to interactive utils (vponcova)
- Fix the FIXME comment for collect_selected_disks (vponcova)
- Rename the argument for the boot drive (vponcova)
- Remove empty lines in collect_used_devices (vponcova)
- Fix: Move the code for collecting device types (vponcova)
- Fix: Move the code for completing the device info (vponcova)
- Fix: Move the code for hiding protected disks to InstallerStorage (vponcova)
- Move the code for suggesting device names (vponcova)
- Fix: Move the code for getting a container device (vponcova)
- Fix: Move the code for collecting device types (vponcova)
- Fix pylint issues in the custom spoke (vponcova)
- Move the code for label validation (vponcova)
- Move the code for collecting supported mount points (vponcova)
- Show a detailed warning in the custom spoke (vponcova)
- Show a detailed error in the custom spoke (vponcova)
- Move the code for collecting containers (vponcova)
- Move the code for getting a container device (vponcova)
- Populate a container for the given device (vponcova)
- Simplify the code for creating container store rows (vponcova)
- Move the code for renaming containers (vponcova)
- Move the code for destroying devices (vponcova)
- Remove the method for removing empty parents (vponcova)
- Move the code for completing the device info (vponcova)
- Move the code for creating devices (vponcova)
- Move the function get_device_raid_level (vponcova)
- Refactor the code for setting up the device types (vponcova)
- Move the code for collecting device types (vponcova)
- Move the code for collecting file system types (vponcova)
- Move the code for getting the device LUKS version (vponcova)
- Move the code for the device reformatting (vponcova)
- Move the code for changed encryption (vponcova)
- Move the code for changing the device size (vponcova)
- Move the code for reverting reformat (vponcova)
- Collect roots with supported devices (vponcova)
- Move the code for adding the unknown page (vponcova)
- Move the code for adding the root page (vponcova)
- Move the code for creating a new root (vponcova)
- Move the code for adding the initial page (vponcova)
- Move the code for collecting roots to interactive utils (vponcova)
- Move constants and function from custom_storage.py (vponcova)
- Optimize the method _update_space_display of the custom spoke (vponcova)
- Remove the method _current_total_space from the custom spoke (vponcova)
- Remove the method _set_current_free_space of the custom spoke (vponcova)
- Move the code for hiding protected disks to InstallerStorage (vponcova)
- Don't check if disks have media present (vponcova)
- Rename _clearpart_devices in CustomPartitioningSpoke (vponcova)
- Rename get_new_devices in CustomPartitioningSpoke (vponcova)
- Fix: Remove bootloader_devices from CustomPartitioningSpoke (vponcova)
- Fix: Remove unused_devices from CustomPartitioningSpoke (vponcova)
- Remove bootloader_devices from CustomPartitioningSpoke (vponcova)
- Remove the attribute _devices from CustomPartitioningSpoke (vponcova)
- Remove unused_devices from CustomPartitioningSpoke (vponcova)
- Remove the property unused_devices from InstallerStorage (vponcova)
- Remove banners (vponcova)
- Replace the Progress hub (vponcova)
- Remove useless class attributes from SpokeCategory (vponcova)
- LiveImageHandler: add progress reporting of download (rvykydal)
- LiveImageHandler: split out Teardown task from PostInstall (rvykydal)
- LiveImageHandler: pass source image mount point as argument to tasks
  (rvykydal)
- LiveImageHandler: PostInstallWithTask() 2/2 (rvykydal)
- LiveImagehandler: InstallWithTask() (rvykydal)
- LiveImageHandler: UpdateKernelVersionList() (rvykydal)
- LiveImageHandler: PostInstallWithTask() 1/2 (rvykydal)
- Change the sort order of the User Settings category (vponcova)
- Move all spokes to the Summary hub (vponcova)
- LiveImageHandler: PreInstallWithTask() (rvykydal)
- LiveImageHandler: SetupWithTask() (CheckInstallationSourceImage) (rvykydal)

* Thu Jul 11 2019 Jiri Konecny <jkonecny@redhat.com> - 31.19-1
- Call teardown_all explicitly (vponcova)
- Don't publish the module in the loop (vponcova)
- Start swap on ZRAM service (cmurf)
- Use %%autosetup instead of %%setup (mkolman)
- Adjust the exclude arguments for livepayloads (bcl)
- Recreate the BLS entries when using liveimg (bcl)
- Cache the liveimg tar kernel list (bcl)
- Add common function for creating rescue images (bcl)
- move comment into docstring for PowerNVGRUB2 install method (dan)
- add PowerNV into BootloaderClassTestCase (dan)
- LiveImage payload: clean up directory used for image mounting (rvykydal)
- LiveImage payload: mount live image privately (rvykydal)
- introduce PowerNV variant for grub2 class (dan)
- initial PowerNV class support (dan)
- Add the option decorated_window to the Anaconda configuration (vponcova)
- Add test for Live OS detect live os image feature (jkonecny)
- Add Live OS base image detection code (jkonecny)
- Add tests for the new Live OS tasks (jkonecny)
- Add Live OS handler tests for ImagePath property (jkonecny)
- Implement teardown to Live OS payload handler (jkonecny)
- Add support to create Live OS handler manually (jkonecny)
- Implement SetupInstallationSource Live OS task (jkonecny)
- Add ImagePath property to the Live OS handler (jkonecny)
- Add an empty LiveOS payload handler (jkonecny)
- Don't use the auto partitioning module in the custom spoke (vponcova)
- Add support for decomposing DBus values (vponcova)
- Use the default file system type for /boot (vponcova)
- Move updates reponames to constants (riehecky)
- Fix setting and reporting ready state in Source Spoke. (rvykydal)

* Tue Jun 25 2019 Jiri Konecny <jkonecny@redhat.com> - 31.18-1
- Add comprehensive unit tests for ConfigureFirewallTask (mkolman)
- Fix a typo (mkolman)
- Use FirewallMode enum firewall configuration DBus Task (#1722979) (mkolman)
- Don't encrypt devices in the interactive partitioning by default (vponcova)
- Provide a default passphrase for the PassphraseDialog (vponcova)
- Set the passphrase for the automatic partitioning from the dialog (vponcova)
- Don't use the global encryption passphrase (vponcova)
- Add support for passphrases in the device tree module (vponcova)
- Handle the passphrase requirements in the partitioning modules (vponcova)
- Use _get_passphrase in the custom partitioning task (vponcova)
- Don't generate passphrases in a kickstart file (vponcova)
- Fix the unit tests for the Services module (vponcova)
- Convert names of attributes and variables in custom storage helpers
  (vponcova)
- Fix code alignment in the custom storage helpers (vponcova)
- Convert names of attributes and variables in the custom spoke (vponcova)
- Remove local variables with unused values in the custom spoke (vponcova)
- Fix code alignment in the custom spoke (vponcova)
- Initialize attributes in the __init__ method of the custom spoke (vponcova)
- Reorganize imports in the custom spoke (vponcova)

* Mon Jun 24 2019 Martin Kolman <mkolman@redhat.com> - 31.17-1
- Move graphical login detection to a DBus Task (#1722950) (mkolman)
- Add DBus support for device trees of partitioning modules (vponcova)
- Create the interactive partitioning module (vponcova)
- Fix misleading comment (riehecky)

* Thu Jun 20 2019 Martin Kolman <mkolman@redhat.com> - 31.16-1
- Replace the XConfig execute() method by DBus Tasks (mkolman)
- Fix list-screens script reference (gpchelkin)
- Fix protecting of the live device (#1699387) (vponcova)
- Adapt tests for new Live payload handler changes (jkonecny)
- Add setters to LiveImage payload handler (jkonecny)
- Rename Live payload handler to LiveImage (jkonecny)
- Extend payload live handler with new properties (jkonecny)
- Add read only properties to payload Live handler (jkonecny)
- Add the apply-updates script (vponcova)
- Add payload live handler tests (jkonecny)
- Update payload DNF handler tests (jkonecny)
- Create a new payload handler mixin class for tests (jkonecny)
- Improve the documentation of inst.stage2.all and inst.ks.all (vponcova)
- Add DBus support for teardown tasks (vponcova)
- Tear down images with teardown_disk_images (vponcova)
- Move get_anaconda_version_string to util (vponcova)
- Support multiple payload handlers (jkonecny)
- Add kickstart processing to payload live handler (jkonecny)
- Create Live payload handler module (jkonecny)
- Deprecate the method changed (vponcova)
- Calculate free space for the physical root in dir installations (vponcova)
- Use the actual sysroot to pick up a mount point for downloading (vponcova)
- Use the physical root for mounting existing systems (vponcova)
- Change the path to the system root (vponcova)
- Read files in /etc/anaconda/conf.d on demand (vponcova)

* Thu Jun 13 2019 Martin Kolman <mkolman@redhat.com> - 31.15-1
- iscsi: require relevant blivet version for iscsi module (rvykydal)
- iscsi: add unit tests for iscsi module (rvykydal)
- iscsi: fix name of some method arguments (target -> portal) (rvykydal)
- iscsi: use proper iscsi interface mode constants in ui (rvykydal)
- iscsi: update the CanSetInitiator docstring to reflect the reality (rvykydal)
- iscsi: move conversion to IscsiInterfacesMode from implementation to
  interface (rvykydal)
- iscsi: use better name for a NodeIsFromIbft method (rvykydal)
- iscsi: move kickstart iscsi processing into the iSCSI module (rvykydal)
- iscsi: attach iBFT targets in early kickstart by the iSCSI module (rvykydal)
- iscsi gui: show target in Target column (not initiator) (rvykydal)
- iscsi: rename iSCSI node info attribute holding name of iscsi interface
  (rvykydal)
- iscsi: move dracut argument generating into the iSCSI module (rvykydal)
- iscsi: get info about target being added from iBFT from the iSCSI module
  (rvykydal)
- iscsi: use attributes added blivet iscsi device replacing iscsi node object
  (rvykydal)
- iscsi: rename Target to Portal where appropriate (rvykydal)
- iscsi: move kickstart data update to the iSCSI module (rvykydal)
- iscsi: write configuration by the iSCSI module (rvykydal)
- iscsi: use the iSCSI module by kickstart iscsi command (rvykydal)
- iscsi: use the iSCSI module in GUI (rvykydal)
- Adapt iSCSI structures to dbus structure updates (rvykydal)
- Use the ISCSI module in the ISCSIDialog (vponcova)
- Create DBus tasks for discovering iSCSI nodes (vponcova)
- Create the basic structure for the iSCSI module (vponcova)
- Hide spokes in Silverblue and Workstation (vponcova)
- Remove the screen access management (vponcova)
- Hide spokes with the Anaconda configuration file (vponcova)
- Run the DBus task for configuration of post-installation tools (vponcova)
- Replace the lang execute() method (mkolman)
- Collect requirements of the Storage module (vponcova)
- Add DBus support for module requirements (vponcova)
- Replace the Services execute() method by a DBus Task (mkolman)
- Replace the SELinux execute() method by a DBus Task (mkolman)
- Replace the Firewall execute() method by a DBus Task (mkolman)
- Add FirewallConfigurationTask DBus Task (mkolman)
- Add root parameter to execInSysroot utility function (mkolman)
- Improve post install tools configuration (mkolman)

* Fri May 31 2019 Martin Kolman <mkolman@redhat.com> - 31.14-1
- Require langtable-0.0.44, drop langtable-data requirement (mfabian)
- Extend the format data with the mountable property (vponcova)
- Add DBus support for supported file system types (vponcova)
- Add DBus support for getting format type data (vponcova)
- Add DBus support for gathering mount point requests (vponcova)
- Move tests for partitioning modules to new files (vponcova)
- Add DBus support for populating a device tree (vponcova)
- Don't define the __eq__ method of DBusData (vponcova)
- Add DBus support for mounting the existing system (vponcova)
- Extend the function mount_existing_system (vponcova)
- Add DBus support for finding existing operating system (vponcova)
- Simplify generate_string_from_data (vponcova)
- Define the __eq__ method of DBusData (vponcova)

* Mon May 27 2019 Martin Kolman <mkolman@redhat.com> - 31.13-1
- Parse the output of df correctly (#1708701) (vponcova)
- Skip scaling if there is no primary monitor (#1592014) (vponcova)
- Document how to report a bug (vponcova)
- Handle post inst tools toggling in screen access manager (mkolman)
- Fix a typo in Initial Setup configuration task (mkolman)
- Remove methods _setup_mount_data and _process_mount_data (vponcova)
- Rename MountPoint to MountPointRequest (vponcova)
- Add tests for the storage checker module (vponcova)
- Add DBus support for setting a constraint (vponcova)
- Don't check the storage in a separate thread (vponcova)
- Remove HMC from flags (jkonecny)
- Rename the method add_new_constraint (vponcova)
- Rename the method add_constraint (vponcova)
- Remove the update_constraint method (vponcova)
- Create the DBus module for the storage checker (vponcova)
- Use MountPoint in TUI (vponcova)
- Use MountPoint in ManualPartitioningTask (vponcova)
- Use MountPoint in tests (vponcova)
- Use MountPoint as DBus structure (vponcova)
- Cleanup long removed "headless" option from docs (mkolman)

* Wed May 15 2019 Martin Kolman <mkolman@redhat.com> - 31.12-1
- Fix condition for running GUI User spoke in Initial Setup (mkolman)
- Expose individual user group, user and root password DBus tasks (mkolman)
- Use a DBus task for Initial Setup configuration (mkolman)
- Add ConfigureInitialSetupTask (mkolman)
- Sysroot support for enable_service() and disable_service() (mkolman)
- Fix documentation for nosslverify (jkonecny)
- Replace noverifyssl flag in anaconda (jkonecny)
- Adjust verify_ssl config from cmdline (jkonecny)
- Move payload nosslverify to the config files (jkonecny)
- Skip some of the driver disk tests (vponcova)
- Use the absolute paths to set the testing environment (vponcova)
- Use DBus consistently (mkolman)
- Test generate_string_from_data with invalid argument (vponcova)
- Make from_structure and to_structure more strict (vponcova)

* Thu May 02 2019 Martin Kolman <mkolman@redhat.com> - 31.11-1
- Remove no longer needed kickstart command overrides (mkolman)
- Use Users DBUS module for user configuration in GUI (mkolman)
- Use Users DBUS module for user configuration in TUI (mkolman)
- Adjust Users module DBus API for better kickstart root configuration
  (mkolman)
- Use DBusData base class for data holders (mkolman)
- Add a string representation for UserData (mkolman)
- Add ui/lib/users.py (mkolman)
- Use a constant for the UID/GID not set value (mkolman)
- Improve ksdata <-> user data methods in Users DBUS module (mkolman)
- Do root, group, user and SSH key configuration with DBUS tasks (mkolman)
- Add tasks for root, user, group and ssh key configuration (mkolman)
- Fix indentation for user creation method docstring (mkolman)
- Drop support for using custom password crypt algorithm (mkolman)
- Make clear_root_password() into set_root_password() alias (mkolman)
- Lock root & user accounts if password in kickstart is empty (mkolman)
- Convert create_user() from kwargs to optional args (mkolman)
- Convert create_group() from kwargs to optional args (mkolman)
- Mark the root account as locked by default (mkolman)
- Add docstrings & some signature tweaking in users.py (mkolman)
- Move methods from User class to module top-level (mkolman)
- Apply PEP8 for method names in users.py (mkolman)
- Move user management code to core (mkolman)
- Use Pykickstart data classes via handler (mkolman)
- Add API for easy admin user detection (mkolman)
- Add support for SSH key management via the users DBUS module (mkolman)
- Add support for group management via the users DBUS module (mkolman)
- Add support for managing multiple users to the users module (mkolman)

* Tue Apr 30 2019 Martin Kolman <mkolman@redhat.com> - 31.10-1
- get_iface_from_hwaddr: be more careful about hwaddr (#1703152) (awilliam)
- network: fix a typo in infiniband connections creating (#1698937) (rvykydal)
- network: do not crash on --device bootif when BOOTIF is not specified
  (#1699091) (rvykydal)
- Add DBus support for the device specifier for use in /etc/fstab (vponcova)
- Set swap devices for fstab in the interactive partitioning (vponcova)
- Refactor the passphrase setup on unconfigured LUKS devices (vponcova)
- Add DBus support for UUID (vponcova)
- Add DBus support for device format (vponcova)
- Add DBus support for unlocking LUKS devices (vponcova)
- Add DBus support for finding mountable partitions (vponcova)
- We inherit self.data.repo.dataList() from parent class. (riehecky)

* Thu Apr 11 2019 Martin Kolman <mkolman@redhat.com> - 31.9-1
- Remove the function get_structure (vponcova)
- Remove the function apply_structure (vponcova)
- Remove the decorator (vponcova)
- Add the class DBusData (vponcova)
- Give payload a hook for adding disabled repos. (riehecky)
- Extend the function generate_string_from_data (vponcova)
- Blivet-GUI should wait for the storage threads to finish (#1696478)
  (vponcova)
- network: do not pass None value from NM device object to data holder
  (#1695967) (rvykydal)
- Handle bytes and strings from RPM (#1693766) (vponcova)
- network module: add network module unit tests (rvykydal)

* Tue Apr 09 2019 Martin Kolman <mkolman@redhat.com> - 31.8-1
- network: create systemd .link files for ifname= boot options (#1695894)
  (rvykydal)
- Bump Workstation root partition max size to 70 GiB (klember)
- Add DBus support for finding optical media (vponcova)
- Add DBus support for handling a device (vponcova)
- Do not use ISO source as install tree root (#1691832) (jkonecny)
- Fix bad assumption about base repo identification (#1691832) (jkonecny)
- network tui: fix updating of a connection from UI (#1692677) (rvykydal)
- network: fix copying of resolv.conf for cases where target /etc does not
  exist (#1695990) (rvykydal)
- network: fix crash ensuring single connections for unplugged devices
  (#1695899) (rvykydal)
- Add support for skipping attributes in the string representation (vponcova)
- Raise the UnknownDeviceError exception (vponcova)
- Add DBus support for resolving devices (vponcova)
- Add DBus support for the available space (vponcova)
- Move GetRequiredDeviceSize to the device tree module (vponcova)
- Create the device tree module (vponcova)
- Don't set the __repr__ methods of data classes (vponcova)
- network: for vlan set DEVICE only if interfacename is specified in kickstart
  (rvykydal)
- Change fips package requirement reason (jkonecny)
- payload: raise exception on invalid Languages (jkonecny)
- payload: Mark DefaultEnvironment API as temporary (jkonecny)
- payload: fix default values for packages section (jkonecny)
- Remove unused import for DNF (jkonecny)
- payload: add converter for kickstart groups (jkonecny)
- payload: switch multilib policy to names (jkonecny)
- payload: add rest of the DNF/Packages attributes (jkonecny)
- payload: add packages controlling properties (jkonecny)
- payload: add package groups interface to Packages (jkonecny)
- payload: adjust packages section attributes (jkonecny)
- payload: move %%packages parsing to DNF/Packages (jkonecny)
- payload: add DBus packages dnf submodule (jkonecny)
- payload: add the empty DNF handler (jkonecny)
- payload: create internal Packages class (jkonecny)
- payload: parse %%packages section in module (jkonecny)

* Tue Apr 02 2019 Martin Kolman <mkolman@redhat.com> - 31.7-1
- Create the initialization config in _get_initialization_config (vponcova)
- Remove config from InstallerStorage (vponcova)
- Update DiskInitializationConfig only before clearpart (vponcova)
- Create the method can_initialize (vponcova)
- Remove should_clear from InstallerStorage (vponcova)
- Remove clear_partitions from InstallerStorage (vponcova)
- Replace StorageDiscoveryConfig (vponcova)
- Update the protected devices in the Storage module (vponcova)
- Import the bootloader classes on demand (vponcova)
- Remove bootloader_device from InstallerStorage (vponcova)
- Remove update_bootloader_disk_list from InstallerStorage (vponcova)
- Remove boot_fstypes of InstallerStorage (vponcova)
- Remove set_up_bootloader from InstallerStorage (vponcova)
- Define all bootloader attributes in the __init__ method (vponcova)
- Remove workarounds for the unset bootloader (vponcova)
- Clean up the do_it method of the storage (vponcova)
- Validate the GRUB2 configuration in the Bootloader module (vponcova)
- Add DBus support for the bootloader arguments (vponcova)
- Add DBus support for detecting Windows OS (vponcova)
- Add DBus support for EFI (vponcova)
- Add DBus support for the bootloader installation tasks (vponcova)
- Add DBus support for usable disks (vponcova)
- Apply the disks selection in the partitioning modules (vponcova)
- Remove the function get_available_disks (vponcova)
- Organize actions in InteractivePartitioningTask (vponcova)
- Add DBus support for device actions (vponcova)
- Simplify ActionSummaryDialog (vponcova)
- Set up the clearpart command from the storage (vponcova)
- payload: request /usr/bin/fips-mode-setup (zbyszek)
- Fix the entry for swap in /etc/fstab (#1258322) (vponcova)
- Add DBus support for disk images (vponcova)
- Remove askmethod flag (jkonecny)
- Fix two typos (zbyszek)
- Disable updates-testing (#1670091) (vponcova)
- network module: return slaves in set and order them predictably in generated
  ks (rvykydal)
- network module: update ifcfg.py unit tests for getting ifcfg file on s390
  (rvykydal)
- network module: fix getting ifcfg file for s390 (rvykydal)
- network module: remove unused functionality from get_ifcfg_file (rvykydal)
- network module: unit tests for update onboot functions in ifcfg.py (rvykydal)
- network module: add TODO to ifcfg.py tests (rvykydal)
- network module: ifcfg.py tests - no need for ifcfg for vlan bound to device
  (rvykydal)
- network module: add ifcfg.py unit tests (rvykydal)
- network module: do not try to generate ksdata from wireless device ifcfg
  (rvykydal)
- network module: fix a typo in function name (rvykydal)
- network module: allow to generate ifcfg files in optional root (rvykydal)
- network module: fix thinko (rvykydal)
- network module: rename _ifcfg_files method (rvykydal)
- network module: fix a super call (rvykydal)
- Fix the unit tests (vponcova)

* Thu Mar 21 2019 Martin Kolman <mkolman@redhat.com> - 31.6-1
- Test the DBus support for the device tree (vponcova)
- Add DBus support for the device tree (vponcova)
- Fix the initialization of BootInfo (#1599378) (vponcova)
- network module: update module API unit tests (rvykydal)
- network module: guard some methods on NM availability (rvykydal)
- Remove useless swapoff (vponcova)
- Always specify the LUKS version in CustomPartitioningSpoke (#1689699)
  (vponcova)
- Remove the property free_space_snapshot from InstallerStorage (vponcova)
- network: fix setting of NetworkDeviceInfo from NM Device (rvykydal)
- Hide the encryption checkbox for the interactive partitioning (vponcova)
- Deprecate DBusObjectObserver (vponcova)
- Remove DBusCachedObserver (vponcova)
- Add the method get_file_system_free_space to InstallerStorage (vponcova)
- Use get_disk_free_space and get_disk_reclaimable_space in StorageSpoke
  (vponcova)
- Use get_disk_free_space in ResizeDialog (vponcova)
- Use get_disk_free_space in CustomPartitioningSpoke (vponcova)
- Use get_disk_free_space in SelectedDisksDialog (vponcova)
- network: adapt a unit test to get_supported_devices change (rvykydal)
- Don't estimate the free space based on the clearpart settings (vponcova)
- Update the kickstart data for iSCSI and NVDIMM during the installation
  (vponcova)
- network: share single NM Client in anaconda (rvykydal)
- network: handle ONBOOT in ifcfg by network module (rvykydal)
- network: network.py cleanup (rvykydal)
- Don't generate temporary kickstart in the Storage module (vponcova)
- Remove attributes for autopart encryption from the InstallerStorage
  (vponcova)
- Make invalid installation from HDD more visible (jkonecny)
- network module: fix updating of ONBOOT value on installed system (rvykydal)
- network: remove nm.py (rvykydal)
- network: use libnm to get device IP addresses (rvykydal)
- network: use libnm to get ntp servers from dhcp options (rvykydal)
- network module: provide and use GetActivatedInterfaces (rvykydal)
- network: remove unused stuff from nm.py (rvykydal)
- network: use GetSupportedDevices API (rvykydal)
- network module: provide GetSupportedDevices (rvykydal)
- Remove the encrypted_autopart property of the InstallerStorage (vponcova)
- Remove the autopart_type property of the InstallerStorage (vponcova)
- Remove the autopart_requests property of the InstallerStorage (vponcova)
- Remove the do_autopart property of the InstallerStorage (vponcova)
- Move the support for scheduling partitions to the Storage module (vponcova)
- Move do_autopart to the Storage module (vponcova)
- Move do_reqpart to the Storage module (vponcova)
- Add a new task for interactive auto partitioning (vponcova)
- Replace the function do_kickstart_storage (vponcova)
- Replace partitioning executors with tasks (vponcova)
- Move partitioning executors to the Storage module (vponcova)
- Move swap_suggestion to pyanaconda.storage.utils (vponcova)
- network: remove ifcfg.log (rvykydal)
- network module: log configuration state after installation task (rvykydal)
- network: remove low-level debug logging on IfcfgFile modifications (rvykydal)
- network module: use module for logging of configuration state (rvykydal)
- network module: move ifcfg logging into the module (rvykydal)
- network module: do not log secrets (rvykydal)
- network module: rename and add doc to network initialization task interface
  (rvykydal)
- network module: guard initialization tasks by anaconda system configuration
  (rvykydal)
- network: log network initialization better (rvykydal)
- network module: use task to dump missing ifcfg files (rvykydal)
- network module: use task to set real onboot values (rvykydal)
- network module: use task for initramfs connections consolidation (rvykydal)
- network module: use task for apply kickstart (rvykydal)
- payload: separate blivet.utils & blivet.arch call (jkonecny)
- Improve content of the top-level README file (mkolman)

* Tue Mar 12 2019 Martin Kolman <mkolman@redhat.com> - 31.5-1
- Don't run the storage checker to check autopart (vponcova)
- Remove the SnapshotValidateTask class (vponcova)
- Validate post-installation snapshot requests with the storage checker
  (vponcova)
- Add a new type of the installation system for the initial setup (vponcova)
- Simplify update_storage_ksdata (vponcova)
- Don't set anything if the partitioning fails (vponcova)
- Reset the bootloader with reset_bootloader (vponcova)
- Add support for scanning all devices in the system (vponcova)
- Add the ExclusiveDisks property (vponcova)
- Move tests for the disk selection module to a new file (vponcova)
- Replace initialize_storage with reset_storage (vponcova)
- Remove the shutdown method (vponcova)
- payload: don't force host-only mode when executing dracut (javierm)
- Simplify the code for protected devices (vponcova)
- Define the quit message in TUI (#1686116) (vponcova)
- efi: don't include the grub2-pc package on EFI installs (javierm)
- Small optimization in boot arg parsing method (jkonecny)
- Fix bad --addrepo command line parsing (jkonecny)
- Raise correct exception on bad addrepo boot param (jkonecny)
- payload: migrate TUI software spoke to pep8 (jkonecny)
- payload: switch from CamelCase in software spoke (jkonecny)
- payload: remove unused radio button (jkonecny)
- payload: solve basic pep 8 errors (jkonecny)

* Wed Mar 06 2019 Martin Kolman <mkolman@redhat.com> - 31.4-1
- Add tests for UnsupportedPartitioningError (vponcova)
- Handle missing support for Blivet-GUI in the Storage module (#1685645)
  (vponcova)
- Create the default partitioning requests on demand (vponcova)

* Tue Mar 05 2019 Martin Kolman <mkolman@redhat.com> - 31.3-1
- Fix live payload error introduced by clean-up (#1685258) (jkonecny)

* Mon Mar 04 2019 Martin Kolman <mkolman@redhat.com> - 31.2-1
- Get the summary about selected disks from a function (vponcova)
- Replace warnings about disks with constants (vponcova)
- Rename and reorganize members of the storage spoke in TUI and GUI (vponcova)
- Add tests for the Blivet partitioning module (vponcova)
- Add DBus support for Blivet-GUI (vponcova)
- Create the Blivet partitioning module (vponcova)
- Don't override bg color of gtk-themes (mate)
- Fix the import of ZFCP (#1684583) (vponcova)
- Set up the disk initialization module from the partitioned storage (vponcova)
- Move the tests for the disk initialization module (vponcova)
- Set the default filesystem type for /boot in the Storage module (vponcova)
- Replace the default autopart type in the Storage module (vponcova)
- Set the correct attribute of the bootloader kickstart data (vponcova)
- network: Get FCoE nics from the DBus module (vponcova)
- Set up the kickstart partitioning from the storage by default (vponcova)
- Get the required device size for the given space from DBus (vponcova)
- network module: remove DisableIPV6 API (rvykydal)
- network module: fix disabling of ipv6 (rvykydal)
- Fixes for pylint-2.3.0 (vponcova)
- network module: remove API for applying boot options (rvykydal)
- network: use DEVICETYPE for team when updating virtual slaves ifcfgs
  (rvykydal)
- dracut/parse-kickstart: Set DEVICETYPE instead of TYPE in a team master ifcfg
  file (ptalbert)
- network module: take DEVICETYPE for team into account (rvykydal)
- payload: fix pep8 errors in TUI source spoke (jkonecny)
- network: fix network spoke status message (rvykydal)
- payload: switch source spoke from CamelCase (jkonecny)
- payload: solve pep8 errors in GUI source spoke (jkonecny)
- network module: fix missing argument in a log message (rvykydal)
- network module: honor ifname boot option for kickstart %%pre and missing
  ifcfg (rvykydal)

* Mon Feb 25 2019 Martin Kolman <mkolman@redhat.com> - 31.1-1
- Use apply_disk_selection (vponcova)
- Use filter_disks_by_names (vponcova)
- Exclude zFCP and NVDIMM devices in is_local_disk (vponcova)
- Move code from pyanaconda.ui.lib.disks (vponcova)
- Remove the support for fake disks (vponcova)
- Add tests for the Snapshot module (vponcova)
- Remove the extra code for protecting live devices (vponcova)
- payload: switch from CamelCase in utils.py (jkonecny)
- payload: switch from CamelCase in rpmostreepayload.py (jkonecny)
- payload: switch from CamelCase in manager.py (jkonecny)
- payload: switch from CamelCase in livepayload.py (jkonecny)
- payload: switch from CamelCase in dnfpayload.py (jkonecny)
- payload: switch from CamelCase in the __init__.py (jkonecny)
- payload: move versionCmp to a separate file (jkonecny)
- payload: convert manager states to enum (jkonecny)
- payload: use ABCMeta for abstract classes (jkonecny)
- payload: move manager to a separate file (jkonecny)
- payload: remove ImagePayload abstract class (jkonecny)
- payload: move requirements code to a separate file (jkonecny)
- payload: move requirements exception to payload.errors (jkonecny)
- payload: import exceptions directly in dnf payload (jkonecny)
- payload: move exceptions to a separate file (jkonecny)
- payload: remove unused code parts (jkonecny)
- payload: fix pep8 issues (jkonecny)
- Specify the sysroot when you call the DBus method InstallWithTasks (vponcova)
- Remove the obsolete check for unknown sources (vponcova)
- network tui: guard use of NMClient by system configuration (rvykydal)
- network tui: handle device configuration in proper spoke (rvykydal)
- Use unformatted DASDs for the partitioning (vponcova)
- Fix the storage reset in TUI (vponcova)
- Use the Snapshot module in UI (vponcova)
- Use the Snapshot module in the Storage module (vponcova)
- Create a task for creation of snapshots (vponcova)
- Create a task for validation of snapshot requests (vponcova)
- Handle the command snapshot in the Snapshot module (vponcova)
- Create the Snapshot module (vponcova)
- network: rename sanityCheckHostname function (rvykydal)
- network: remove code which is no more needed/used with network module
  (rvykydal)
- network ui: share some code (will be provided by module) (rvykydal)
- network gui: update model instead of recreating it on config changes
  (rvykydal)
- network gui: connect to network module DeviceConfigurations (rvykydal)
- network: use NM Client for networking status message (rvykydal)
- network tui: use NetworkDeviceConfiguration structure (rvykydal)
- network tui: let network module handle updating kickstart data (rvykydal)
- network: remove no more used code (rvykydal)
- network tui: use network module and libnm (rvykydal)
- Add tests for the NVDIMM module (vponcova)
- Use the NVDIMM module in the NVDIMMDialog (vponcova)
- Create a task for the NVDIMM namespace reconfiguration (vponcova)
- Move the support for setting NVDIMM namespaces to use on DBus (vponcova)
- Move the support for updating NVDIMM actions on DBus (vponcova)
- Move the support for ignoring NVDIMM devices on DBus (vponcova)
- Create the NVDIMM module (vponcova)

* Tue Feb 19 2019 Martin Kolman <mkolman@redhat.com> - 30.25-1
- Remove one more obsolete group tag (mkolman)

* Tue Feb 19 2019 Martin Kolman <mkolman@redhat.com> - 30.24-1
- Add tests for the bootloader installation tasks (vponcova)
- Move the bootloader tests to a new file (vponcova)
- Create the DBus installation tasks for the bootloader (vponcova)
- Check for dirinstall target on s390 (bcl)
- Remove the menu_auto_hide attribute from Bootloader (vponcova)
- Remove the efi_dir attribute from EFIBase (vponcova)
- Clean up the Anaconda class (vponcova)
- Move pyanaconda.ihelp (vponcova)
- Update the stylesheet data (vponcova)
- Add tests for new methods of the Storage module (vponcova)
- Apply the partitioning in the Storage module (vponcova)
- Fix missing space in translatable string (mail)

* Wed Feb 13 2019 Martin Kolman <mkolman@redhat.com> - 30.23-1
- Reorganize the code for the boot loader installation (vponcova)
- Remove a useless argument from write_boot_loader (vponcova)
- Remove useless arguments from methods of the kickstart commands (vponcova)
- Create installation tasks for the Storage module (vponcova)
- Add tests for the custom partitioning module (vponcova)
- Create the custom partitioning module (vponcova)
- Process the btrfs command in the Storage module (vponcova)
- Remove the data from the execute method of the partitioning executors
  (vponcova)
- Remove unmaintained signal handler (#1676683) (vponcova)
- Change a confusing message for headless systems (vponcova)
- Mount the file systems in a different installation task (vponcova)
- Write the escrow packets later (vponcova)
- Replace the writeStorageEarly and writeStorageLater methods (vponcova)

* Tue Feb 12 2019 Martin Kolman <mkolman@redhat.com> - 30.22-1
- Don't use the network manager client in a mock environment (vponcova)
- Don't load storage plugins in dir installations (#1674605) (vponcova)
- Test the storage configuration and validation in the Storage module
  (vponcova)
- Implement configuration and validation in the partitioning modules (vponcova)
- Create the storage validation task (vponcova)
- Create the storage configuration task (vponcova)
- Create base classes for the partitioning modules (vponcova)
- Check if we can access a DBus service (vponcova)

* Thu Feb 07 2019 Martin Kolman <mkolman@redhat.com> - 30.21-1
- Drop the temporary anaconda-live dependency (mkolman)
- network module: update tests for generating dracut arguments (rvykydal)
- network_module: return set from function for getting dracut arguments
  (rvykydal)
- network module: pass ifcfg to the function for getting dracut arguments
  (rvykydal)
- network module: split add_connection_from_ksdata function (rvykydal)
- network module: split bind_connection function (rvykydal)
- network module: move looking for first device with link into a function
  (rvykydal)
- network module: split and fix device configuration functions (rvykydal)
- network module: fix device configuration update for GUI (rvykydal)
- network module: add docstring to ifcfg.py (rvykydal)
- network module: use super() (rvykydal)
- network module: update docstrings and style of kickstart.py (rvykydal)
- network module: do not generate kickstart data for onboot value tweaking
  (rvykydal)
- network module: decide better when to apply onboot policy (rvykydal)
- network module: move functions getting network data to better places
  (rvykydal)
- network module: update docstrings of installation task methods (rvykydal)
- network module: remove unused return values from installation task methods
  (rvykydal)
- network module: fix ONBOOT log message for installation task (rvykydal)
- network module: remove devel debugging log messages (rvykydal)
- network module: transform device configurations to structures in interface
  (rvykydal)
- network module: update doc strings for DeviceConfigurations API (rvykydal)
- network module: connect DisableIPv6 to implementation signal (rvykydal)
- network module: fix generating of kickstart --activate option (rvykydal)
- network module: clean up typos and style (rvykydal)
- network module: use already existing function (rvykydal)
- Reset the storage object in the Storage module (vponcova)
- Protect devices in the Storage module (vponcova)
- Create the storage object in the Storage module (vponcova)
- Initialize Blivet in the Storage module (vponcova)
- Create a task with a result in the Baz module (vponcova)
- Allow to publish a task with a different interface (vponcova)
- Add the GetResult method (vponcova)
- Add the Succeeded signal (vponcova)
- network module: update unit tests (rvykydal)
- newtork module: put use of NM client under control of network module
  (rvykydal)
- network module: use constant for nm connection uuid length (rvykydal)
- network module: use network module to get dracut arguments (rvykydal)
- network module: add support for getting dracut arguments (rvykydal)
- network module: support renaming of devices with ifname= boot option
  (rvykydal)
- network module: generate kickstart from network module (rvykydal)
- network module: set current hostname using network module directly (rvykydal)
- network module: remove dependency of configuration task on nm_client
  (rvykydal)
- network module: use module task for network configuration writing (rvykydal)
- network module: ifcfg.py cleanup (rvykydal)
- network module: dump missing ifcfg files via network module (rvykydal)
- network module: add support for dumping missing ifcfg files (rvykydal)
- network module: set real ONBOOT values via network module (rvykydal)
- network module: add support for updating ONBOOT ifcfg value (rvykydal)
- network module: apply kickstart via network module (rvykydal)
- network module: fix list of devices for which kickstart was applied
  (rvykydal)
- network module: work with ifcfg file objects, not paths (rvykydal)
- network module: set bootif kickstart value from boot options (rvykydal)
- network module: provide apply_kickstart (rvykydal)
- network module: consolidate initramfs connections via Network module
  (rvykydal)
- network module: provide initramfs connections consolidation (rvykydal)
- network module: set default value for missing network --device from ksdevice.
  (rvykydal)
- network module: handle default network --device value (rvykydal)
- network module: handle hostname only network commands correctly (rvykydal)
- network module: use DBus Structure for DeviceConfiguration (rvykydal)
- network module: provide dbus API for DeviceConfigurations (rvykydal)
- network module: fix looking up vlan parent if specified by UUID (rvykydal)
- network module: fix kickstart generating for vlan interface name (rvykydal)
- network module: generate kickstart data from DeviceConfigurations (rvykydal)
- network module: add a module providing NM.Client (rvykydal)
- network module: connect DeviceConfigurations to signals from NM (rvykydal)
- network module: add DeviceConfigurations for persistent config state
  (rvykydal)

* Wed Feb 06 2019 Martin Kolman <mkolman@redhat.com> - 30.20-1
- Remove obsolete Group tag & obsolete scriptlets (mkolman)
- Move the write method of the InstallerStorage class (vponcova)
- Clean up the reset method of the InstallerStorage class (vponcova)
- Allow non-ASCII characters in passphrases again (#1619813) (vponcova)
- Remove the argument protected from initialize_storage (vponcova)
- Remove multiboot support for tboot (javierm)
- Move the code for ignoring disks labeled OEMDRV (vponcova)
- Set default entry to the BLS id instead of the entry index (javierm)
- Remove the ksdata argument from the initialize_storage function (vponcova)
- Remove the ksdata attribute from the InstallerStorage class (vponcova)
- Move the code for ignoring nvdimm devices to pyanaconda.storage.utils
  (vponcova)
- Use new ssl certificate kickstart options (lars)
- Remove the data argument from the do_autopart function (vponcova)
- Call refreshAutoSwapSize from the do_autopart function (vponcova)
- Move getAvailableDiskSpace to pyanaconda.storage.utils (vponcova)
- Move lookupAlias to pyanaconda.storage.utils (vponcova)
- Move getEscrowCertificate to pyanaconda.storage.utils (vponcova)
- Move get_ignored_nvdimm_blockdevs to pyanaconda.storage.utils (vponcova)
- Remove update_ksdata from the InstallerStorage class (vponcova)
- Remove obsolete ldconfig scriptlets (mkolman)
- Do not try to use disks without partition slots for autopart (vtrefny)
- dracut: Add deps for fetch-kickstart-disk (walters)

* Mon Jan 28 2019 Martin Kolman <mkolman@redhat.com> - 30.19-1
- Move code for the storage creation (vponcova)
- Move code for the storage initialization (vponcova)
- Remove the GRUB class (javierm)
- Remove support for deprecated bootloaders (javierm)
- Spelling fix in Boot Options documentation (josephvoss14)
- Put 'lock' checkbox under 'Confirmation field' (frederic.pierret)
- Don't create an extra instance of the bootloader (vponcova)
- Remove the preStorage method in payload (vponcova)
- Use LUKS2 by default (vponcova)
- Clean up the space checkers (#1520749) (vponcova)
- Don't show time and date controls in live installations (#1510425) (vponcova)
- anaconda: add option to lock root account (frederic.epitre)

* Mon Jan 21 2019 Martin Kolman <mkolman@redhat.com> - 30.18-1
- Relabel X11/xorg.conf.d directory (#1666892) (jkonecny)
- Reorder items in selinux relabeling post script (#1666892) (jkonecny)
- Fix jumping boxes in root password spoke (jkonecny)
- Move the execute method of the bootloader command (vponcova)
- Remove ksdata from the execute method of the bootloader command (vponcova)
- Move writeBootLoader to pyanaconda.bootloader.installation (vponcova)
- Move EXTLINUX to pyanaconda.bootloader.extlinux (vponcova)
- Move ZIPL to pyanaconda.bootloader.zipl (vponcova)
- Move Yaboot to pyanaconda.bootloader.yaboot (vponcova)
- Move EFIBase to pyanaconda.bootloader.efi (vponcova)
- Move GRUB2 to pyanaconda.bootloader.grub2 (vponcova)
- Move GRUB to pyanaconda.bootloader.grub (vponcova)
- Move Bootloader to pyanaconda.bootloader.base (vponcova)
- Move BootLoaderImage to pyanaconda.bootloader.image (vponcova)
- Create the pyanaconda.bootloader module (vponcova)
- Tweak tests documentation (jkonecny)
- Fix requires in dependency solver (jkonecny)
- Remove the unused method add_re_check (vponcova)
- Remove the unused attribute _lHome (vponcova)
- Remove the unused attribute _actionStore (vponcova)
- Remove unused constants ERROR_WEAK and ERROR_NOT_MATCHING (vponcova)
- Remove the unused attributes _repoNameWarningBox and _repoNameWarningLabel
  (vponcova)
- Remove the unused attribute _configureBox (vponcova)
- Remove the unused attribute _addDisksButton (vponcova)
- Remove the unused attribute orig_fstab (vponcova)
- Remove the unused attribute ignore_disk_interactive (vponcova)
- Remove the unused class TarPayload (vponcova)
- Remove the unused method environmentGroups (vponcova)
- Remove the unused exception NoSuchPackage (vponcova)
- Remove the unused function get_locale_territory (vponcova)
- Remove the unused variable upgrade_log (vponcova)
- Remove unused classes RegexpCheck and FunctionCheck (vponcova)
- Remove the unused property check_request (vponcova)
- Remove the unused constant PASSWORD_DONE_TO_CONTINUE (vponcova)
- Remove the unused constant SECRET_MIN_LEN (vponcova)
- Remove the unused variable bugzillaUrl (vponcova)
- Remove the unused attribute stage1_device_types (vponcova)
- Move attributes from the Blivet class to Anaconda (vponcova)
- Remove the Blivet's gpt flag (vponcova)
- Set Automatic Installation Media for HDD not ISO (jkonecny)
- Adapt old code to new partition name translation (jkonecny)
- Fix source spoke status for expanded tree on HDD (jkonecny)
- Enable installation from install tree on HDD (jkonecny)
- Remove the unused class IPSeriesYaboot (vponcova)
- Fix the name of the attribute stage2_device_raid_levels (vponcova)
- Remove the useless attribute stage2_max_end_mb (vponcova)
- Remove the unused attribute problems (vponcova)
- Remove the unused logger to stderr (vponcova)
- Move the code from format_by_default to the storage checker (vponcova)
- Move the code from must_format to the storage checker (vponcova)

* Wed Jan 09 2019 Martin Kolman <mkolman@redhat.com> - 30.17-1
- Fix anaconda-live package temporary Requires: (mkolman)
- Add a new configuration option allow_imperfect_devices (vponcova)
- Remove the selinux flag (vponcova)
- Rename the Services section (vponcova)
- Fix Arm EFI package selection and 32 bit status (pbrobinson)
- Remove support for the undocumented option force_efi_dir (vponcova)
- Remove the flag extlinux (vponcova)
- Remove the flag nombr (vponcova)
- Remove the flag leavebootorder (vponcova)
- Remove the flag nonibftiscsiboot (vponcova)

* Tue Jan 08 2019 Martin Kolman <mkolman@redhat.com> - 30.16-1
- Use the file system type provided by Blivet by default (#1663585) (vponcova)
- Move remaining GUI related files to anaconda-gui (mkolman)
- Create anaconda-live sub-package (mkolman)
- Don't acquire the imp's lock (#1644936) (vponcova)

* Thu Jan 03 2019 Martin Kolman <mkolman@redhat.com> - 30.15-1
- Remove install classes from the code (vponcova)
- Remove files with install classes (vponcova)
- Use the Anaconda configuration to configure the storage (vponcova)
- Use the Anaconda configuration to configure the bootloader (vponcova)
- Use the correct name of the variant AtomicHost (vponcova)
- Use the Anaconda configuration to configure payload (vponcova)
- Use the Anaconda configuration to configure network devices (vponcova)
- Use the Anaconda configuration to customize the user interface (vponcova)
- Use the Anaconda configuration to show EULA (vponcova)
- Use the Anaconda configuration to detect unsupported hardware (vponcova)
- Remove the kickstart command installclass (vponcova)
- Fix the anaconda documentation (vponcova)
- Add support for inst.product and inst.variant (vponcova)
- Use the product configuration files in Anaconda (vponcova)

* Wed Jan 02 2019 Martin Kolman <mkolman@redhat.com> - 30.14-1
- Require password confirmation in GUI (#1584064) (mkolman)
- Run zipl again after generating initramfs (#1652727) (vponcova)
- Preserve the boot option zfcp.allow_lun_scan (#1561662) (vponcova)
- Don't allow /boot on LVM (#1641986) (vponcova)
- The encoding should be always set to UTF-8 (#1642857) (vponcova)
- Make sure fips is correctly enabled on target system (#1619568) (mkolman)
- Remove workaround for bd_s390_dasd_online (vponcova)
- Clean up /run/install (#1562239) (vponcova)
- Make it possible to exit empty user spoke (#1620135) (mkolman)
- Don't allow to use LDL DASD disks (#1635825) (vponcova)
- Remove initThreading method from pyanaconda.threading (vponcova)
- Drop the inst.noblscfg option (javierm)

* Tue Dec 04 2018 Martin Kolman <mkolman@redhat.com> - 30.13-1
- Extend tests for the configuration support (vponcova)
- Split the Anaconda configuration handler to more files (vponcova)
- Add tests for the product configurations (vponcova)
- Read only *.conf files from /etc/anaconda/conf.d (vponcova)
- Create the product configuration loader (vponcova)
- Disable BLS config if new-kernel-pkg script is installed (javierm)
- Drop xorg-x11-server-Xorg check from graphical target detection (#1583958)
  (mkolman)
- Create a basic structure of the product configuration files (vponcova)
- Fix pylint errors (vponcova)
- dracut/parse-kickstart: don't abort on --device=link (lkundrak)
- Add provides_network_config system property (rvykydal)
- Get rid of network system capability which does not make sense. (rvykydal)
- Prohibit network configuration on Live OS. (rvykydal)
- Use check_supported_locales to filter unsupported locales (vponcova)
- Replace filterSupportedLangs and filterSupportedLocales (vponcova)
- Remove help-related constants from install classes (vponcova)
- Remove setup_on_boot from the install classes (vponcova)
- Convert a keymap into a list of layouts (vponcova)
- RPM: anaconda-core requires dbus-daemon (awilliam)
- Remove use_geolocation_with_kickstart from install classes (vponcova)

* Thu Nov 22 2018 Martin Kolman <mkolman@redhat.com> - 30.12-1
- Simplify the task Activate filesystems (vponcova)
- Remove the flag livecdInstall (vponcova)
- Overwrite network configuration for the live image payload (vponcova)
- Write tests for the installation system configuration (vponcova)
- Resolve the name conflicts in exception.py (vponcova)
- Use the Anaconda configuration in the network module (vponcova)
- Revert "Don't try to get hostnamed proxy in non-installer-image environments
  (#1616214)" (vponcova)
- Remove the function can_touch_runtime_system (vponcova)
- Add rules for the installation system (vponcova)
- Configure the installation system (vponcova)
- Replace setNetworkOnbootDefault (vponcova)
- Add tests for the FCoE module (vponcova)
- Discover an FCoE device with a DBus task (vponcova)
- Reload the FCoE module on the storage reset (vponcova)
- Let the FCoE module to provide the dracut arguments (vponcova)
- Let the FCoE module to write the configuration (vponcova)
- Move kickstart support to the FCoE module (vponcova)
- Create the basic structure for the FCoE module (vponcova)

* Mon Nov 19 2018 Martin Kolman <mkolman@redhat.com> - 30.11-1
- Install grubby-deprecated when using the extlinux bootloader (javierm)
- Remove configurePayload (vponcova)
- Resolve the name conflicts with conf (vponcova)
- Write tests for the target support (vponcova)
- Simplify the code (vponcova)
- Replace the dirInstall flag (vponcova)
- Replace the imageInstall flag (vponcova)
- Configure the installation target (vponcova)
- Write tests for the default partitioning (vponcova)
- Define the default partitioning statically (vponcova)
- Remove l10n_domain from the install classes (vponcova)
- Re-generate BLS loader file snippets on live installs (#1648472) (awilliam)
- Remove the attribute bootloaderTimeoutDefault (vponcova)
- Remove the attribute bootloaderExtraArgs (vponcova)
- Remove the method setPackageSelection (vponcova)
- Remove the setStorageChecker method (vponcova)
- Remove the getBackend method (vponcova)
- Add doc to make a release in a mock environment (jkonecny)
- Support in our scripts creating release in a mock (jkonecny)
- Add dependencies to make a new release to dependency_solver (jkonecny)

* Tue Nov 06 2018 Martin Kolman <mkolman@redhat.com> - 30.10-1
- Make the pyanaconda/image.py more pep8 (jkonecny)
- Test image repodata folder based on treeinfo file (jkonecny)
- Use var instead of strings in findFirstIsoImage (jkonecny)
- Use new InstallTreeMetadata instead of TreeInfo (jkonecny)
- Add InstallTreeMetadata class (jkonecny)
- Move DEFAULT_REPOS to the constants (jkonecny)
- Don't check for firmware compatibility to enable BootLoaderSpec support
  (javierm)
- Update kernel command line parameters in BLS files (javierm)
- Add support for GRUB_ENABLE_BLSCFG and inst.noblscfg (pjones)
- Get rid of new-kernel-pkg invocations (pjones)
- Minor pylint cleanups (pjones)

* Mon Nov 05 2018 Martin Kolman <mkolman@redhat.com> - 30.9-1
- Load configuration files from /etc/anaconda/conf.d (vponcova)
- Let the DBus launcher to set up the modules (vponcova)
- Start modules that are enabled in the configuration file (vponcova)
- Enable the DBus modules and addons via the configuration file (vponcova)

* Thu Nov 01 2018 Jiri Konecny <jkonecny@redhat.com> - 30.8-1
- Remove flags from anaconda_logging (vponcova)
- Remove blivet-specific flags from pyanaconda.flags (vponcova)
- The armplatform option is deprecated (vponcova)
- Create a class for the Anaconda bus connection (vponcova)
- Fix local repo files aren't enabled (#1636739) (jkonecny)
- Write RPM tests for the Anaconda configuration file (vponcova)
- Write tests for the configuration support (vponcova)
- Create a class for handling the Anaconda configuration (vponcova)
- Provide a better support for handling the configuration files (vponcova)
- Create the Anaconda configuration file (vponcova)

* Thu Oct 18 2018 Martin Kolman <mkolman@redhat.com> - 30.7-1
- installclass: fix variant string for Atomic Host (#1640409) (dusty)
- Remove EXPERIMENTAL label for mountpoint assignment in TUI (#1636940)
  (mkolman)

* Mon Oct 15 2018 Martin Kolman <mkolman@redhat.com> - 30.6-1
- nvdimm: update ks data for actions in UI (rvykydal)
- nvdimm: use pykickstart constant for setting reconfigure mode (rvykydal)
- Revert "Don't allow booting from nvdimm devices" (rvykydal)
- Add --no-pip to setup-mock-test-env script (jkonecny)
- Fix error message in setup-mock-test-env script (jkonecny)
- Add shortcut function to get dependency script (jkonecny)
- Add install-pip parameter to setup-mock-test-env (jkonecny)
- Small optimalization in setup-mock-test-env (jkonecny)
- Add package installation from pip for test script (jkonecny)
- Fix wrong pylint false positive regex (jkonecny)

* Mon Oct 08 2018 Martin Kolman <mkolman@redhat.com> - 30.5-1
- Adjust to some DNF 3.6 changes (#1637021) (mkolman)
- Ignore errors when trying to activate unsupported swaps (#1635252) (vtrefny)
- Add option to set kernel.hung_task_timeout_secs option (rvykydal)
- Move the glade adaptor to a separate plugin (dshea)

* Wed Oct 03 2018 Martin Kolman <mkolman@redhat.com> - 30.4-1
- Fix strings not marked for translation (jkonecny)
- Drop attempt to add 'nocrypto' to tsflags (awilliam)
- Fix librepo logging with new DNF (jkonecny)
- Revert "Remove librepo imports from Anaconda (#1626609)" (jkonecny)
- Set the VNC password directly (#1592686) (vponcova)
- Update the spoke for unsupported hardware in TUI (#1601545) (vponcova)
- Update the dialog for unsupported hardware in GUI (#1601545) (vponcova)
- Support detection of kernel taints (vponcova)
- Fix the rescue mode (#1631749) (vponcova)
- Fix the sanity check verify_gpt_biosboot (#1593446) (vponcova)
- Flags shouldn't process the kernel options (vponcova)
- Fully support the inst.gpt option (vponcova)
- Don't set Anaconda-specific flags in Blivet (vponcova)
- Remove the class for kernel arguments from pyanaconda.flags (vponcova)
- Remove unused false positives (vponcova)
- Don't connect to signals of the Network Manager DBus objects (#1582233)
  (vponcova)
- Fix documentation for setting Pykickstart command version (mkolman)
- Don't try to get hostnamed proxy in non-installer-image environments
  (#1616214) (rvykydal)
- Use realm data in UI (vponcova)
- Use realm data in the DBus module (vponcova)
- Create a DBus structure for realm data (vponcova)
- Add support for DBus structures (vponcova)
- docs/commit-log.rst: Don't wrap example firstlines (ferdnyc)
- Detect that there is not enough space on a device (#1613232) (vponcova)
- Add Silverblue InstallClass (jkonecny)

* Tue Sep 11 2018 Martin Kolman <mkolman@redhat.com> - 30.3-1
- Save lsblk output to the Anaconda traceback file (vtrefny)
- Remove librepo imports from Anaconda (#1626609) (jkonecny)
- DNF 3.5 compatibility (mkolman)
- Use the default LUKS version for auto partitioning (#1624680) (vponcova)
- Remove the testing flag (vponcova)

* Thu Aug 30 2018 Martin Kolman <mkolman@redhat.com> - 30.2-1
- Add initial 32-bit ARMv7 EFI support (pbrobinson)
- Drop legacy get_arm_machine pieces (pbrobinson)
- arch: arm: drop omap checks and specifics (pbrobinson)

* Mon Aug 27 2018 Martin Kolman <mkolman@redhat.com> - 30.1-1
- Fix the processing of the live CD source (#1622248) (vponcova)

* Wed Aug 22 2018 Martin Kolman <mkolman@redhat.com> - 29.24-1
- Fix crash in tui when default partitioning scheme is not supported.
  (rvykydal)
- Fix pylint errors (vponcova)
- Add libtool build dependency (jkonecny)
- Remove shebang from DUD test (jkonecny)
- Add inst.addrepo documentation for HD variant (jkonecny)
- Warn when repo names are not unique (jkonecny)
- HD addon repos have mount directories permanent (jkonecny)
- Unmount hard drive additional repositories (jkonecny)
- Move RepoData copy creation to the RepoData class (jkonecny)
- Show empty file protocol on HD addon repo fail (jkonecny)
- Mount and use HDD additional repositories (jkonecny)
- Separate _find_and_mount_iso from _setup_media (jkonecny)
- Load hard drive repo type from inst.addrepo (jkonecny)
- Do not fail if .discinfo file can't be read (jkonecny)
- Use productmd to parse .discinfo file (jkonecny)
- Add payload sources tests (jkonecny)
- Cleanup payload tests source file (jkonecny)
- Add documentation for inst.addrepo boot option (jkonecny)
- Add additional repositories to KS data (jkonecny)
- Use new source solution (jkonecny)
- Add payload sources implementation (jkonecny)
- Don't resize a device if the size is same as the old size (#1572828)
  (vponcova)
- Mark disks with additional repos as protected (jkonecny)
- Support boot args parsing to list (jkonecny)
- Add inst.addrepo new options (jkonecny)
- Make parenthesis consistent (jkonecny)
- Remove unused parameter from live_startup method (jkonecny)
- Disable treeinfo based repos only once (jkonecny)
- Disable treeinfo repos when base repo change (jkonecny)
- Treeinfo repos can't be changed nor removed (jkonecny)
- Add all repositories from the treeinfo file (jkonecny)
- Load base repository location from treeinfo (jkonecny)
- Add limited file:// protocol to GUI Source spoke (jkonecny)
- Add BaseOS between default base repositories (jkonecny)
- Split _setupInstallDevice method in payload (jkonecny)
- Check the LUKS2 memory requirements (vponcova)
- Add an option for choosing version of LUKS in GUI (vponcova)
- Add tests for LUKS2 in the auto partitioning module (vponcova)
- Apply the LUKS2 options from the auto partitioning module (vponcova)
- Support LUKS2 options in the auto partitioning module (vponcova)
- Support LUKS2 options in logvol, part and raid commands (vponcova)
- Enable to set a default version of LUKS (vponcova)
- Update dependencies and kickstart commands to support LUKS2 (#1547908)
  (vponcova)
- Revert back to running DNF in a subprocess (mkolman)
- Use SimpleConfigFile to get PLATFORM_ID from /etc/os-release (mkolman)
- Fix a 5 year old typo in the spec file (mkolman)
- Use wwn attr instead of removed wwid. (#1565693) (dlehman)

* Tue Aug 07 2018 Martin Kolman <mkolman@redhat.com> - 29.23-1
- Bump required DNF version (mkolman)
- Fix some small issues with the platform id patch (mkolman)
- Set platform id for DNF (mkolman)
- Fix crash when software environment is False (jkonecny)
- Allow to delete all file systems used by Unknown (#1597199) (vponcova)
- DD: Use text mode when calling tools with subprocess (rvykydal)
- Update RHEL placeholder names (mkolman)
- Typo fixup (rvykydal)
- Define if blivet-gui is supported via installclasses (rvykydal)
- Offer Blivet-GUI partitioning only if supported (rvykydal)
- Only show the "closest mirror" source option where appropriate (mkolman)
- Starting from 3.0 DNF expects strings in comps queries (mkolman)
- Use the manual partitioning module in TUI (vponcova)
- Use the manual partitioning module in UI (vponcova)
- Add tests for the manual partitioning module (vponcova)
- Create the manual partitioning module (vponcova)
- Reserve enough static space for 2 lines in spoke status on hub (#1584160)
  (rvykydal)
- Fix disable additional repositories (jkonecny)
- Show better messages for NoSuchPackage and NoSuchGroup (#1599190) (vponcova)
- Bootloader stage2 can't be on btrfs on rhel (#1533904) (rvykydal)

* Fri Jul 27 2018 Martin Kolman <mkolman@redhat.com> - 29.22-1
- Handle new module specific error states (mkolman)
- Handle missing package errors reported by the install_specs() function
  (mkolman)
- Initial module enablement and installation support (mkolman)
- Use productmd library to parse .treeinfo (#1411673) (jkonecny)
- Import kickstart classes as version-less in the dracut script (vponcova)
- Use only version-less kickstart classes (vponcova)
- Define version-less variants of kickstart classes (vponcova)

* Wed Jul 25 2018 Martin Kolman <mkolman@redhat.com> - 29.21-1
- Pylint should skip the file livepayload.py (vponcova)
- Fix pylint errors (vponcova)
- Change the pop-up text with the pre-release warning (#1542998) (vpodzime)
- Sort categories on the hub by defined order (#1584160) (rvykydal)
- Show a note about EULA where relevant (mkolman)
- Change message log level to INFO when adding repo (jkonecny)
- Set packaging log level to DEBUG by default (jkonecny)
- Remove the python-wrapt dependency (vponcova)
- Do not use capitals for spoke names (#1584160) (rvykydal)
- Wrap category label and add space between columns (#1584160) (rvykydal)
- Use 32 px icons (instead of 16 px) on hubs (#1584160) (rvykydal)
- Replace deprecated dracut options for booting with ibft. (rvykydal)
- Improve handling of unsupported filesystems in UI. (rvykydal)
- Reserve two lines for status message (#1584160) (rvykydal)
- Use three spoke columns on hub for better scaling (#1584160) (rvykydal)

* Wed Jul 18 2018 Martin Kolman <mkolman@redhat.com> - 29.20-1
- Make pyanaconda.dbus.typing work with Python 3.7 (#1598574) (awilliam)
- Protected devices might be hidden (#1561766) (vponcova)
- fstab: include a note about systemctl daemon-reload (zbyszek)
- Access the ZFCP module only on s390x (vponcova)
- Tell libreport if it is a final release or not (#1596392) (vpodzime)
- bootloader: GRUB2: Set menu_auto_hide when enabled by the instClass
  (hdegoede)
- installclass: Add bootloader_menu_autohide property (hdegoede)
- Add tests for the zFCP module (vponcova)
- Handle the zfcp command in the zFCP module (vponcova)
- Use the zFCP discovery task in UI (vponcova)
- Create the zFCP discovery task (vponcova)
- Create the zFCP module (vponcova)

* Wed Jun 27 2018 Martin Kolman <mkolman@redhat.com> - 29.19-1
- DNF 3: progress callback constants moved to dnf.transaction (awilliam)
- DNF 3: Update size calculations for transaction item changes (awilliam)
- DNF 3: config substitutions moved from dnf to libdnf (awilliam)

* Mon Jun 25 2018 Martin Kolman <mkolman@redhat.com> - 29.18-1
- Add tests for the DASD module (vponcova)
- Run the DASD formatting task in UI (vponcova)
- Extend the sync_run_task method with a callback (vponcova)
- Create a task for formatting DASDs (vponcova)
- Run the DASD discovery task from UI (vponcova)
- Create a task for discovering DASDs (vponcova)
- Create the DASD module (vponcova)
- Add tests for the language installation task (vponcova)
- Run an installation task to install a language (vponcova)
- nvdimm: fix crash on non-block devices (rvykydal)

* Tue Jun 12 2018 Martin Kolman <mkolman@redhat.com> - 29.17-1
- Wait for kickstart modules to quit (vponcova)
- Ask for a default passphrase if required (vponcova)
- Add support for setting different types of passwords in TUI (vponcova)

* Thu Jun 07 2018 Martin Kolman <mkolman@redhat.com> - 29.16-1
- Add tests for changes in tasks and the install manager (vponcova)
- Add a simple installation task in the Baz module (vponcova)
- Update the boss classes (vponcova)
- Update the base clases for modules (vponcova)
- Use the system installation task in the install manager (vponcova)
- Add the system installation task (vponcova)
- Add methods for running remote DBus tasks (vponcova)
- Improved base clases for DBus tasks (vponcova)
- Do not manually create LUKSDevice when unlocking a LUKS format (vtrefny)
- Fix pylint errors (vponcova)
- Skip the pylint check for the bootloader.py (vponcova)
- Enable DNF depsolver debugging in debug mode (mkolman)
- Don't reset locale of our DBus daemon (vponcova)
- Close the DNF base later (#1571299) (vponcova)
- Add 10%% for storage metadata to the total required space (#1578395)
  (vponcova)
- Add hook to prevent mistake upstream pushes (jkonecny)
- Revert "WIP" (vponcova)
- WIP (vponcova)
- Set locale to en_US.UTF-8 in every module (#1575415) (vponcova)
- Move initial module configuration to the init function (vponcova)
- Fix the mount command (vponcova)
- Use the auto partitioning module in UI (vponcova)
- Only check space during a tui kickstart if ksprompt is enabled (bcl)
- Fix can't exit TUI storage spoke (jkonecny)
- Use PROCESSED_AND_CLOSE and PROCESSED_AND_REDRAW (jkonecny)
- Remove not required PROCESSED return (jkonecny)
- Remove PROCESSED from refresh method (jkonecny)

* Wed May 16 2018 Martin Kolman <mkolman@redhat.com> - 29.15-1
- nvdimm: make debug messages more clear (rvykydal)
- nvdimm: use libblockdev enum to check namespace mode (rvykydal)
- Add data loss warning to nvdimm reconfigure dialog. (rvykydal)
- Add UI feedback for disk repopulating after nvdimm reconfiguration.
  (rvykydal)
- Fix ignoring of nvdimm devices (rvykydal)
- Don't allow booting from nvdimm devices (rvykydal)
- Improve UI feedback for invalid boot on non-iBFT iSCSI devices. (rvykydal)
- Add inst.nonibftiscsiboot boot option. (rvykydal)
- Use only devices specified by nvdimm command for installation. (rvykydal)
- Add option to reconfigure nvdimm devices into sector mode. (rvykydal)
- Allow only devices in sector mode to be selected. (rvykydal)
- Add nvdimm devices to Advanced Storage spoke. (rvykydal)
- Add kickstart support for nvdimm reconfiguration to sector mode. (rvykydal)
- Ignore nvdimm disks which are not in sector mode. (rvykydal)
- Do not ignore nvdimm (pmemX) devices (rvykydal)
- Update the pykickstart commands (vponcova)
- Fix firewall DBUS module API usage (#1577405) (mkolman)
- Fix formatting in the TUI storage spoke (jkonecny)
- Fix TUI crash in mountpoint assignment (#1564067) (jkonecny)
- Fix KS logvol metadata and chunksize parameters (#1572511) (jkonecny)
- Show correct bootloader error on the MacEFI platform (vponcova)
- Revert "Fix broken kickstart command test" (rvykydal)
- Support fcoe --autovlan option (#1564096) (rvykydal)

* Fri May 04 2018 Martin Kolman <mkolman@redhat.com> - 29.14-1
- Increase module startup timeout to 600 seconds (mkolman)
- Fix name of the Zanata Python client package (mkolman)
- Add tests for the auto partitioning module (vponcova)
- Create the auto partitioning module (vponcova)
- Add the firewall submodule (mkolman)
- Once again fix cmdline error handling. (#1360223) (sbueno+anaconda)
- Extend the timeout period to 180s in the case of cmdline error. (#1360223)
  (sbueno+anaconda)
- Fix the clearpart test with disklabel option (vponcova)
- The specified nosetests failed to run (vponcova)

* Tue Apr 24 2018 Martin Kolman <mkolman@redhat.com> - 29.13-1
- Show correct root account locked status in reconfig mode (#1507940) (mkolman)
- Add missing lines and modularization only log to test coverage (jkonecny)
- Remove makebumpver dependency from spec file (jkonecny)
- network module: use connectivity checking in anaconda (rvykydal)
- network module: add connectivity checking (rvykydal)
- Permit adding disabled external repos to installation. (riehecky)
- Handle empty active attribute for consoles (#1569045) (mkolman)
- Support temporary kickstart generating (vponcova)
- Create the dynamic module User (vponcova)
- Select Workstation install class for Workstation live (#1569083) (awilliam)
- Rename the main module User to Users (vponcova)

* Thu Apr 19 2018 Martin Kolman <mkolman@redhat.com> - 29.12-1
- Save logs to result folder after rpm-tests (jkonecny)
- Add Installed pyanaconda tests (jkonecny)
- Fix name of the RPM test (jkonecny)
- Support running just chosen rpm test (jkonecny)
- Add test cache files to gitignore (jkonecny)
- Move test install test from Makefile to rpm tests (jkonecny)
- Create structure to run rpm tests (jkonecny)
- Move all nosetests to separate directory (jkonecny)
- Fix broken kickstart command test (jkonecny)
- Fix broken kickstart command test (jkonecny)
- localization: use LanguageKickstarted module property (#1568119) (rvykydal)
- Start only the specified kickstart modules (#1566621) (vponcova)
- Use the Bootloader module in UI (vponcova)
- Add tests for the bootloader module (vponcova)
- Create the bootloader module (vponcova)
- rpmostreepayload: do not require network for dvd installation (#1565369)
  (rvykydal)
- Fix double logging to stdout (vponcova)
- Don't try to create required partitions if there are none (vponcova)

* Thu Apr 12 2018 Martin Kolman <mkolman@redhat.com> - 29.11-1
- Add anaconda-install-env-deps as dependency of the anaconda package (mkolman)
- Add %%files for install-env-deps so it actually exists (awilliam)

* Tue Apr 10 2018 Martin Kolman <mkolman@redhat.com> - 29.10-1
- Bump simpleline version (mkolman)
- Do not redraw screen after text YesNo dialog (#1557951)(jkonecny)
- Revert "Adapt to a new simpleline changes (#1557472)(jkonecny)
- authselect: enable silent last log (pbrezina)
- authselect: fix typo to enable fingerprint authentication (pbrezina)

* Mon Apr 09 2018 Martin Kolman <mkolman@redhat.com> - 29.9-1
- Move install time dependencies to a metapackage (mkolman)

* Thu Apr 05 2018 Martin Kolman <mkolman@redhat.com> - 29.8-1
- Fix forgotten usage of the selinux kickstart command (vponcova)
- Fix tests for the storage module (vponcova)
- Use the disk selection and initialization modules in UI (vponcova)
- Enable to use object identifiers instead of object paths (vponcova)

* Thu Mar 29 2018 Martin Kolman <mkolman@redhat.com> - 29.7-1
- Add Makefiles for disk initialization and selection modules (vponcova)
- Remove the invalid self argument (vponcova)
- Run all unit tests (vponcova)

* Tue Mar 27 2018 Martin Kolman <mkolman@redhat.com> - 29.6-1
- Create the disk initialization and disk selection modules (vponcova)
- Use watch_property to watch changes of DBus properties (vponcova)
- Better organize the base classes for modules (vponcova)
- Fixed KS forcing zerombr onto RO disk (japokorn)
- Add tests for the kickstart specifications (vponcova)
- Standardize calls to parent via super() (riehecky)
- Fix 'isDisk' property name (#1558906) (vtrefny)
- Make the class for removed kickstart commands more strict (vponcova)
- Fix the progress bar steps (vponcova)
- Use enum for the first boot action (vponcova)
- Use enum for the SELinux modes (vponcova)
- datetime spoke: still pass ksdata to NTPconfigDialog (UIObject) (rvykydal)

* Mon Mar 19 2018 Martin Kolman <mkolman@redhat.com> - 29.5-1
- Write rootpw command to kickstart (#1557529) (mkolman)
- Don't make safe to observe services on buses that don't run (vponcova)
- Add the LanguageKickstarted property (vponcova)
- Don't autoquit by default if the last hub is empty (#1553935) (mkolman)
- Use the Services module in UI (vponcova)
- Create the Services module (vponcova)
- Enable hibernation only on x86 (#1554345) (vponcova)
- Add the Storage module with no API (vponcova)
- Add the Payload module with no API (vponcova)
- Remove DBus modules Foo and Bar (vponcova)
- network module: fix accessing org.freedesktop.hostname1 for current hostname
  (rvykydal)

* Mon Mar 12 2018 Martin Kolman <mkolman@redhat.com> - 29.4-1
- network module: add basic test (rvykydal)
- Add prepare command to setup-mock-test-env script (jkonecny)
- Mark partition live device's disk protected. (#1524700) (dlehman)

* Fri Mar 09 2018 Martin Kolman <mkolman@redhat.com> - 29.3-1
- Remove useless constants from pyanaconda.dbus.constants (vponcova)
- Use identifiers to get observers and proxies (vponcova)
- Remove the publish method from DBus interfaces (vponcova)
- Replace constants in publish and register methods (vponcova)
- Replace constants in DBus interface names (vponcova)
- Define DBus errors with the dbus_error decorator (vponcova)
- Use namespaces and identifiers to describe Anaconda DBus objects (vponcova)
- Add support for identification of DBus objects and services (vponcova)
- User module should parse only rootpw for now (#1553488) (vponcova)
- localization module: plug localization module into keyboard GUI spoke
  (rvykydal)
- localization module: add KeyboardKickstarted property (rvykydal)
- localization module: add KS support for keyboard command (rvykydal)
- localization module: don't use Kickstarted so another command can be added
  (rvykydal)
- Fix release docs (mkolman)
- network: set TYPE value in ifcfg from kickstart in initrmfs (rvykydal)
- Make formatting consistent in AnacondaWidgets.xml (riehecky)

* Mon Mar 05 2018 Martin Kolman <mkolman@redhat.com> - 29.2-1
- Use the user DBUS module in the UI (mkolman)
- Use the user DBUS module for the rootpw command in kickstart.py (mkolman)
- Add initial user DBUS module (mkolman)
- Add tests for the Security module (vponcova)
- Use the Security module in UI (vponcova)
- Don't send empty kickstart to DBus modules (vponcova)
- Add the Security module (vponcova)
- Fix makeupdates script to work with new DBus structure (jkonecny)
- Fix Makefile of the kickstart manager (vponcova)
- Fix check if dbus daemon quit properly (jkonecny)
- Remove check if dbus is running (#1551096) (jkonecny)
- Use Anaconda's special env variable for dbus address (#1551096) (jkonecny)
- Migrate Anaconda to our private dbus session (#1551096) (jkonecny)
- localization module: use l12 shortcut for module name in UI (rvykydal)
- localization module: replace ksdata.lang with the module in anaconda.
  (rvykydal)
- localization module: add KS support for lang command (rvykydal)
- Return restorecon utility to Fedora 28 mock (jkonecny)
- Include dbus.log when exporting logs (mkolman)
- Reorganize pyanaconda.modules.boss (vponcova)
- Move all DBus errors to pyanaconda.modules.common.errors (vponcova)
- Move common classes and functions to pyanaconda.modules.common (vponcova)
- Close DBus log file when quitting DBus session (jkonecny)
- Enable payload configuration for Install classes (jkonecny)
- Rename files that provide kickstart specifications (vponcova)
- Move the kickstart specification to pyanaconda.core.kickstart (vponcova)
- Start and quit Boss properly (jkonecny)
- Make class from dbus.launcher module (jkonecny)
- Add the kernel option resume= by default (#1206936) (vponcova)

* Wed Feb 28 2018 Martin Kolman <mkolman@redhat.com> - 29.1-1
- Use observers to access the hostname service (vponcova)
- Make safe to observe services on buses that don't have to run (vponcova)
- DBus logs are now saved to /tmp/dbus.log (jkonecny)
- Add tests for toplevel installclass attribs (riehecky)
- Wait for DBus modules for longer time (vponcova)
- Drop dependency on authselect and firewalld (vponcova)
- Fix kickstart version test (vponcova)
- Authconfig is replaced with authselect (#1542968) (vponcova)
- Add support for different message buses (vponcova)
- Fix makeupdates script (vponcova)
- Set up basic logging for DBus modules (vponcova)
- Remove get_dbus_module_logger (vponcova)
- Fix logging of the DBus modules (vponcova)
- Fix the reimport error (vponcova)
- Fix the network module specification (vponcova)
- network module: update_network_data test (rvykydal)
- network module: use Module.Kickstarted instead of ksdata.seen (rvykydal)
- network module: use for hostname in tui (rvykydal)
- network module: handle current hostname (rvykydal)
- network module: handle ksdata.network.hostname (rvykydal)
- network module: add module skeleton (rvykydal)
- Log changes in the kickstart modules. (vponcova)
- Use the Timezone module in UI. (vponcova)
- Start Boss from Anaconda (jkonecny)
- Do not use System DBus (jkonecny)
- Remove anaconda-boss.service (jkonecny)
- Move Anaconda dbus services and confs to session dbus (jkonecny)
- Run DBus session if not present (jkonecny)
- Change pykickstart version (vponcova)
- Move system-logos dependency from anaconda-core to anaconda-gui (mkolman)
- makebumpver: fix parsing of -m option (rvykydal)
- makebumpver: fix -i option (rvykydal)
- Fix tests of the Timezone module (vponcova)
- installclass: add comments to server install class (dusty)
- Don't use deprecated formatErrorMsg (vponcova)
- Use the KickstartError attributes (vponcova)
- kickstart: "clearpart --list" does not work (#1410335) (marcel)
- Use handler in the Timezone module (vponcova)
- Fix the specification of the Bar module (vponcova)
- Use the KickstartHandler class (vponcova)

* Mon Feb 19 2018 Martin Kolman <mkolman@redhat.com> - 28.22-1
- Prevent anaconda-core requiring gjs-console (awilliam)
- Temporarily don't test versions of specified kickstart objects (vponcova)

* Mon Feb 19 2018 Martin Kolman <mkolman@redhat.com> - 28.21-1
- Explain when run dependency_solver without options (jkonecny)
- Clean dd_test code (jkonecny)
- We can't set file permission mode for .so in dd test (jkonecny)
- Rename installclass_atomic to Fedora Atomic Host (jkonecny)
- Support running only nosetests or only some nosetests (jkonecny)
- Do not run tests as root (jkonecny)
- Save start and end time for pylint run (jkonecny)
- Separate grab-logs from ci target in Makefile (jkonecny)
- Remove false positive but disable Pylint in makeupdates script (jkonecny)
- Add copyright to scripts in ./scripts/testing (jkonecny)

* Thu Feb 15 2018 Adam Williamson <awilliam@redhat.com> - 28.20-2
- Prevent anaconda-core requiring gjs-console (awilliam)

* Fri Feb 09 2018 Martin Kolman <mkolman@redhat.com> - 28.20-1
- Check the proxy attribute before accessing it (vponcova)
- Check the noverifyssl attribute before accessing it (vponcova)
- Don't access the url attribute (#1530428) (vponcova)
- Use Fedora Server default partitioning in Atomic (jkonecny)
- Clean code of Atomic install class (jkonecny)
- Migrate Atomic install class (#1491287) (jkonecny)
- Move Atomic install class to Anaconda (#1491287) (#1536853) (jkonecny)
- Make sure that fetch_url is defined. (vponcova)

* Mon Feb 05 2018 Martin Kolman <mkolman@redhat.com> - 28.19-1
- Change pykickstart version. (vponcova)
- Do not deepcopy the kickstart data in the storage (vponcova)
- Replace deepcopy of the method command (vponcova)
- Use pykickstart 3 (vponcova)
- Provide comprehensive log messages about the display mode (vponcova)
- Fix missing logging in some cases of update of ONBOOT value. (rvykydal)
- Fix tests for the timezone module. (vponcova)
- Add the Kickstarted property to the kickstart modules. (vponcova)
- Connect to the observed service and other stuff. (vponcova)
- Prevent 99-copy-lgs.ks from exiting with a 1 (bcl)
- Rename SetUTC to SetIsUTC in the timezone module. (vponcova)

* Thu Jan 18 2018 Martin Kolman <mkolman@redhat.com> - 28.18-1
- Move how to use setup-mock-test-env script to help (jkonecny)
- Add --init as new parameter to setup-mock-test-env (jkonecny)
- Initialize the thread manager at the first import. (vponcova)
- Added tests for the timezone module and other. (vponcova)
- Remove 'i' from iutil module (jkonecny)
- Remove 'i' from isignal module (jkonecny)
- Move isignal module to core/isignal (jkonecny)
- Extract process watch functions to a static class (jkonecny)
- Move regexes module to core/regexes (jkonecny)
- Move i18n module to core/i18n (jkonecny)
- Move constants module to core/constants (jkonecny)
- Move iutil module to core/iutil (jkonecny)
- Move async_utils to core/async_utils (jkonecny)
- Replace gobject GLib by our core/glib (jkonecny)
- Rename run_in_main_thread to run_in_loop (jkonecny)
- Add Timer and PidWatcher abstraction above GLib (jkonecny)
- Create abstraction above GLib event loop (jkonecny)
- Add core/glib module for GLib access (jkonecny)
- Ignore errors for KickstartSpecificationHandler. (vponcova)
- Try to use the PropertiesChanged signal. (vponcova)
- Add timezone module. (vponcova)
- Collect properties changes before emit. (vponcova)
- Use Ping method from the standard interface. (vponcova)
- Recognize members of standard interfaces. (vponcova)
- Add an object observer with cached properties (vponcova)
- Rename modules with Fedora install classes. (vponcova)
- Add support for Variant in .buildstamp (vponcova)
- Fix the Bar module. (vponcova)
- Add pykickstart version to branching policy doc (jkonecny)
- Remove `unstable` branch from documentation (jkonecny)
- Move system-logos to anaconda-core (#1529239) (bcl)

* Fri Jan 05 2018 Martin Kolman <mkolman@redhat.com> - 28.17-1
- Modules should use the proxy pattern. (vponcova)
- Variants need to be instances of the Variant class (vponcova)
- kickstart: support firewall --use-system-defaults (#1526450) (dusty)
- Check payload is set before accessing its data (#1524785) (mkolman)
- Do not fail when test are failing in setup-env script (jkonecny)
- Support running multiple commands at once (jkonecny)
- Support copy Anaconda result dir out of mock (jkonecny)
- Remove dependencies from Makefile (jkonecny)
- Add path to Anaconda in mock to constant (jkonecny)
- Properly exclude packages from the install set (ngompa13)
- Add the _prepare_command helper function to setup-test-env (jkonecny)
- Add run-tests parameter to setup-test-env script (jkonecny)
- Remove /anaconda in mock before copying new one (jkonecny)

* Tue Jan 02 2018 Martin Kolman <mkolman@redhat.com> - 28.16-1
- Improve password checking status and error messages (mkolman)
- Spin kickstarts shouldn't be test dependency (jkonecny)

* Wed Dec 20 2017 Martin Kolman <mkolman@redhat.com> - 28.15-1
- Remove spurious echo call from tmux service file (#1526861) (mkolman)
- Restore fix for RHBZ #1323012 (`set_name` not `setName`) (awilliam)
- Fix Makefile for modules/[foo,bar]/tasks and for install_manager (rvykydal)
- Make passing kickstart to boss more visible. (rvykydal)
- Add tests for KickstartManager. (rvykydal)
- Add kickstart dispatching to anaconda. (rvykydal)
- Add kickstart dispatching to local boss run script (rvykydal)
- Add KickstartManager for Boss. (rvykydal)
- Add method for getting line mapping from kickstart elements to kickstart
  (rvykydal)
- Add info about handled kickstart commands to modules (rvykydal)
- Add missing Makefile for kickstart_dispatcher (rvykydal)

* Mon Dec 18 2017 Martin Kolman <mkolman@redhat.com> - 28.14-1
- Use observers in the install manager (vponcova)
- Modify readme file for tests (jkonecny)
- Do not bump version when testing installation (jkonecny)
- Add set up test environment script (jkonecny)
- Add dependency solver script (jkonecny)
- Differentiate upstream and build-time version (#1493952) (mkolman)
- Fix bad bash '*' expansion when loading kernel modules (#1525841) (jkonecny)
- Fix connection to a signal in the install manager (vponcova)
- Use the InterfaceTemplate in the InstallationInterface (vponcova)
- Use the InterfaceTemplate in the TaskInterface (vponcova)
- Add a base class for DBus interfaces (vponcova)
- Update module manager to use observers (vponcova)
- Add DBus observers for better access to proxies. (vponcova)
- Remove running CI in mock from Makefile (jkonecny)
- Add xfsprogs and git to the test requirements (jkonecny)
- The gettext-devel is required by autogen (jkonecny)
- Remove kickstart-test dependencies from test requires (jkonecny)

* Tue Dec 12 2017 Martin Kolman <mkolman@redhat.com> - 28.13-1
- Unregister and unpublish all DBus services and objects (vponcova)
- Add tests for InstallManager (jkonecny)
- Add tests for Tasks (jkonecny)
- Add run_in_glib decorator for tests (jkonecny)
- Instantiate and publish InstallManager in Boss (jkonecny)
- Add Makefile for install_manager (jkonecny)
- Implement InstallManager with interface (jkonecny)
- Init threading in modules (jkonecny)
- Provide installation tasks from modules (jkonecny)
- Remove *.Anaconda.Modules interface from Boss (jkonecny)
- Implementing example tasks for modules (jkonecny)
- Add Makefile for Task (jkonecny)
- Base implementation of Task (jkonecny)
- Add Task interface class (jkonecny)
- Remove in-memory kickstart representation from traceback file (#1519895)
  (mkolman)
- Support call_when_thread_terminates in ThreadManager (jkonecny)
- Change gtk_action_wait/nowait as general use decorators (jkonecny)
- Add controllable loop to run_boss_locally script (jkonecny)
- Tweak run_boss_locally script (jkonecny)
- Enable SE/HMC file access to repo (vponcova)
- Change string formatting to format method (jkonecny)
- Pass handler instance, not class to SplitKickstartParser (rvykydal)
- Add kickstart parser for splitting kickstart (rvykydal)

* Thu Dec 07 2017 Martin Kolman <mkolman@redhat.com> - 28.12-1
- Fix unit tests (mkolman)
- Fixes in makefiles (vponcova)
- Use the input_checking module for TUI password validation (mkolman)
- Use the input_checking module for user checking (mkolman)
- Use the input_checking module for root password checking (mkolman)
- Use the input_checking module for checking the LUKS passphrase (mkolman)
- Reflect GUISpokeInputCheckHandler changes in installation source spoke
  (mkolman)
- Convert the input checking helpers to use the input_checking module (mkolman)
- Provide more robust method of using the warning message bar (mkolman)
- Remove the validatePassword() method (mkolman)
- Add new input checking module (mkolman)
- fixup! Migrate Workstation InstallClass to anaconda (sgallagh)
- Handle an invalid install class style sheet (vponcova)
- Enhance password checking constants (mkolman)
- Fix interactive defaults (mkolman)
- Modify the PYTHONPATH in run_boss_locally (vponcova)
- Replace get_bus with the class DBus (vponcova)
- Migrate Workstation InstallClass to anaconda (sgallagh)
- Point at new path for fedora-server.css (sgallagh)
- Rename dbus_constants to constants (vponcova)
- Add the boot option inst.ks.all (vponcova)
- Add the boot option inst.stage2.all (vponcova)
- Remove errors for mounting and unmounting (vponcova)
- Override the right method in the task (vponcova)
- Remove useless code (vponcova)
- Support timeout and retries options in %%packages section (vponcova)
- Fix device_name_is_disk to fully support raid devices (vponcova)
- Onlyuse devices of the ignoredisk command should be only disks (vponcova)
- Add the boot option inst.xtimeout (vponcova)
- Do not shadow build-in module variable (jkonecny)
- Module manager is replaceable (jkonecny)
- Remove pyanaconda.constants_text module (vponcova)

* Mon Nov 27 2017 Martin Kolman <mkolman@redhat.com> - 28.11-1
- Bump Blivet GUI version (mkolman)
- Change path to start-module script when running locally (mkolman)
- Handle DBUS module related files in makeupdates (mkolman)
- Handle DBUS_STARTER_ADDRESS not being defined (mkolman)
- Use start-module script in DBUS service files (mkolman)
- Add a DBUS module startup script (mkolman)
- Add Makefile.am for DBUS modules an addons (mkolman)
- Add the setup-updates script (mkolman)
- Add __init__.py file to anaconda/modules (mkolman)
- Add a unit file for Boss startup (mkolman)
- Really install all the right packages on Mac UEFI installs (awilliam)
- Refactor DASD formatting and support detection of LDL DASDs. (vponcova)
- Remove unused import sys from run_boss_locally script (jkonecny)
- Fix blivet imports in the Fedora Server install class (#1513024) (vponcova)
- Update the use of suggest_container_name method (vponcova)
- Devicetree doesn't have protected_dev_names (vponcova)
- Add pyanaconda.dbus to Makefile (vponcova)
- Add pyanaconda.storage to Makefile (#1511735) (vponcova)
- network: GUI, be more robust when displaying vlan parent and id (#1507913)
  (rvykydal)
- network: GUI, fix lookup of existing device configurations (#1507913)
  (rvykydal)
- network: GUI, don't crash on added vlan without device name specified
  (#1507913) (rvykydal)
- Add a script for running Boss & modules locally (mkolman)
- Add an example addon (mkolman)
- Add DBUS module examples (mkolman)
- Add Boss (mkolman)
- Add a base class for DBUS modules (mkolman)
- Add .service and .conf files for the DBUS modules (mkolman)
- Add constants for DBUS module namespaces (mkolman)
- Add support for logging from DBUS modules (mkolman)
- Add the get_bus() method (mkolman)
- Remove storage check for too small swap (#1466964) (vponcova)
- Migrate fedora-server installclass into the anaconda repository (#1466967)
  (rvykydal)

* Thu Nov 09 2017 Martin Kolman <mkolman@redhat.com> - 28.10-1
- Bump required Blivet version to 3.0 (mkolman)
- Add modular server repo to the base repositories (#1506894) (jkonecny)
- Split addon and environment refresh in software TUI (jkonecny)
- Fix changing source don't erase old environment TUI (#1505090) (jkonecny)
- Add logging to TUI software selection spoke (#1505090) (jkonecny)
- Do not try to use protected disks for autopart (vtrefny)
- Adapt new storage tui spoke to storage code move. (dlehman)
- Update blivet upstream URL in testing README. (dlehman)
- Adapt to devicefactory API change. (dlehman)
- Adapt to removal of default rounding in blivet.size.Size. (dlehman)
- Use anaconda's logic for ostree sys/physical root. (dlehman)
- Adapt to removal of blivet.udev.device_is_realdisk. (dlehman)
- Adapt to move of disklabel type logic into DiskLabel. (dlehman)
- Move blivet.partspec into pyanaconda.storage. (dlehman)
- Move blivet.platform to pyanaconda.platform. (dlehman)
- Fix traceback from mocked partitions in clearpart test. (dlehman)
- Move blivet.osinstall to pyanaconda.storage. (dlehman)
- Move autopart from blivet to pyanaconda.storage. (dlehman)

* Thu Oct 26 2017 Martin Kolman <mkolman@redhat.com> - 28.9-1
- Mac EFI installs need grub2-tools (#1503496) (awilliam)
- network: create default ifcfg also for missing default NM connection
  (#1478141) (rvykydal)
- Print screen stack next to exception in TUI (jkonecny)
- Enable Custom GRUB2 Password Utility (#985962) (rmarshall)

* Tue Oct 17 2017 Martin Kolman <mkolman@redhat.com> - 28.8-1
- Bump simpleline version requires (jkonecny)
- Remove DataHolder class (jkonecny)
- Remove EditTUISpoke EditTUIDialog and EditTUISpokeEntry (jkonecny)
- Replace EditTUI* from the TUI Storage spoke (jkonecny)
- Replace EditTUI* from the TUI User spoke (jkonecny)
- Replace EditTUI* from the TUI Source spoke (jkonecny)
- Replace EditTUI* from the TUI Network spoke (jkonecny)
- Password spoke is using PasswordDialog now (jkonecny)
- Return default policy if nothing match (jkonecny)
- Add Dialog and PasswordDialog TUI objects (jkonecny)
- Remove EditTUIDialog from time_spoke (jkonecny)
- packaging: clear downloaded packages repo cache before using it (#1480790)
  (rvykydal)
- Do substitutions only after translating the string (mkolman)
- Fix a translation check error (mkolman)
- Do not run commands in messages in Makefile (jkonecny)
- Fix storage spoke completeness checking (#1496416) (rvykydal)

* Thu Oct 12 2017 Martin Kolman <mkolman@redhat.com> - 28.7-1
- Mark the mount point assignment in TUI as experimental (vpodzime)
- Reset storage on change in text mode (vpodzime)
- Only allow the supported file systems in text mode (vpodzime)
- Textual configuration of mount points (vpodzime)
- Add support for the new 'mount' kickstart command (vpodzime)
- Fix dnf exception repository not set (#1495211) (jkonecny)
- Add logging of complete spokes in GUI. (rvykydal)
- Do not execute storage when the spoke is left with no selected disk
  (#1496327) (rvykydal)
- Reflect building from master branch in the release docs (mkolman)
- Add checks for group names (#1497676) (vponcova)
- Add new checks for user names (#1491006) (vponcova)

* Fri Sep 29 2017 Martin Kolman <mkolman@redhat.com> - 28.6-1
- Add changelog entries from the unstable branch (mkolman)
- Log when we are executing command in chroot (jkonecny)
- Use name instead of index in TUI env selection (#1495204) (jkonecny)
- Fix missing container in TUI source spoke (#1494801) (jkonecny)
- Add MOCK_EXTRA_ARGS to Makefile (jkonecny)
- tui source spoke: initialize nfs values when switching to nfs (rvykydal)
- Deselect encryption when switching to blivet-gui partitioning (vtrefny)
- Add 2 spaces between functions in iutil (jkonecny)
- rpmostreepayload: Fix logic for copying of EFI data (walters)
- rpmostreepayload: Avoid recursing for fstab mounts (walters)
- payload: Add handlesBootloaderConfiguration(), teach bootloader.py (walters)

* Thu Sep 21 2017 Martin Kolman <mkolman@redhat.com> - 28.5-1
- Fix missing id to name environment transition (#1491119) (jkonecny)
- Fix test for unset TUI software environment (#1491119) (jkonecny)
- Rename processingDone to processing_done variable (jkonecny)

* Mon Sep 18 2017 Martin Kolman <mkolman@redhat.com> - 28.4-1
- network: add support for kickstart --bindto=mac for virtual devices
  (#1328576) (rvykydal)
- network: support mac bound network settings as first class (#1328576)
  (rvykydal)
- network: add support for kickstart --bindto=mac for wired devices (#1328576)
  (rvykydal)
- Don't setup the hub twice (#1491333) (vponcova)
- rpmostreepayload: Substitute ${basearch} in ostreesetup ref (walters)
- Perform repo checks only when there are checks available. (rvykydal)
- Add support for repo --metalink (GUI) (#1464843) (rvykydal)
- Add support for repo --metalink (kickstart, tui) (#1464843) (rvykydal)
- Add inst.notmux option (dusty)

* Mon Sep 11 2017 Martin Kolman <mkolman@redhat.com> - 28.3-1
- Add missing dot to the availability status message (mail)
- Bump Simpleline version (jkonecny)
- Make EFIGRUB._efi_binary a property, not a method (awilliam)
- Better storing logs from build and tests (jkonecny)
- Provide a default install class. (vponcova)
- Do not use hidden install classes. (vponcova)
- Make geolocation with kickstart possible (#1358331) (mkolman)
- Run python-meh as modal in TUI (jkonecny)
- Use GLib event loop in the simpleline (jkonecny)
- TUI progress reporting is handled by show_all (jkonecny)
- Add efi_dir to the BaseInstallClass (#1412391) (vponcova)
- Use /usr/bin/python3 shebang once again (miro)

* Mon Sep 04 2017 Martin Kolman <mkolman@redhat.com> - 28.2-1
- Fix catch TUI not main thread exceptions (jkonecny)
- Document Anaconda branching workflow (mkolman)
- Use constants for version number bumps and additions (mkolman)
- Fix closest mirror now needs network (jkonecny)
- Fix restart payload thread in Network spoke GUI (#1478970) (jkonecny)
- Network spoke freeze when testing availability (#1478970) (jkonecny)
- Add support for adding version numbers to makebumpver (mkolman)
- Add support for major version bump to makebumpver (mkolman)
- Fix proxy settings badly used when testing repos (#1478970) (jkonecny)

* Tue Aug 29 2017 Martin Kolman <mkolman@redhat.com> - 28.1-1
- Remove the metacity theme. (vponcova)
- Add the option inst.decorated to allow title bar in GUI (vponcova)
- Move python3-gobject Requires to core (jkonecny)
- Return simpleline removed ipmi calls back (jkonecny)
- Use new list container from Simpleline (jkonecny)
- Remove old simpleline from anaconda (jkonecny)
- Ask multiple times for wrong input (jkonecny)
- Show TUI exception only first time (jkonecny)
- Add simpleline logger to the Anaconda (jkonecny)
- Modify TUI to use new Simpleline package (jkonecny)
- Make 64-bit kernel on 32-bit firmware work for x86 efi machines (pjones)
- Add missing gtk3 required version to spec file (jkonecny)
- Sort spec required versions alphabetically (jkonecny)
- Fix testing of the kickstart version (vponcova)
- Move the installclass command to the %%anaconda section. (vponcova)
- Fix SL install class to use right efi dir (riehecky)
- Fix accelerator key for blivet-gui partitioning (#1482438) (vtrefny)
- Add blivet-gui logs to python-meh file list (vtrefny)
- Remove the title bar in anaconda by default (#1468801) (vponcova)
- Add simple script to read journal with message code source and thread info.
  (rvykydal)

* Mon Aug 14 2017 Martin Kolman <mkolman@redhat.com> - 27.20-1
- Add support for automatic generating of DBus specification. (vponcova)
- Add support for generating XML (vponcova)
- Add support for DBus typing system (vponcova)
- dnfpayload: do not try to contact disabled repo (artem.bityutskiy)
- Add message to setup-test-env is ran (jkonecny)
- Use SHA256 instead of MD5 for repoMDHash (#1341280) (bcl)
- Add lorax-packages.log to bug report. (rvykydal)
- Use SHA256 instead of MD5 for repoMDHash (#1341280) (jkonecny)
- 80-setfilecons: Add a few paths (/var/run, /var/spool) (walters)
- Also capture anaconda-pre logs if they exist (riehecky)
- Don't mock modules with sys in unit tests (vponcova)
- logging: replace SyslogHandler with JournalHandler (rvykydal)
- Add setup-test-env target to the Makefile (jkonecny)
- Add tests for the install class factory (vponcova)
- Support for the installclass kickstart command (vponcova)
- Modules with install classes should define __all__ (vponcova)
- Refactorization of the installclass.py (vponcova)
- docs: minor fixups of release document (rvykydal)
- rescue: add RTD documentation (rvykydal)
- rescue: clean up method for mounting root (rvykydal)
- rescue: separate UI and execution logic (rvykydal)
- Make kickstart rescue command noninteractive. (rvykydal)
- Remove unused argument and code. (rvykydal)

* Thu Jul 27 2017 Radek Vykydal <rvykydal@redhat.com> - 27.19-1
- rpmostreepayload: Set up /var first (walters)
- rpmostreepayload: Explicitly create /var/lib before tmpfiles (walters)
- rpmostreepayload: Rework mount setup to support admin-defined mounts
  (walters)
- rpmostreepayload: try to verify local ostree repo cache (dusty)
- rpmostreepayload: ignore <F25 location, support RHEL (dusty)
- rpmostreepayload: use correct secondary url location (dusty)
- Add tracking of requirements application to requirements container.
  (rvykydal)
- Add langpacks via payload requirements (rvykydal)
- Add NTP_PACKAGE via installation requirements (rvykydal)
- timezone: simplify kickstart setup metod (rvykydal)
- Store payload (packages, groups) requirements in a container. (rvykydal)
- Fix anaconda --help fail with traceback (#1470514) (jkonecny)
- rpmostreepayload: Do /sysroot mount non-recursively (walters)
- Add isolated-test makefile target (jkonecny)
- gui: show supported locales on Atomic Host installs (jlebon)

* Mon Jul 03 2017 Martin Kolman <mkolman@redhat.com> - 27.18-1
- rpmostreepayload: Reuse the local repo as a cache (walters)
- Document how to create Anaconda releases and package builds (mkolman)

* Sat Jul 01 2017 Martin Kolman <mkolman@redhat.com> - 27.17-1
- Require "blivet-gui-runtime" instead of "blivet-gui" (vtrefny)
- Fix a typo in python-meh initialization (#1462825) (mkolman)

* Mon Jun 26 2017 Martin Kolman <mkolman@redhat.com> - 27.16-1
- Install class shouldn't set the default boot fstype (#1463297) (vponcova)
- Store testing logs properly (jkonecny)
- Fix location of the blivet-gui user help (vtrefny)
- netowrk: fix noipv6 option check regression (#1464297) (rvykydal)
- Refactor imports in kickstart.py (jkonecny)
- Use context manager to check KickstartError (jkonecny)

* Wed Jun 21 2017 Martin Kolman <mkolman@redhat.com> - 27.15-1
- Honor --erroronfail kickstart option in cmdline mode (rvykydal)
- Fix import from a renamed module (#1462538) (vponcova)
- Fix the 'non-ASCII characters in password' checks (#1413813) (awilliam)
- Move mock config files to slaves (jkonecny)

* Thu Jun 15 2017 Martin Kolman <mkolman@redhat.com> - 27.14-1
- Bump version of Pykickstart and Blivet (#1113207) (jkonecny)
- Add XFS uuid changer (#1113207) (jkonecny)
- Support --when parameter in snapshot (#1113207) (jkonecny)
- Add snapshot support (#1113207) (jkonecny)

* Wed Jun 14 2017 Martin Kolman <mkolman@redhat.com> - 27.13-1
- Fix source.glade renaming mixup (#1461469) (mkolman)
- Separate blivet-daily builds in mock config (jkonecny)
- network: bind to device name (not hwaddr) when dumping connections (#1457215)
  (rvykydal)

* Tue Jun 13 2017 Martin Kolman <mkolman@redhat.com> - 27.12-1
- Show warning if swap is smaller then recommended (#1290360) (vponcova)

* Tue Jun 06 2017 Martin Kolman <mkolman@redhat.com> - 27.11-1
- Fix renaming error (mkolman)
- Add a getter for the Anaconda root logger (mkolman)
- Disable test-install in Makefile (jkonecny)

* Thu Jun 01 2017 Martin Kolman <mkolman@redhat.com> - 27.10-1
- Bump Blivet version (mkolman)
- Remove GUI logging prefixes from Network spoke (mkolman)
- Rename TUI spokes (mkolman)
- Rename GUI spokes (mkolman)
- Rename anaconda_argparse.py to argument_parsing.py (mkolman)
- Rename install_tasks.py to installation_tasks.py (mkolman)
- Rename install.py to installation.py (mkolman)
- Rename threads.py to threading.py (mkolman)
- Get special purpose loggers from anaconda_loggers (mkolman)
- Use structured logging in Anaconda modules (mkolman)
- Use unique 3 letter log level names (mkolman)
- Use constants for special purpose logger names (mkolman)
- Add the anaconda_loggers module (mkolman)
- Rename anaconda_log.py to anaconda_logging.py (mkolman)
- Add support for structured logging to the anaconda logger (mkolman)
- Make it possible to set filters for file handlers (mkolman)
- Add custom filter and formatter support for the syslog handler (mkolman)
- Add AnacondaPrefixFilter (mkolman)
- Fixes for Pylint 1.7 (vponcova)
- Add support for IPoIB in tui (#1366935) (rvykydal)
- Fix pylint unused import error (jkonecny)
- network: handle multiple connections for one device better (#1444887)
  (rvykydal)
- Fix setting errors and warnings in the StorageCheckHandler (vponcova)
- Add inst.waitfornet option (#1315160) (rvykydal)
- network: catch exception when reading in-memory connection being removed
  (#1439220) (rvykydal)

* Thu May 25 2017 Martin Kolman <mkolman@redhat.com> - 27.9-1
- Add support for DNF-2.5.0 (jkonecny)
- Fix simpleline_getpass related Pylint warning (mkolman)
- Provide access to simpleline App instance (mkolman)
- Make it possible to use a custom getpass() (mkolman)
- Set the default filesystem type from a kickstart file (vponcova)
- Adapt to our new daily builds of Anaconda (jkonecny)
- Provide access to simpleline App instance (mkolman)
- Make it possible to use a custom getpass() (mkolman)
- Perform recursive copying of driver disk RPM repo contents (esyr)
- network: fix setting hostname via boot options (#1441337) (rvykydal)
- Fix a typo in an error message (esyr)
- Use the function we already have for applying disk selection (#1412022)
  (rvykydal)
- Ignore disks labeled OEMDRV (#1412022) (rvykydal)
- network: create dracut arguments for iSCSI root accessed via vlan (#1374003)
  (rvykydal)
- Test if Anaconda can be installed inside of mock (jkonecny)
- Remove run_install_test test (jkonecny)
- rpmostreepayload: Handle /var as a user-specified mountpoint (walters)
- Fix the addon handlers for the checkbox (#1451754) (vponcova)
- Show the text of completions in the datetime spoke. (vponcova)
- Use new daily-blivet copr builds (jkonecny)
- Prevent TUI from crashing with a single spoke on a hub (mkolman)

* Tue May 09 2017 Martin Kolman <mkolman@redhat.com> - 27.8-1
- Bump Pykickstart version (mkolman)

* Fri May 05 2017 Martin Kolman <mkolman@redhat.com> - 27.7-1
- Make some missed adjustments to blivet API changes. (#1440134) (dlehman)
- Bump required version for blivet-gui (vtrefny)
- BlivetGuiSpoke: Set keyboard shortcuts for blivet-gui (#1439608) (vtrefny)
- BlivetGuiSpoke: Refresh blivet-gui UI after spoke is entered (vtrefny)
- Really fix with tmux 2.4 (version comparison was busted) (awilliam)
- Show or hide the content of the expander on Fedora (vponcova)
- itertools.chain can be iterated only once (#1414391) (vponcova)

* Fri Apr 28 2017 Martin Kolman <mkolman@redhat.com> - 27.6-1
- Use `time.tzset()` to apply timezone changes when we can (awilliam)
- Tweak epoch definition to fix system clock setting (#1433560) (awilliam)
- Optimize payload thread restart on network change (jkonecny)
- Add unit test for RepoMDMetaHash object (#1373449) (jkonecny)
- Make the formating in payload consistent (#1373449) (jkonecny)
- Fix Anaconda forces payload restart when network (not)change (#1373449)
  (jkonecny)
- Catch race-condition error reading from in-memory connection being removed
  (#1373360) (rvykydal)
- network tui: fix changing ipv4 config from static to dhcp (#1432886)
  (rvykydal)
- Allow setting up bridge for fetching installer image from kickstart
  (#1373360) (rvykydal)

* Thu Apr 27 2017 Martin Kolman <mkolman@redhat.com> - 27.5-1
- make anaconda working back again with tmux2.4 (pallotron)
- Trigger the entered signal only once the screen is shown (#1443011) (mkolman)
- Use constants in storage checker constraints. (vponcova)
- Gtk: Fix creating images from resources. (vponcova)
- Fix partial kickstart software selection in GUI (#1404158) (jkonecny)
- Removed unused code in the Software spoke (#1404158) (jkonecny)
- Fix selection logic in Software spoke (#1404158) (jkonecny)
- Fix Driver Disc documentation (#1377233) (jkonecny)
- Support DD rpm loading from local disk device (#1377233) (jkonecny)
- Gtk: Replace deprecated get_misc_set_alignment in widgets. (vponcova)
- Gtk: Replace deprecated Gtk.Viewport.get_v/hadjustment. (vponcova)
- Gtk: Replace deprecated methods. (vponcova)
- Set the info bar only once if the partitioning method changes. (vponcova)
- Fix pylint issue Catching too general exception Exception (jkonecny)
- Support --noboot and --noswap options in autopartitioning (#1220866)
  (vponcova)
- Support --nohome option in the autopartitioning (vponcova)

* Tue Apr 11 2017 Martin Kolman <mkolman@redhat.com> - 27.4-1
- Hide options based on storage configuration method (#1439519) (mkolman)
- Catch exception when reading from in-memory connection being removed
  (#1439051) (rvykydal)
- docs/boot-options.rst: Fix #dhcpd anchor (mopsfelder)
- docs/boot-options.rst: Remove trailing spaces (mopsfelder)
- Fix logging of the storage checker report. (vponcova)
- Fix a property name of luks devices in storage checking (#1439411) (vponcova)
- Bump required version for blivet-gui (vtrefny)
- Use newly created swaps after the installation (#1439729) (vtrefny)
- docs/boot-options.rst: Fix #dhcpd anchor (mopsfelder)
- docs/boot-options.rst: Remove trailing spaces (mopsfelder)
- Set default FS type for blivet-gui (#1439581) (vtrefny)
- Display progress for the post installation phase (mkolman)
- Display progress for the post installation phase (mkolman)
- Increase verbosity of lvmdump in pre logging script (#1255659) (jkonecny)

* Thu Mar 30 2017 Martin Kolman <mkolman@redhat.com> - 27.3-1
- Enable the install class to customize the storage checking (vponcova)
- Replace sanity check with more advanced storage checker (vponcova)
- Various log-capture script improvements (mkolman)
- Rename StorageChecker to StorageCheckHandler (vponcova)

* Thu Mar 16 2017 Martin Kolman <mkolman@redhat.com> - 27.2-1
- Correction of some typographic mistakes in documentation. (rludva)
- Fix bullet point formatting in contribution guidelines (mkolman)
- Propagate firstboot --disable to Screen Access Manager (mkolman)
- util: Add script to capture logs (riehecky)
- Fix a typo (mkolman)
- Correction of some typographic mistakes in documentation. (rludva)
- Enhance git-find-branch script (jkonecny)
- Improve how storage configuration settings are displayed (mkolman)
- util: Add script to capture logs (riehecky)
- Propagate firstboot --disable to Screen Access Manager (mkolman)

* Mon Mar 06 2017 Martin Kolman <mkolman@redhat.com> - 27.1-1
- We should not have pyanaconda submodules on PYTHONPATH (vponcova)
- Lock empty root password during kickstart installation (#1383656) (mkolman)
- Use system Python when running Anaconda (mkolman)
- Remove unused false positives for pylint (vtrefny)
- Fix pylint error in BlivetGUI spoke (vtrefny)
- Fix tests by renaming packaging to payload (jkonecny)
- Rescue mode should wait for the storage and luks devices (#1376638) (vponcova)

* Mon Feb 27 2017 Martin Kolman <mkolman@redhat.com> - 26.21-1
- Add blivet-gui as requirement for the GUI package (vtrefny)
- Add a bottom bar to the Blivet GUI spoke (mkolman)
- Hide storage config spokes marked by SAM as visited (mkolman)
- Keep last used partitioning method selected (mkolman)
- Rollback planned storage changes if partitioning method changes (mkolman)
- Add blivet-gui spoke (vpodzime)
- docs: fix formating a bit for Links (Frodox)
- Fix a typo (mkolman)
- Polish unsupported filesystems in the custom spoke (jkonecny)

* Tue Feb 07 2017 Martin Kolman <mkolman@redhat.com> - 26.20-1
- Update dracut test for network --ipv6gateway (rvykydal)
- Correctly propagate --ipv6gateway to ifcfg files(#1170845) (mkolman)
- network: respect --activate value for bridge from kickstart (rvykydal)
- network: fix --activate for bridge slaves configured via %%pre ks (rvykydal)
- network: activate bridge for first network command in ks via %%pre (rvykydal)
- network: unify slave connection names for ks %%pre with ks and gui (rvykydal)
- network: bind slave connections to DEVICE, not HWADDR (#1373360) (rvykydal)
- Do not allow creating ntfs filesystem in custom spoke (vtrefny)
- Various minor formatting fixes (mkolman)
- PEP8 and refactoring for packaging (mkolman)
- PEP8 and refactoring for vnc.py (mkolman)
- PEP8 and refactoring for storage_utils.py (mkolman)
- PEP8 and refactoring for network.py (mkolman)
- PEP8 and refactoring for kickstart.py (mkolman)
- PEP8 and refactoring for image.py (mkolman)
- Cosmetic PEP8 and refactoring for flags.py (mkolman)
- PEP8 and refactoring for exception.py (mkolman)
- PEP8 and refactoring for bootloader.py (mkolman)
- PEP8 and refactoring for anaconda_log.py (mkolman)
- Validate dasd and zfcp user input (#1335092) (vponcova)
- network: use introspection data from libnm instead of libnm-glib (lkundrak)

* Mon Jan 16 2017 Martin Kolman <mkolman@redhat.com> - 26.19-1
- Use initialization controller for spoke initialization (mkolman)
- Add module initialization controller (mkolman)
- Fix link to the documentation in the README file (jkonecny)
- There is no thread for dasd formatting in tui. (vponcova)
- Move the (mkolman)
- Fix the status of the StorageSpoke for dasd formatting (#1274596) (vponcova)

* Mon Jan 09 2017 Martin Kolman <mkolman@redhat.com> - 26.18-1
- Always refresh the size of swap before autopartitioning. (vponcova)
- Run the space check only if the spokes are complete (#1403505) (vponcova)
- Ignore result directory with logs from tests (jkonecny)
- Disable pylint no-member error for re.MULTILINE (jkonecny)
- Fix nosetests to use newest python3 (jkonecny)
- Disable the button if iscsi is not available (#1401263) (vponcova)
- Include Python 3.6 sysconfigdata module in initramfs (#1409177) (awilliam)
- Nicer __repr__ for hubs and spokes (mkolman)
- Close the .treeinfo file after the retrieve. (vponcova)

* Wed Jan 04 2017 Martin Kolman <mkolman@redhat.com> - 26.17-1
- Fix a GTK Widget related deprecation warning (mkolman)
- Fix GTK screen/display related deprecation warnings (mkolman)
- Fix GObject and GLib deprecation warnings (mkolman)
- Fix selection of no software environment (#1400045) (vponcova)
- Use signals for Spoke & Hub entry/exit callbacks (mkolman)
- Fix the name of StorageDiscoveryConfig attribute (#1395350) (vponcova)
- Iutil PEP8 & formatting fixes (mkolman)
- Add inst.ksstrict option to show kickstart warnings as errors. (vponcova)
- Use the structured installation task classes (mkolman)
- Improved password quality checking (mkolman)
- Add unit tests for password quality checking (mkolman)
- Use Enum for password status constants (mkolman)
- Use a sane unified password checking policy (mkolman)
- Add install task processing classes and unit tests (mkolman)
- Add a signal/slot implementation (mkolman)
- Set correctly the default partitioning. (vponcova)

* Wed Dec 14 2016 Martin Kolman <mkolman@redhat.com> - 26.16-1
- rpmostreepayload: Rework binds to be recursive (walters)
- Let DNF do its own substitutions (riehecky)
- Bump Blivet version due to systemd-udev dependency (mkolman)
- Don't log "Invalid bridge option" when network has no --bridgeopts.
  (rvykydal)
- Fix updating of bridge slave which is bond. (rvykydal)

* Mon Dec 05 2016 Martin Kolman <mkolman@redhat.com> - 26.15-1
- Don't pass storage to firstboot.setup() (mkolman)
- RTD fixes (mkolman)
- Catch ValueError from LVM part in Blivet library (jkonecny)
- Handle unexpected storage exception from blivet (jkonecny)
- Add sudo to test requires (jkonecny)
- network: fix network --noipv4 in %%pre (rvykydal)
- fix typo in systemd service keyword (mail)
- Fix pylint issue in ks_version_test (jkonecny)
- Move Anaconda tests to mock (jkonecny)
- Add checks to git-find-branch script (jkonecny)
- Remove intermediate pot files in po-push (mkolman)
- Allow install classes to set alternate states for firstboot/initial-setup
  (riehecky)

* Wed Nov 23 2016 Martin Kolman <mkolman@redhat.com> - 26.14-1
- Changed the required version of BlockDev to 2.0. (vponcova)
- Remove auto generated documentation (mkolman)
- Fix generated zanata.xml from https unstable branch (jkonecny)
- Don't crash if the UIC file can't be written (#1375702) (mkolman)

* Wed Nov 23 2016 Martin Kolman <mkolman@redhat.com> - 26.13-1
- Fix calling of can_touch_runtime_system function (jkonecny)
- fix formating a bit (gitDeveloper)
- Fix zanata.xml.in in substitution variables (mkolman)

* Thu Nov 17 2016 Martin Kolman <mkolman@redhat.com> - 26.12-1
- Mock chroot environment is chosed by a git branch (jkonecny)
- Set Zanata branch from git-find-branch script (jkonecny)
- Add git-find-branch script for finding parent branch (jkonecny)
- fix pykickstart docks link (gitDeveloper)
- aarch64 now has kexec-tools (pbrobinson)
- Resolve directory ownership (mkolman)
- Fix user interaction config handling in image & directory install modes
  (#1379106) (mkolman)
- tui: Available help system (vponcova)
- network: index team slave connection names starting with 1 (rvykydal)

* Thu Nov 10 2016 Martin Kolman <mkolman@redhat.com> - 26.11-1
- Relax blivet dependency to >= 2.1.6-3 (awilliam)
- Bump required Blivet version (#1378156) (mkolman)
- Fix bad exception handling from blivet in iscsi (#1378156) (jkonecny)
- tui: New class for prompt (vponcova)
- iSCSI: adjust to change in blivet auth info (#1378156) (awilliam)
- Disable false positive pylint error (jkonecny)
- Add some error checking when users don't provide input for DASD devices.
  (sbueno+anaconda)
- Add some error checking when users don't provide input for zFCP devices.
  (sbueno+anaconda)
- Fix tui timezone region selection by name (vponcova)

* Fri Nov 04 2016 Martin Kolman <mkolman@redhat.com> - 26.10-1
- F26_DisplayMode was added by non-interactive mode (jkonecny)
- Fix pyanaconda tests for display mode (jkonecny)
- Fix parse-dracut to support new kickstart displaymode (jkonecny)
- Add boot option inst.noninteractive to the docs (jkonecny)
- Abort installation when Playload exc rise in a NonInteractive mode (jkonecny)
- Support non interactive mode in standalone spokes (jkonecny)
- Non-interactive mode support for Password and User spokes (jkonecny)
- Raise NonInteractive exception in Hubs event loop (jkonecny)
- Raise exception for noninteractive mode in Hub (jkonecny)
- Add new pykickstart noninteractive mode (jkonecny)
- Disable bad kickstart command on F25 (jkonecny)
- Improve DNF error message to be more understandable (jkonecny)
- tui: Add software group selection (vponcova)
- use blivet iSCSI singleton directly in storage spoke (awilliam)
- Correct deviceLinks to device_links (blivet renamed it) (awilliam)
- Instantiate the zFCP object ourselves now. (#1384532) (sbueno+anaconda)
- Fix the way DASD list is determined. (#1384532) (sbueno+anaconda)
- Add tests for payload location picking (#1328151) (jkonecny)
- Fix picking mountpoint for package download (#1328151) (jkonecny)
- Improve packaging logs without DEBUG logging (jkonecny)

* Tue Oct 25 2016 Martin Kolman <mkolman@redhat.com> - 26.9-1
- Move the collect() function to iutil (mkolman)
- Update messiness level (mkolman)
- PEP8 and general refactoring for the main anaconda.py (mkolman)
- Move kickstart file parsing code to startup_utils (mkolman)
- Don't directly import items from anaconda_log (mkolman)
- Remove old useless code (mkolman)
- Move the rescue ui startup code to the rescue module (mkolman)
- Move set-installation-thod-from-anaconda code to startup_utils (mkolman)
- Move the live startup code to startup_utils (mkolman)
- Move code printing the startup note to startup_utils (mkolman)
- Move the pstore cleanup function to startup_utils (mkolman)
- Move the prompt_for_ssh function to startup_utils (mkolman)
- Move logging setup to startup_utils (mkolman)
- Move the geolocation startup code to a separate function (mkolman)
- Unify addons path variable name (mkolman)
- PEP 8 for startup_utils.py (mkolman)
- PEP 8 for display.py (mkolman)
- Move VNC startup checking to a separate function (mkolman)
- Move imports to the top of the file in display.py (mkolman)
- Refactor display mode handling (mkolman)
- Move display setup & startup tasks out of anaconda.py (mkolman)
- Remove main and extra Zanata pot files on master (jkonecny)
- Remove main and extra pot files before zanata push (jkonecny)
- Don't send intermediate pot files to zanata (gh#791) (awilliam)
- Improve message to be clearer in rescue.py (jkonecny)
- Add option to show password in password field (vponcova)
- Generate a list of DASDs in GUI storage spoke. (#1378338) (sbueno+anaconda)
- Echoing 4de0ec44bdf0f68545bb55bb5fea00464b65fcab May as well include the SL
  file (riehecky)
- Fixup class name for CentOS install class (riehecky)
- Fix a typo in SAM file header (mkolman)
- Skip live image on usb when checking storage for mounted partitions
  (#1369786) (rvykydal)

* Mon Oct 03 2016 Martin Kolman <mkolman@redhat.com> - 26.8-1
- Fix network spoke being incorrectly marked as mandatory (#1374864) (mkolman)

* Fri Sep 30 2016 Samantha N. Bueno <sbueno+anaconda@redhat.com> - 26.7-1
- Increse python3-blivet version to 1:2.1.5 (jkonecny)
- Fix dnf.repo.Repo now requires dnf.conf.Conf (jkonecny)
- Provides compatibility with DNF-2.0 (jmracek)

* Tue Sep 27 2016 Martin Kolman <mkolman@redhat.com> - 26.6-1
- Don't deactivate all storage in anaconda-cleanup. (#1225184) (dlehman)
- Stop setting ANACONDA udev environment variable. (#1225184) (dlehman)

* Tue Sep 27 2016 Martin Kolman <mkolman@redhat.com> - 26.5-1
- Improved driver disk copying (#1269915) (mkolman)
- Fix screenshot taking logic (#1327456) (mkolman)
- Change blank lines to pep8 for Dracut DUD test (jkonecny)
- Tweak lambda use in Dracut test (jkonecny)
- Add Dracut test for reloading mod dependencies (jkonecny)

* Wed Sep 21 2016 Martin Kolman <mkolman@redhat.com> - 26.4-1
- Fix NTP server list fetching when running in IS (#1374810) (mkolman)
- rpmostreepayload: Clean up use of sysroot files a bit (walters)
- rpmostreepayload: Fix remote handling to use correct sysroot (walters)

* Mon Sep 19 2016 Martin Kolman <mkolman@redhat.com> - 26.3-1
- network: set onboot correctly for vlan on bond device in ks (#1234849)
  (rvykydal)
- network: don't show ibft configured devices in UI (#1309661) (rvykydal)
- iscsi: don't generate kickstart iscsi commands for offload devices (#1252879)
  (rvykydal)
- iscsi: allow installing bootloader on offload iscsi disks (qla4xxx)
  (#1325134) (rvykydal)
- network: adapt to changed NM ibft plugin enablement configuration (#1371188)
  (rvykydal)
- network: don't activate bond/team devices regardless of --activate (#1358795)
  (rvykydal)
- Fix traceback when payload have None as url (#1371494) (jkonecny)
- Add new Dracut test and fix another ones (#1101653) (jkonecny)
- Fix bug when we add set to list (#1101653) (jkonecny)
- Add new helper script files to build system (#1101653) (jkonecny)
- Document new helper scripts to the DriverDisk README (#1101653) (jkonecny)
- Fix driver unload is disabling network settings (#1101653) (jkonecny)
- dud: fix multiple inst.dd=http:// instances stalling in dracut (#1268792)
  (rvykydal)
- network: fix ksdata generating for for non-active virtual devices (#1321288)
  (rvykydal)
- network: update kickstart data also with bond bridge slaves (#1321288)
  (rvykydal)
- network: add support for bridge bond slaves (#1321288) (rvykydal)
- screen_access: Ensure we write config to real sysroot (walters)
- Add release commit support to makebumpver (mkolman)
- Makefile improvents for separate release commits & tarball creation
  (mkolman)
- network: add support for --no-activate kickstart opton (#1277975) (rvykydal)
- fixup! Add base.close() after base.do_transaction (RhBug:1313240) (jmracek)
- Add base.close() after base.do_transaction (RhBug:1313240) (jmracek)

* Tue Sep 06 2016 Martin Kolman <mkolman@redhat.com> - 26.2-1
- Add git merging examples to the contribution guidelines (mkolman)
- network: don't stumble upon new Device.Statistics NM dbus iface (#1370099)
  (rvykydal)
- Current Anaconda is not compatible with DNF 2.0.0 (jkonecny)
- Filter out all merge commits from the changelog (mkolman)
- Make it possible to override Zanata branch name (mkolman)
- Switch to argparse & autodetect name, version and bug email address (mkolman)
- Fix multi-inheritance (phil)
- Fix replacement of deprecated DNF method (jkonecny)
- Replace deprecated method of DNF (jmracek)
- Static checker recommended improvements (mkolman)
- Fix replacement of deprecated DNF method (jkonecny)
- Replace deprecated method of DNF (jmracek)

* Mon Aug 29 2016 Samantha N. Bueno <sbueno+anaconda@redhat.com> - 26.1-1
- Fix a pylint no-member warning (mkolman)
- Translate press-c-to-continue correctly in TUI (#1364539) (mkolman)
- Fix bootDrive driveorder fallback (#1355795) (jkonecny)
- Fix bootloader when re-using existing /boot part (#1355795) (jkonecny)
- Add support for device specification variants (#1200833) (mkolman)
- Revert "Update zanata.xml for f25-devel branch." (sbueno+anaconda)
- Update zanata.xml for f25-devel branch. (sbueno+anaconda)
- Add option to override efi_dir (phil)
- efiboot: stderr= is not an option to efibootmgr (phil)
- Fix EFI grub1 case (phil)
- Make Fedora module not so grabby (phil)
- Add centos module to pyanaconda (phil)
- network: don't require gateway for static ipv4 config in TUI (#1365532)
  (rvykydal)
- Improve connection network change detection (jkonecny)
- Revert "Revalidate source only if nm-con-ed change settings (#1270354)"
  (jkonecny)
- Fix anaconda-pre.service wasn't properly installed (#1255659) (jkonecny)
- Rename function for better consistency (#1259284) (rvykydal)
- Update error message for consistency (#1259284) (rvykydal)
- Add more specific username check messages also to gui (#1360334) (rvykydal)
- fix style guide test false positive on username variable (#1350375)
  (rvykydal)
- tui: use functions instead of fake REs for checking values (#1350375)
  (rvykydal)
- tui: get proper index of entry we are handling in input (#1331054) (rvykydal)
- tui: fix user name validity checking (#1350375) (rvykydal)
- More descriptive message on invalid username (kvalek)
- Fix another pep8 name issue (jkonecny)
- iscsi: fix getting iscsi target iface of bound target (#1359739) (rvykydal)
- Fix needsNetwork testing only additional repositories (#1358788) (jkonecny)
- Fix restart payload only when repo needs network (#1358788) (jkonecny)
- Cleanup remaining runlevel references (mkolman)
- Clarify a nosave related log message (mkolman)
- Use Screen Access Manager (mkolman)
- Add screen entry/exit callbacks (mkolman)
- Add screen access manager (mkolman)
- A simple formatting fix (mkolman)
- Fix another blivet-2.0 pep8 error (jkonecny)
- Quickfix of failing test (japokorn)
- Some docstring refactoring & typo fixes for the TUI base classes (mkolman)
- Add a file about contributing. (sbueno+anaconda)
- Store logs before anaconda starts (#1255659) (japokorn)
- DD can now replace existing drivers (#1101653) (japokorn)
- Use the F25 timezone kickstart command version (mkolman)
- Use sshd-keygen.target instead of hardcoded sshd-keygen script (jjelen)
- Make it possible to disable sshd service from running. (#1262707)
  (sbueno+anaconda)
- Change bootloader boot drive fallback (jkonecny)
- Fix of Python3x uncompatible commands (japokorn)
- Add NTP server configuration to the TUI (#1269399) (mkolman)
- Move the NTP server checking constants to constants.py (mkolman)
- Use a constant for the NTP check thread name prefix (mkolman)
- Fix another victim of the python 2->3 conversion. (#1354020) (dshea)
- Attempt to unload modules updated by a driver disk (dshea)
- Fix the processing of device nodes as driver disks (dshea)

* Fri Jul 08 2016 Brian C. Lane <bcl@redhat.com> - 25.20-1
- Allow kickstart users to ignore the free space error (dshea)
- Stop kickstart when space check fails (bcl)
- Service anaconda-nm-config is missing type oneshot (jkonecny)
- Fix dhcpclass to work both via kickstart and the boot cmdline. (clumens)
- network: handle also ifcfg files of not activated virtual devices (#1313173)
  (rvykydal)
- network: check onboot value in ksdata, not NM connections (#1313173)
  (rvykydal)
- network: do not activate device on kickstart --onboot="yes" (#1341636)
  (rvykydal)

* Fri Jun 24 2016 Brian C. Lane <bcl@redhat.com> - 25.19-1
- hostname: don't set installer env hostname to localhost.localdomain
  (#1290858) (rvykydal)
- hostname: add tooltip to Apply button (#1290858) (rvykydal)
- hostname: fix accelerator collision (#1290858) (rvykydal)
- hostname: don't set hostname in initrafms of target system (#1290858)
  (rvykydal)
- hostname: set current hostname from target system hostname on demand
  (#1290858) (rvykydal)
- hostname: suggest current hostname for storage containers (#1290858)
  (rvykydal)
- hostname: don't set target system static hostname to current hostname
  (#1290858) (rvykydal)
- network tui: do not activate device when setting its onboot value (#1261864)
  (rvykydal)
- network tui: edit persistent configuration, not active connection (#1261864)
  (rvykydal)
- network: validate netmask in tui (#1331054) (rvykydal)
- Add wordwrap to text mode and use it by default (#1267881) (rvykydal)
- Fix adding new VG in Custom spoke can't be applied (#1263715) (jkonecny)
- Fix SimpleConfigFile file permissions (#1346364) (bcl)
- Re-configure proxy when updateBaseRepo is called (#1332472) (bcl)

* Fri Jun 17 2016 Brian C. Lane <bcl@redhat.com> - 25.18-1
- Only use <> for markup (#1317297) (bcl)
- Update iscsi dialog for Blivet 2.0 API change (bcl)
- Use the signal handlers to set initial widget sensitivies (dshea)
- Fix bad sensitivity on boxes in source spoke (jkonecny)
- Fix install-buildrequires (bcl)
- Added optional [/prefix] as pattern (kvalek)
- Require network for network-based driver disks (dshea)
- Add missing pkgs to install-buildrequires (#612) (phil)
- Increase the required version of gettext (dshea)
- Fix the name sensitivity in the custom spoke. (dshea)

* Fri Jun 10 2016 Brian C. Lane <bcl@redhat.com> - 25.17-1
- Revert "Temporarily disable translations" (bcl)
- Change where to look for the iscsi object (#1344131) (dshea)
- Fix old blivet identifiers (#1343907) (dshea)
- Fix a covscan warning about fetch-driver-net (#1269915) (bcl)
- Fix crash when NM get_setting* methods return None (#1273497) (jkonecny)
- Overwrite network files when using ks liveimg (#1342639) (bcl)
- Stop using undocumented DNF logging API (bcl)
- Use the LUKS device for encrypted swap on RAID (dshea)
- Keep the subdir in driver disk update paths (dshea)
- Warn about broken keyboard layout switching in VNC (#1274228) (jkonecny)
- Make the anaconda-generator exit early outside of the installation
  environment (#1289179) (mkolman)

* Fri Jun 03 2016 Brian C. Lane <bcl@redhat.com> - 25.16-1
- Add a button to refresh the disk list. (dlehman)
- Only try to restart payload in the Anaconda environment (mkolman)
- Make current runtime environment identifiers available via flags (mkolman)
- Display storage errors that cause no disks to be selected (#1340240) (bcl)
- Fix the SourceSwitchHandler pylint errors differently. (clumens)
- Fix pylint errors. (clumens)
- Update the disk summary on Ctrl-A (dshea)
- Revert "Refresh the view of on-disk storage state every 30 seconds."
  (dlehman)
- Refresh the view of on-disk storage state every 30 seconds. (dlehman)
- Handle unsupported disklabels. (dlehman)
- Use a blivet method to remove everything from a device. (dlehman)
- Tighten up ResizeDialog._recursive_remove a bit. (dlehman)
- Only look for partitions on partitioned disks. (dlehman)
- NFS DDs installation now works correctly (#1269915) (japokorn)
- Remove unused on_proxy_ok_clicked from Source spoke (jkonecny)
- send all layouts to localed for keymap conversion (#1333998) (awilliam)
- Small cleanup (mkolman)

* Fri May 27 2016 Brian C. Lane <bcl@redhat.com> - 25.15-1
- Resolve shortcut conflict between "Desired Capacity" and "Done" (yaneti)
- network: don't crash on devices with zero MAC address (#1334632) (rvykydal)
- Remove Authors lines from the tops of all files. (clumens)
- Related: rhbz#1298444 (rvykydal)
- New Anaconda documentation - 25.14 (bcl)
- Catch DNF MarkingError during group installation (#1337731) (bcl)
- Fix TUI ErrorDialog processing (#1337427) (bcl)
- Clean up yelp processes (#1282432) (dshea)

* Fri May 20 2016 Brian C. Lane <bcl@redhat.com> - 25.14-1
- Temporarily disable translations (bcl)
- Don't crash when selecting the same hdd ISO again (#1275771) (mkolman)

* Thu May 19 2016 Brian C. Lane <bcl@redhat.com> - 25.13-1
- Fix writeStorageLate for live installations (#1334019) (bcl)
- Remove the locale list from zanata.xml (dshea)
- Ditch autopoint. (dshea)
- Ditch intltool. (dshea)
- Rename fedora-welcome to fedora-welcome.js (dshea)
- Fix UEFI installation after EFIBase refactor (bcl)
- Fix error handling for s390 bootloader errors (sbueno+anaconda)
- Deselect all addons correctly (#1333505) (bcl)
- gui-testing needs isys to be compiled. (clumens)
- Add more to the selinux check in tests/gui/base.py. (clumens)

* Fri May 13 2016 Brian C. Lane <bcl@redhat.com> - 25.12-1
- Add single language mode (#1235726) (mkolman)
- Move default X keyboard setting out of the Welcome spoke (mkolman)
- Rerun writeBootLoader on Live BTRFS installs (bcl)
- Check for mounted partitions as part of sanity_check (#1330820) (bcl)
- Merge pull request #620 from dashea/new-canary (dshea)
- Update the required pykickstart version. (dshea)
- Implement %%packages --excludeWeakdeps (#1331100) (james)
- Fix bad addon handling when addon import failed (jkonecny)
- Add retry when downloading .treeinfo (#1292613) (jkonecny)
- Return xprogressive delay back (jkonecny)
- Change where tests on translated strings are run. (dshea)
- Merge the latest from translation-canary (dshea)
- Squashed 'translation-canary/' changes from 5a45c19..3bc2ad6 (dshea)
- Add new Makefile target for gui tests (atodorov)
- Define missing srcdir in run_gui_tests.sh and enable coverage (atodorov)
- Split gui test running out into its own script. (clumens)
- Look higher for the combobox associated with an entry (#1333530) (dshea)
- Use createrepo_c in the ci target. (dshea)
- Compile glib schema overrides with --strict. (dshea)

* Fri May 06 2016 Brian C. Lane <bcl@redhat.com> - 25.11-1
- Don't join two absolute paths (#1249598) (mkolman)
- Don't crash when taking a screenshot on the hub (#1327456) (mkolman)
- Fix pylint errors. (phil)
- Factor out common grub1/grub2 stuff into mixin, and other factoring (phil)
- Add GRUB1 (legacy) support back to Anaconda (phil)

* Fri Apr 29 2016 Brian C. Lane <bcl@redhat.com> - 25.10-1
- Handle unmounting ostree when exiting (bcl)
- ostree: Use bind mounts to setup ostree root (bcl)
- ostree: Skip root= setup when using --dirinstall (bcl)
- disable_service: Specify string format args as logging params. (clumens)
- Ignore failure when disable services that do not exist (phil)
- Get rid of an unused variable in the network spoke. (clumens)
- Revalidate source only if nm-con-ed change settings (#1270354) (jkonecny)
- Merge solutions for test source when network change (#1270354) (jkonecny)
- Changes in network state revalidate sources rhbz#1270354 (riehecky)

* Wed Apr 27 2016 Brian C. Lane <bcl@redhat.com> - 25.9-1
- Use the iutil functions for interacting with systemd services. (dshea)
- Add methods to enable and disable systemd services. (dshea)
- Do not add .service to the end of service names. (dshea)
- Remove detach-client from tmux.conf (dshea)
- Use Blivet 2.0 for set_default_fstype (#607) (sgallagh)
- Remove dnf from the list of required packages. (#605) (dshea)
- Add access to the payload from addons (#1288636) (jkonecny)
- Disable pylint warnings related to the log handler fixer. (dshea)
- Allow the metacity config dir to be overriden. (dshea)
- Do not include /usr/share/anaconda files in the gui package. (dshea)
- Work around logging's crummy lock behavior. (dshea)
- Use rm -r to remove the temporary python site directory. (dshea)
- Remove the subnet label for wired devices. (#1327615) (dshea)
- Fix how unusued network labels are hidden (#1327615) (dshea)
- Remove yum_logger (bcl)
- Remove the lock loglevel (bcl)
- Use a temporary user-site directory for the tests. (dshea)
- Build everything for make ci. (dshea)
- Ignore some E1101 no-member errors when running pylint (bcl)
- Sprinkle the code with pylint no-member disable statements (bcl)
- Catch GLib.GError instead of Exception (bcl)
- Update storage test for Blivet 2.0 API change. (bcl)
- Initialize missing private methods in BasePage class (bcl)
- Update kickstart.py for Blivet 2.0 API change. (bcl)
- Use namedtuple correctly in kexec.py (bcl)
- Add more requires to make password checking still work. (#1327411) (dshea)
- Rename isS390 to match the renames in blivet. (dshea)
- Suppress signal handling when setting zone from location (#1322648) (dshea)
- Refresh metadata when updates checkbox changes (#1211907) (bcl)

* Fri Apr 15 2016 Brian C. Lane <bcl@redhat.com> - 25.8-1
- network: handle null wireless AP SSID object (#1262556) (awilliam)
- Change new_tmpfs to new_tmp_fs. (clumens)
- Add support for kickstart %%onerror scripts. (clumens)
- Show network spoke in the TUI reconfig mode (#1302165) (mkolman)
- network: copy static routes configured in installer to system (#1255801)
  (rvykydal)
- network: fix vlan over bond in kickstart (#1234849) (rvykydal)
- network: use NAME to find ifcfg on s390 with net.ifnames=0 (#1249750)
  (rvykydal)
- Get rid of the reimport of MultipathDevice. (clumens)
- Fix iSCSI kickstart options aren't generated (#1252879) (jkonecny)
- Fix adding offload iSCSI devices (vtrefny)
- Make the list-harddrives script mode robust (mkolman)

* Fri Apr 08 2016 Brian C. Lane <bcl@redhat.com> - 25.7-1
- Blivet API change getDeviceBy* is now get_device_by_* (bcl)
- network: don't set 803-3-ethernet.name setting (#1323589) (rvykydal)
- Log non-critical user/group errors (#1308679) (bcl)
- Fix btrfs metadata raid level kwarg. (dlehman)
- docs: Add release building document (bcl)
- Minor improvements - README and test dependencies (atodorov)
- Add more matches for network connectivity (atodorov)

* Mon Apr 04 2016 Brian C. Lane <bcl@redhat.com> - 25.6-1
- Remove an unused import from anaconda-cleanup. (clumens)
- Don't use booleans in Requires (#1323314) (dshea)
- Set CSS names on all of the anaconda classes. (#1322036) (dshea)
- Don't crash if no groups are specified (#1316816) (dshea)
- Fix only one address is shown in anaconda (#1264400) (jkonecny)
- Fix call to update optical media format. (#1322943) (dlehman)
- Reset invalid disk selection before proceeding. (dlehman)
- Multiple Dogtail tests improvements (atodorov)
- Do not allow liveinst with --image or --dirinstall (#1276349) (dshea)
- New Anaconda documentation - 25.5 (bcl)

* Wed Mar 30 2016 Brian C. Lane <bcl@redhat.com> - 25.5-1
- Don't provide subclasses of the multipath or dmraid commands. (clumens)
- Add support for chunksize raid kickstart parameter. (vtrefny)
- Convert to blivet-2.0 API. (dlehman)

* Thu Mar 24 2016 Brian C. Lane <bcl@redhat.com> - 25.4-1
- Require that the English locale data be available. (#1315494) (dshea)
- Revert "Change the default locale to C.UTF-8 (#1312607)" (#1315494) (dshea)
- Make windows in metacity closable (#1319590) (dshea)
- Fix the use of CSS psuedo-classes in the widgets. (dshea)
- Add reason when logging invalid repository (#1240379) (jkonecny)

* Sat Mar 19 2016 Brian C. Lane <bcl@redhat.com> - 25.3-1
- Apply language attributes to all labels within anaconda. (dshea)
- Add a function to apply a PangoAttrLanguage to a label. (dshea)
- Add functions to watch changes to a container widget. (dshea)
- Switch to the adwaita icon theme. (dshea)
- Fix duplicate network settings in dracut (#1293539) (jkonecny)
- Fix create device with bad name when parsing KS (#1293539) (jkonecny)
- Use a lock for repoStore access (#1315414) (bcl)
- Add missing inst prefix to the nokill option in docs (mkolman)
- Merge pull request #551 from wgwoods/master-multiple-initrd-dd-fix (wwoods)
- fix multiple inst.dd=<path> args (rhbz#1268792) (wwoods)

* Fri Mar 11 2016 Brian C. Lane <bcl@redhat.com> - 25.2-1
- Load the system-wide Xresources (#1241724) (dshea)
- Use an icon that exists in Adwaita for the dasd confirmation (dshea)
- Make it possible to skip saving of kickstarts and logs (#1285519) (mkolman)
- Add a function for empty file creation (#1285519) (mkolman)
- Run actions for argparse arguments (#1285519) (mkolman)

* Wed Mar 09 2016 Brian C. Lane <bcl@redhat.com> - 25.1-1
- don't install kernel-PAE on x86_64 (#1313957) (awilliam)
- except block in py3.5 undefines the variable (bcl)
- Remove some history from the liveinst setup. (dshea)
- Do not run the liveinst setup if not in a live environment. (dshea)
- Set GDK_BACKEND=x11 before running anaconda from liveinst. (dshea)
- Run zz-liveinst as an autostart application (dshea)
- Translate the help button. (dshea)
- Translate the required space labes in resize.py (dshea)

* Fri Mar 04 2016 Brian C. Lane <bcl@redhat.com> - 25.0-1
- Add device id to dasdfmt screen. (#1269174) (sbueno+anaconda)
- Unify displayed columns in custom spoke dialogs. (#1289577) (sbueno+anaconda)
- Show some confirmation to users if adding a DASD was successful. (#1259016)
  (sbueno+anaconda)
- Hotfix for missing storage in payload class (#1271657) (jkonecny)
- Check to see if DD repo is already in addOn list (#1268357) (bcl)
- Use the default levelbar offset values. (dshea)
- Do not change the GUI language to a missing locale. (#1312607) (dshea)
- Don't crash when setting an unavailable locale (#1312607) (dshea)
- Change the default locale to C.UTF-8 (#1312607) (dshea)
- Update the libtool version-info. (dshea)
- Use CSS to style the internal widgets. (dshea)
- Move the widgets pixmaps into resources. (dshea)
- Add a resource bundle to libAnacondaWidgets (dshea)
- Rename show_arrow and chosen_changed to show-arrow and chosen-changed (dshea)
- Remove an invalid transfer notation. (dshea)
- Stop using SGML in the docs. (dshea)
- Change the install test URL. (dshea)
- Fix nfs source crash when options change (#1264071) (bcl)
- makebumpver: Add a --dry-run option (bcl)
- NTP should have better behavior (#1309396) (jkonecny)
- Manually set clock shifts on UI idle (#1251044) (rmarshall)
- Don't remove selected shared part when Delete all (#1183880) (jkonecny)
- Don't delete shared/boot parts in deleteAll (#1183880) (jkonecny)

* Fri Feb 19 2016 Brian C. Lane <bcl@redhat.com> - 24.13-1
- tests/gui enhancements (atodorov)
- Fix gui tests for anaconda move to anaconda.py (atodorov)
- Use a different ipmi command to log events. (clumens)
- Clarify that a string in list-screens is actually a regex. (clumens)
- Merge pull request #513 from wgwoods/update-dd-docs (wwoods)
- updated driver updates docs (wwoods)
- Add specification for the user interaction config file (mkolman)
- Update zanata webui URL in translation doc. (dlehman)
- Tweak partition removal in Custom spoke (jkonecny)
- Do not skip evaluation after removing partitions (jkonecny)
- Import iutil earlier so we can use ipmi_report from check_for_ssh. (clumens)
- Make disconnect_client_callbacks more resilient (#1307063). (clumens)
- Move the langpacks install into to a separate function. (dshea)
- Fix _find_by_title method in Accordion (jkonecny)

* Fri Feb 12 2016 Brian C. Lane <bcl@redhat.com> - 24.12-1
- Use host storage for directory or image install dnf download (bcl)
- Log payloadError so we know why installation failed. (bcl)
- Add the addons directory to the rpm. (dshea)
- Use the packaged version of ordered-set (dshea)
- Remove an unused import (dshea)
- Add an uninstall hook for the renamed anaconda (dshea)
- Make langpack work in DNF (#1297823) (jsilhan)
- New Anaconda documentation - 24.11 (bcl)

* Fri Feb 05 2016 Brian C. Lane <bcl@redhat.com> - 24.11-1
- Fix makeupdates for anaconda move to anaconda.py (bcl)
- Rename ./anaconda to ./anaconda.py to work around coverage.py #425 (atodorov)
- Remove special handling for interruptible system calls. (dshea)
- Handle PEP 3101 strings in the gettext context check (dshea)
- Improve RHS summary strings in multiselection (#1265620) (jkonecny)
- Increase GI version required of AnacondaWidgets (jkonecny)
- Increment version of g-introspection for widgets (jkonecny)
- Increment the AnacondaWidgets version (jkonecny)
- Switch to the new Initial Setup unit name (#1299210) (mkolman)
- Uncomment self.check_lang_locale_views in tests/gui/ (atodorov)
- Add dogtail to test requirements (atodorov)
- Add config for easier combining of kickstart and Jenkins coverage data
  (atodorov)
- Apply the fallback style to anaconda selectors. (dshea)
- Redo the stylesheet for Gtk 3.19+ (dshea)
- Directly overwrite /usr/share/anaconda/anaconda-gtk.css (dshea)
- Merge pull request #463 from dashea/translation-tests (dshea)
- Display the name of the addon while executing it (bcl)
- Add page selection summary to the right side (#1265620) (jkonecny)
- Ask when removing new items in multiselection (#1265620) (jkonecny)
- Add multiselection with SHIFT key (#1265620) (jkonecny)
- Use show_arrow feature implemented in Selector (#1265620) (jkonecny)
- Add new property to show/hide arrow in Selector (#1265620) (jkonecny)
- Change selection logic when opening Page (#1265620) (jkonecny)
- Add new BasePage class (#1265620) (jkonecny)
- Add signal and methods to MountpointSelector (#1265620) (jkonecny)
- Fix errors with multiselection (#1265620) (jkonecny)
- Accordion class now process events for selectors (#1265620) (jkonecny)
- Change cammel case for accordion.py to new pep8 (jkonecny)
- Move selection logic from custom spoke to accordion (#1265620) (jkonecny)
- Modify ConfirmDeleteDialog now the checkbox is optional (#1265620) (jkonecny)
- Multiselection works in GUI with remove (#1265620) (jkonecny)
- Add multiselection to Accordion with control key (#1265620) (jkonecny)
- Remove bad translations from the source tarball. (dshea)
- Treat warnings from xgettext as errors. (dshea)
- Run translation-canary tests from make check. (dshea)
- Do not run pylint on translation-canary (dshea)
- Squashed 'translation-canary/' content from commit 5a45c19 (dshea)

* Fri Jan 29 2016 Brian C. Lane <bcl@redhat.com> - 24.10-1
- Add a finished method to spokes (#1300499) (bcl)
- Handle DeviceConfiguration with con = None (#1300499) (bcl)
- Log detailed information about installed packages (bcl)
- s/KickstartValueError/KickstartParseError. (clumens)
- Move requiredDeviceSize to the main Payload class (#1297905) (dshea)

* Fri Jan 08 2016 Brian C. Lane <bcl@redhat.com> - 24.9-1
- Handle unexpected DNF exit (bcl)
- Fix bad space needed messages (jkonecny)
- nosetests-3.5 is now the right version. (clumens)
- Ignore a pylint error about how we're using Popen (dshea)
- Mark an unused variable as unused (dshea)
- Ignore type-related errors for types pylint can't figure out (dshea)
- Import errors are just regular errors now (dshea)
- Replace the remaining log.warn calls with log.warning. (dshea)
- Fix an erroneously bare raise statement (dshea)
- Replace the deprecated assertEquals with assertEqual (dshea)
- Don't add a None to the list of things to unmount on ostree installs.
  (clumens)

* Wed Dec 02 2015 Brian C. Lane <bcl@redhat.com> - 24.8-1
- Fix pylint problems in the gui testing code. (clumens)
- Merge 9c5e02392d0401a3bd0adecedea03535595773ef into
  67b569253c724639c2490f5fab70f7111f699b3f (atodorov)
- Fix the replacement suggestion for "hostname" (dshea)
- Automatically generate sr (dshea)
- Fix PropertyNotFoundError PermHwAddress (#1269298) (jkonecny)
- Make sure python3.5 code can run in early initrd (bcl)
- Replace <list>.delete() with <list>.remove() in user.py (sujithpandel)
- Rename everything that still refers to LiveCD (atodorov)
- Updates to progress and storage tests (atodorov)
- Multiple changes to DogtailTestCase (atodorov)
- Move all Python files into the main gui/ directory (atodorov)
- Simplify tests by removing OutsideMixin and update Creator (atodorov)
- Modify existing tests to match latest anaconda behavior and environment
  (atodorov)
- Temporary disable test code which doesn't work (atodorov)
- Make tests/gui/ execute ./anaconda from git (atodorov)
- Add window title (#1280077) (mkolman)
- Replace execReadlines with check_output in parse-kickstart_test.py (bcl)
- Fix a spelling error in the hardware error message (#1284165). (clumens)

* Wed Nov 18 2015 Brian C. Lane <bcl@redhat.com> - 24.7-1
- Collect test-suite.log from all 'make check' invocations. Closes #452
  (atodorov)
- Fix parse-kickstart_test.py. (clumens)
- Remove mkdud.py. (clumens)
- Remove the kickstart_tests directory. (clumens)
- Always quote values in ifcfg- files (#1279131) (bcl)
- Include original kickstart in /root/original-ks.cfg (#1227939) (bcl)
- strip spaces from extlinux label and default (#1185624) (bcl)
- Report kernel failures during kickstart tests. (clumens)
- Make sure unicode in kickstart works. (dshea)
- Set the window icon (dshea)
- Only run space check in TUI if spokes are complete. (#1279413)
  (sbueno+anaconda)
- Allow a user's primary group to be created in --groups (#1279041) (dshea)
- Remove uses of broad-except. (dshea)
- Add a test for all that container minimization stuff. (clumens)
- Use the partition command in one of the kickstart_tests. (clumens)
- Don't clear the _currentIsoFile if another iso was selected (bcl)
- makeupdates: Include utils/handle-sshpw (bcl)
- Add --sshkey to kickstart sshpw command (#1274104) (bcl)
- Split exception description from exception traceback (jkonecny)
- Show DNF exception instead of silent exit (jkonecny)
- Combine results from all gettext_tests into one log file (atodorov)
- Try to run make ci with real translations. (dshea)
- Untranslate undisplayed TreeView column headers. (dshea)
- Add a test for hidden translatable strings (dshea)
- Add the translated string to markup error messages. (dshea)
- Test glade translations by default (dshea)
- Change the way glade tests are run. (dshea)
- Remove the accelerator test. (dshea)
- Add the test lib directory to $PYTHONPATH in the commit hook (dshea)
- network: create ifcfg files in tui if needed (#1268155) (rvykydal)
- Do not limit ONBOOT default setting to url and nfs installation methods
  (#1269264) (rvykydal)
- ibft: fix setting dracut boot args for static ibft nic configuration
  (#1267526) (rvykydal)
- network: Don't set --device link default for hostname only network cmd
  (#1272274) (rvykydal)
- network: assume --device=link as default also for ks on hd (#1085310)
  (rvykydal)
- network: use ibftx interface for iSCSI from iBFT in dracut (#1077291)
  (rvykydal)
- network: add s390 options to default ifcfg files (#1074570) (rvykydal)

* Fri Nov 06 2015 Brian C. Lane <bcl@redhat.com> - 24.6-1
- Fix a pylint error in the previous commits. (clumens)
- Honor ANACONDA_WIDGETS_OVERRIDES (atodorov)
- Load anaconda-gtk.css from ANACONDA_DATA if specified (atodorov)
- Use the correct path for ui categories (atodorov)
- Typo fix, it's ANACONDA_WIDGETS_DATA not ANACONDA_WIDGETS_DATADIR (atodorov)
- Allow wired network properties more grid space. (dshea)
- Improve language selection at low resolutions. (dshea)
- Make reclaim work with small screens and big labels (dshea)
- allow repo with only a name if it's a pre-defined one (#1277638) (awilliam)
- Only raise thread exceptions once (#1276579) (bcl)
- Use py3.4 crypt and salt (bcl)
- Be more careful with incomplete device types (#1256582) (dshea)
- Fix an import error in rpmostreepayload.py. (clumens)
- Fix Testing docs inclusion in Sphinx (bcl)
- Ignore interfaces with invalid VLAN IDs. (dshea)
- Cleaner logging of .treeinfo return conditions in dependant function.
  (riehecky)
- Update link to upstream kickstart docs (opensource)
- rpmostreepayload: Also unmount internal mounts during shutdown (walters)
- rpmostreepayload: Fix two issues with mounting (walters)
- Add a README for kickstart tests. (clumens)
- Make the documentation match the environment variable. (clumens)
- Check that cache PVs (if any) are in the VG the LV belongs to (#1263258)
  (vpodzime)
- Fix the alignment of the "Label" label in custom (dshea)
- Use unsafe caching during kickstart tests. (clumens)

* Wed Oct 28 2015 Brian C. Lane <bcl@redhat.com> - 24.5-1
- Improve install space required estimation (#1224048) (jkonecny)
- Update the on-disk snapshot of storage when adv. disks are added (#1267944)
  (vpodzime)
- Check that ipv6 kickstart outputs the right ip= (dshea)
- Change a variable name for pylint. (dshea)
- Do not run time_initialize for image and directory installations (#1274103)
  (bcl)
- Remove unused properties (dshea)
- Do not modify the kickstart user data until apply() (dshea)
- Make AdvancedUserDialog.run() more readable (dshea)
- Improve the behavior of the home directory input. (dshea)
- Stop setting inappropriate properties in ksdata. (dshea)
- Update the password strength bar during the password strength check. (dshea)
- Remove unnecessary grab_focus and set_sensitive calls (dshea)
- Use signal handlers in the user spoke more sensibly. (dshea)
- Fix potential issues with the username guesser. (dshea)
- Make kickstart tests growing LVs stricter (vpodzime)
- Point coverage.py to the full path of pyanaconda/ (atodorov)
- Don't set BOOTPROTO= when it isn't set (jbacik)
- Pass strings to blockdev.dasd_format, not a DASDDevice object. (#1273553)
  (sbueno+anaconda)
- Revert "Use yum to install the mock buildroot for now." (dshea)
- decode package name for /etc/sysconfig/kernel (RHBZ #1261569) (awilliam)
- Add tests for the more complicated command line options (dshea)
- Store fewer kinds of things in the dirinstall option. (dshea)
- Fix the parsing of selinux=0 (#1258569) (dshea)
- Include a local $ANACONDA_DATADIR in the test environment. (dshea)
- Move the command line arguments to anaconda_argparse. (dshea)
- Don't crash while logging binary output. (dshea)
- Decode program output even if there is no output (#1273145) (dshea)
- Add a test for _run_program with binary output (dshea)
- Test execWithCapture when the command outputs nothing. (dshea)
- Fix a long line in kickstart_tests/functions.sh. (clumens)
- Merge pull request #414 from vpodzime/master-lvm_log (vpodzime)
- Save the lvm.log Blivet may produce (vpodzime)

* Fri Oct 16 2015 Brian C. Lane <bcl@redhat.com> - 24.4-1
- Hide the places sidebar in the ISO chooser widget. (dshea)
- Use GtkResponseType values in the iso chooser dialog (dshea)
- Do not use deprecated getDevicesByInstance method (vtrefny)
- By default, skip those kickstart tests we know to be failing. (clumens)
- Fix pylint unused import (jkonecny)
- network: handle bridge device appearing before its connection (#1265593)
  (rvykydal)
- Use $KSTEST_URL in tests that still had dl.fp.o hardcoded. (dshea)
- Support CONNECT in the test proxy server. (dshea)
- Extract the file used by liveimg as a prereq (dshea)
- Convert the proxy script to a prereq. (dshea)
- Add a prereqs function to kickstart tests. (dshea)
- Fix traceback when trying to create list of unformatted DASDs. (#1268764)
  (sbueno+anaconda)
- network: handle missing connections of a device configured in GUI better
  (rvykydal)
- network: don't set NM_CONTROLLED=no for root on SAN. (rvykydal)
- Add support for other systemd units to kickstart service command (bcl)
- Merge pull request #388 from wgwoods/dd-in-initrd-fix (wwoods)
- Set the password checkbox for empty kickstart passwords. (dshea)
- Do not set the password input text with unencrypted passwords. (dshea)
- Install input checks before modifying the user GUI (#1256065) (dshea)
- Fix a lying error message in style_guide.py (dshea)
- Use "Enter" instead of "Return" for the keyboard key. (dshea)
- New Anaconda documentation - 24.3 (bcl)
- Include missing test files and scripts in Makefile.am/tarball (atodorov)
- dracut: accept inst.dd=[file:]/dd.iso (#1268792) (wwoods)
- Do not override StorageChecker.errors in StorageSpoke (#1252596) (vtrefny)
- Lookup IPv6 address without brackets (#1267872) (bcl)
- Mangle the boot device differently for systemd (#1241704) (dshea)
- Fail the media check if the systemd service failed to start. (dshea)

* Fri Oct 02 2015 Brian C. Lane <bcl@redhat.com> - 24.3-1
- Properly translate c-to-continue on the root selection screen (mkolman)
- Check minimal memory requirements properly (#1267673) (jstodola)
- Allow users to be created with an existing GID. (dshea)
- Add a test for creating a user with an existing GID. (dshea)
- Add tests for gids embmedded in the user groups list. (dshea)
- Allow the kickstart --groups list to specify GIDs. (dshea)
- Add a --groups argument to the user ks test. (dshea)
- Fix the locale pattern packages-instlangs-3 looks for. (dshea)
- Raise an error if osimg cannot be found (#1248673) (bcl)
- Use the bootloader raid levels for bootloader installation (#1266898) (bcl)
- Use otps.display_mode during early startup (#1267140) (mkolman)
- Mount stage2 cdrom after running driver-updates (#1266478) (bcl)
- Get rid of an unused import in the user spoke. (clumens)
- Log crashes from the signal handler. (dshea)
- Save a core file when anaconda crashes. (dshea)
- Keep environment selection when reentering the software spoke (#1261393)
  (mkolman)
- Only show the user spoke if no users are specified in kickstart (#1253672)
  (mkolman)
- Fix 'cat: /tmp/dd_disk: No such file or directory' (#1251394) (jkonecny)
- Do not display curl 404 errors that can be safely ignored (vtrefny)
- Catch blkid failure in driver-updates (#1262963) (bcl)
- Add kickstart tests for %%packages --instLangs (dshea)
- Do not display markup in showDetailedError. (dshea)
- Skip OEMDRV if interactive DD is requested (#1254270) (bcl)
- Drivers are simply under /run/install/DD-x/ (#1254270) (bcl)
- Fix branding when iso is downloaded from nfs or hd (#1252756) (jkonecny)
- Use yum to install the mock buildroot for now. (dshea)
- Rename the gettext tests (dshea)
- Bring back the KSTEST_HTTP_ADDON_REPO substitution in nfs-repo-and-addon.sh
  (clumens)
- Run substitution checks on the right kickstart file. (clumens)
- Tell gettext that anaconda is not a GNU package. (dshea)
- Ignore environment modification warnings in docs/conf.py (dshea)
- Check for unsubstituted strings before running a test. (dshea)
- Autopart use 90%% of disk capacity for required space compare (#1224048)
  (jkonecny)
- Fix include packages install size when downloading on root (#1224048)
  (jkonecny)
- Enable and improve the check for swap LV size in LVM cache kickstart tests
  (vpodzime)
- make-sphinx-docs: Add modules needed to document tests (bcl)
- Add test documentation (atodorov)
- Fix how the reqpart test checks for /boot, again. (clumens)
- Add a way to get default settings when running the kickstart_tests. (clumens)
- Change how we ignore non-tests in kickstart_tests. (clumens)
- Various fixes to substitution strings in kickstart_tests. (clumens)
- Move kickstart_test .ks files to .ks.in. (clumens)

* Fri Sep 11 2015 Brian C. Lane <bcl@redhat.com> - 24.2-1
- Handle driver rpms retrieved via network (#1257916) (bcl)
- Fix the types passed to chown_dir_tree (#1260318) (dshea)
- Add a test for home directory reuse (dshea)
- Use MDRaidArrayDevice.members instead of .devices (dshea)
- Make sure anaconda reads in ks file from OEMDRV device. (#1057271)
  (sbueno+anaconda)
- Try to deal with expected errors from devicetree.populate (#1257648)
  (vpodzime)
- Revert "Temporarily disable generating a coverage report." (clumens)
- Fix a DBus InvalidProperty handling (jkonecny)
- Fix another bash syntax problem in kickstart-genrules.sh (#1057271)
  (sbueno+anaconda)
- Add a test for the rootpw kickstart command (dshea)
- Add tests for setRootPassword (dshea)
- Add a /boot partition to the reqpart test. (clumens)
- Fix up a statement that's not assigned to anything. (clumens)
- Temporarily disable generating a coverage report. (clumens)
- Don't try to concatenate a list with a string (#1252444) (mkolman)
- Activate coverage for tests executed with sudo (atodorov)
- set sysroot correctly when setting root password (#1260875) (awilliam)
- Add a test for kickstarts that %%include a URL (dshea)
- Add missing python dependencies for requests. (#1259506) (dshea)
- Serve the http addon repos from the test tmpdir (dshea)
- Make make-addon-pkgs easier to use from within a test (dshea)
- Add a simple http server for use in kickstart tests. (dshea)
- Add a script to print an IP address for the host. (dshea)
- Add a cleanup hook that can be defined by kickstart tests (dshea)
- Move kickstart test support files into a separate directory. (dshea)
- Fix a python3 related error in the pre-commit hook (dshea)
- network: gui spoke TODO cleanup (rvykydal)
- libnm in spoke: add missing connection for eth device with Configure
  (rvykydal)
- libnm in spoke: allow adding missing connection for eth device externally
  (rvykydal)
- libnm in spoke: wait for valid state of added device before adding to list
  (rvykydal)
- libnm in spoke: use libmn objects instead of names an uuids (device on/off)
  (rvykydal)
- libnm in spoke: to check if device is activated just use its object
  (rvykydal)
- libnm in spoke: use connnection objects instead of uuids (edit connection)
  (rvykydal)
- libnm in spoke: refresh early when device is added (rvykydal)
- libnm in spoke: use connection object instead of uuid (DeviceConfiguration)
  (rvykydal)
- libnm in spoke: share nm client in standalone and normal spoke (rvykydal)
- libnm in spoke: add enterprise wpa connection using libnm client (rvykydal)
- libnm in spoke: use AccessPoint object in place of ssid bytearray (rvykydal)
- libnm in spoke: delete connection using libnm client (rvykydal)
- libnm in spoke: replace python-dbus workaround calls for ap security flags
  (rvykydal)
- libnm in spoke: call get_data() on ap.get_ssid() result to get ssid bytes
  (rvykydal)
- libnm in spoke: showing ip configuration of a device (rvykydal)
- libnm in spoke: NMClient -> NM.Client (rvykydal)
- libnm in spoke: gi.NetworkManager -> gi.NM (rvykydal)
- libnm in spoke: Revert "Fix crash when new device appear in Welcome screen
  (#1245960)" (rvykydal)
- libnm in spoke: Revert "Fix crash when connections are changing (#1245960)"
  (rvykydal)
- Add an ignoredisk --drives= test. (clumens)
- Add a test for the reqpart command. (clumens)
- Grab anaconda.coverage on tests that reimplement validate(). (clumens)
- Install driver-updates (dshea)
- Fix a typo in service enablement in kickstart.py. (clumens)
- Get rid of the extraneous cats and greps in user.ks. (clumens)
- Add sshkey testing to the user kickstart_test. (clumens)
- Add a kickstart test in Arabic. (clumens)
- Verify Initial Setup services are present before turning them ON/OFF
  (#1252444) (mkolman)
- Don't crash if the Japanese PC-98 keyboard is selected (#1190589) (mkolman)
- Report on all local files and exclude what we don't need instead of
  explicitly including paths we may not be aware of. (atodorov)
- Change "failed to download" messages from critical to warning. (clumens)
- getcode -> status_code in a live payload error message. (clumens)
- Fix a bash error in kickstart-genrules.sh (#1057271) (sbueno+anaconda)
- specify if=virtio,cache=none for VM drives (atodorov)
- update the test b/c latest anaconda doesn't allow weak passwords (atodorov)
- Specify format=raw to avoid warning from qemu (atodorov)
- update for Python3 nose (atodorov)
- Add a services.sh file to match the existing services.ks. (clumens)
- Add types to all existing kickstart tests. (clumens)
- Add the ability to mark kickstart tests with a type. (clumens)
- Run nm-connection-editor with the --keep-above flag (#1231856) (mkolman)

* Mon Aug 31 2015 Brian C. Lane <bcl@redhat.com> - 24.1-1
- Add a test for the user and group creation functions. (dshea)
- Get rid of libuser. (#1255066) (dshea)
- s/$releasever/rawhide/ (clumens)
- LVM on RAID kickstart test (vpodzime)
- unbuffered read in python3 only works for binary (bcl)
- don't crash if no environment set in interactive (#1257036) (awilliam)
- network: compare with ssid bytes, not str (rvykydal)
- Add dependencies for running the tests/gui tests (atodorov)
- Fix first run environment setup in software spoke (#1257036) (jkonecny)
- Stop pretending liveinst+rescue is supported (#1256061). (clumens)
- Defer to Fedora distro-wide settings for password strength (#1250746) (dshea)
- New Anaconda documentation - 24.0 (bcl)
- Do a better job reporting failures from kickstart_tests. (clumens)
- Preserve coverage results from running the kickstart_tests. (clumens)

* Mon Aug 24 2015 Brian C. Lane <bcl@redhat.com> - 24.0-1
- Remove from the docs repo=hd installation with installable tree (jkonecny)
- Fix a race between a window continuing and the next starting (#1004477)
  (dshea)
- Start hubs with the buttons insensitive. (dshea)
- Do not replace the standard streams if not necessary. (dshea)
- Fix inst.repo=hd: is not working (#1252902) (jkonecny)
- Kickstart: Added SELinux test. (kvalek)
- Kickstart tests related to SELinux. (kvalek)
- Package install and debug message logging. (kvalek)
- Don't crash if incorrect environment is set in kickstart (#1234890) (mkolman)
- Fix I/O issues when anaconda is started without a locale. (dshea)
- Move locale environment logic into localization.py (dshea)
- network: fix configuring team in kickstart pre (#1254929) (rvykydal)
- Merge pull request #311 from atodorov/add_local_coverage (clumens)
- Merge pull request #308 from atodorov/rawhide_missing_deps (clumens)
- Enable test coverage in CI (atodorov)
- Fix the single-spoke TUI message for Python 3. (dshea)
- Merge pull request #291 from atodorov/update_coverage_switch (clumens)
- Add missing requirements (atodorov)
- Add basic kickstart tests for LVM Thin Provisioning (vpodzime)
- Use the default mirrorlist instead of fixed repo URL in kickstart tests
  (vpodzime)
- Destroy the keyboard layout dialog when finished (#1254150) (dshea)
- Do not encode the geoloc timezone to bytes (#1240812) (dshea)
- use inst.debug as alternative option to start coverage (atodorov)

* Mon Aug 17 2015 Brian C. Lane <bcl@redhat.com> - 23.20-1
- Skip source url checks when network is off (#1251130) (bcl)
- Don't set net.device to link if there is no ksdevice (#1085310) (bcl)
- Reading carrier while link is down raises IOError (#1085310) (bcl)
- Don't write nfs repos to the target system (#1246212) (bcl)
- Make sure username entered in TUI if create a user chosen. (#1249660)
  (sbueno+anaconda)
- Write the empty dnf langpacks.conf to the right directory (#1253469) (dshea)
- Add pyanaconda test for network.check_ip_address (jkonecny)
- Replace IPy package by ipaddress (jkonecny)
- Correctly check return code when running rpm from makeupdates (mkolman)
- Fix crash when new device appear in Welcome screen (#1245960) (jkonecny)
- Fix crash when connections are changing (#1245960) (jkonecny)
- Make LVM cache kickstart tests more robust (vpodzime)
- product.img buildstamp should override distribution buildstamp (#1240238)
  (bcl)
- On incomplete ks, don't automatically proceed with install. (#1034282)
  (sbueno+anaconda)
- Update the translation doc with zanata branching incantations.
  (sbueno+anaconda)
- Merge pull request #287 from kparal/patch-1 (clumens)
- boot-options.rst: add a note about nfsiso (kamil.paral)
- Few fixes and amendments for the boot_options.rst file (vpodzime)
- Prevent issues with encrypted LVs on renamed VGs (#1224045) (vpodzime)
- Create and use snapshot of on-disk storage with no modifications (#1166598)
  (vpodzime)
- Implement the class for storage snapshots (vpodzime)
- Prevent any changes in the StorageSpoke if just going back (vpodzime)
- Make StorageSpoke's on_back_clicked less complicated (vpodzime)
- Add kickstart tests for the LVM cache kickstart support (vpodzime)
- Disable packages-multilib, for now. (clumens)
- Make sure the liveimg test shuts down when it finishes. (clumens)
- Change how success is checked for the basic-ostree test. (clumens)

* Fri Aug 07 2015 Brian C. Lane <bcl@redhat.com> - 23.19-1
- Add basic support for LVM cache creation in kickstart (vpodzime)
- Use labels for the rest of the non-autopart test results. (dshea)
- Use a disk label to find the filesystem for escrow results (dshea)
- Use someone else's code for PID file management. (dshea)
- Prevent incomplete translations from making the TUI unusable (#1235617)
  (mkolman)
- Apply the environment substitutions more liberally in nfs-repo-and-addon
  (dshea)
- Use stage2=hd: instead of stage2=live: (dshea)
- Add test for liveimg kickstart command (bcl)
- Fix pre-install script execution (bcl)
- test pre-install kickstart section (bcl)
- Use sys.exit() instead of the exit() created by site.py. (dshea)
- Call ipmi_report before sys.exit (dshea)
- Add a test for proxy authentication (dshea)
- Add optional authentication to the proxy server (dshea)
- Add more tests to proxy-kickstart (dshea)
- Show an alternative prompt if a hub contains only a single spoke (#1199234)
  (mkolman)
- Add few docs and improvement in check_ip_address (jkonecny)
- Check whether files actually contain translatable strings. (dshea)
- Add specific error string to TUI user dialog (#1248421) (bcl)
- Make EditTUIDialog error generic (#1248421) (bcl)
- Fix and expand nfs-repo-and-addon.ks (dshea)
- Added a script to make the packages used by nfs-repo-and-addon (dshea)
- Implement the rest of the repo options in dnfpayload. (dshea)
- Fix kickstart test for bond interface creation (jkonecny)

* Fri Jul 31 2015 Brian C. Lane <bcl@redhat.com> - 23.18-1
- Move the proxy server script into a common file. (dshea)
- Use python3 for the proxy server and remove python2 compatibility (dshea)
- makePickle now needs to return bytes (bcl)
- gi.require_version raises ValueError (bcl)
- Remove duplicate signal setup block (bcl)
- Fix three bugs discovered by driverdisk-disk.ks (clumens)
- Fix error with OEMDRV ks auto-load check. (#1057271) (sbueno+anaconda)
- Make sure TUI is readable for non-latin languages (#1182562) (mkolman)
- Equalize capacity & mount point entries (#1212615) (dshea)
- Disable GRUB os_prober on POWER (#1193281) (rmarshall)
- Cancel Container Edit Sensitizes Update (#1168656) (rmarshall)
- Fix SoftwareSpoke._kickstarted. (dshea)
- Disable a Pylint false-positive (#1234896) (mkolman)
- Add support for autostep and --autoscreenshot (#1234896) (mkolman)
- Escape \'s in doc strings (dshea)
- Ellipsize the file system type combo box (#1212615) (dshea)
- Add graphviz to make-sphinx-doc script (jkonecny)
- Remove many of a documentation compilation errors (jkonecny)
- Add class diagrams to existing spokes and hubs (jkonecny)
- Add class diagram settings to documentation (jkonecny)
- Fix the UnusuableConfigurationError dialog (#1246915) (dshea)
- Chase pygobject's stupid moving target (dshea)
- Add missing translation contexts (dshea)
- Actually translate the container type labels (dshea)
- Check whether a translated string requires a context or comment. (dshea)
- Clean up the temporary pools virt-install makes. (clumens)
- Return the same object for repeated calls to __get__ (#1245423) (dshea)
- Use sys.exit instead of os._exit. (clumens)
- Add parentheses around the IPV6 regex fragment. (dshea)
- Add tests for IPv6 literals in URLs (dshea)
- Modify Installation Source Proxy Label (#11688554) (rmarshall)

* Fri Jul 24 2015 Brian C. Lane <bcl@redhat.com> - 23.17-1
- Fix Initial PPC PReP Boot Selector Name (#1172755) (rmarshall)
- Require a newer version of pykickstart (vpodzime)
- Use dictionaries is thread-safe manner. (dshea)
- Merge pull request #234 from wgwoods/master (wwoods)
- Auto-load ks.cfg if OEMDRV volume available. (#1057271) (sbueno+anaconda)
- Check the encrypt checkbox when encrypted specified in KS (vtrefny)
- Do not raise KickstartValueError for missing passphrase (vtrefny)
- Ask for encryption passphrase when not specified in ks (#1213096) (vtrefny)
- dracut: minor cleanup (wwoods)
- dracut: fix missing messages for inst.ks=cdrom (wwoods)
- Wait forever for kickstarts on CDROM (#1168902) (wwoods)
- Use abs_builddir instead of builddir so paths will look more reasonable.
  (clumens)
- Add a new makefile target that does everything needed for jenkins. (clumens)
- Merge pull request #228 from AdamWill/logind (dshea)
- Fix crash when mirrorlist checkbox is checked (jkonecny)
- Fix crash when user start typing proxy credentials (jkonecny)
- Check repository URL before leaving Source Spoke (jkonecny)
- Add IDs to identify addon repositories (jkonecny)
- Repositories can be checked without a selection (jkonecny)
- Consolidate the language environment variables. (dshea)
- Change the generated API indices slightly (dshea)
- Ignore "mountpoint" used a format specifier (dshea)
- filesystems -> file systems, per the style guide (dshea)
- Properly parameterize a translated string (dshea)
- Fix pylint errors in rescue.py. (dshea)
- Remove unused imports (dshea)
- Remove text.py from spec file (#965985) (sbueno+anaconda)
- Merge pull request #220 from AdamWill/1243962 (dshea)
- Fix adding 'boot=' option in FIPS mode (vtrefny)
- anaconda.target: Wants systemd-logind.service (#1222413) (awilliam)
- Remove the last usage of newt and get rid of it as a dependency (#965985)
  (sbueno+anaconda)
- Enable anaconda to use the new rescue mode. (#965985) (sbueno+anaconda)
- Get rid of unnecessary constants in constants_text. (#965985)
  (sbueno+anaconda)
- Get rid of some unnecessary files. (#965985) (sbueno+anaconda)
- Display verbose packaging errors to the user (bcl)
- Show source errors from refresh method (bcl)
- Fix the validate functions in the btrfs kickstart_tests. (clumens)
- Connect kickstart lang data to dnf-langpacks (#1051816) (dshea)
- Add simple_replace config file function (bcl)
- Remove some vestiges of the old packaging module (dshea)
- Remove window boot block detection functions. (dshea)
- Remove iutil.xprogressive_delay. (dshea)
- Simplify iutil.mkdirChain. (dshea)
- Decode wifi SSIDs into strings. (#1240398) (dshea)
- Actually use the temp directory so test files get cleaned up (dshea)
- Disable the output from rpmbuild (dshea)
- Remove stray references to python2. (dshea)
- Fix possible to start installation without network (#1221109) (jkonecny)
- Fix 'q' (to quit) do not work in TUI hub (jkonecny)
- act on the right objects when stripping URL protocols (#1243962) (awilliam)
- Fix 'App' object has no attribute 'queue' (#1243316) (jkonecny)

* Thu Jul 16 2015 Brian C. Lane <bcl@redhat.com> - 23.16-1
- fix storage writing for live and ostree installs (#1236937) (awilliam)
- Add O_CREAT to the open flags when extracting rpm files. (dshea)
- Move ostree gobject version check next to the import (#1243543) (bcl)
- Remove rpmfluff from the buildrequires. (dshea)
- Only import readline if readline is necessary. (dshea)
- use the right baseurl in run_install_test.sh. (clumens)
- Don't copy the environment when starting metacity. (dshea)
- Fix the use of a temporary file in SimpleConfig.write (dshea)
- Add a test for SimpleConfig.write(use_tmp=True). (dshea)
- Remove an unnecessary chmod when creating chrony.conf (dshea)
- Fix some bad uses of chmod. (dshea)
- Add a function to open a file with specific permission bits (dshea)
- Don't ask to start vnc if user specifies text mode. (#1202277)
  (sbueno+anaconda)
- New Anaconda documentation - 23.15 (bcl)
- Add a helper for building Sphinx docs using mock. (bcl)
- Update Sphinx configuration for python3 (bcl)
- Running without a GUI can also raise ValueError in errors.py (bcl)
- parse-kickstart_test.py: fix driverdisk_test() (wwoods)
- Fix the spelling of "version" (dshea)

* Mon Jul 13 2015 Brian C. Lane <bcl@redhat.com> - 23.15-1
- Some dracut modules anaconda needs have been split into their own package.
  (clumens)
- User operation kickstart tests. (kvalek)
- Kickstart tests for UTC and LOCAL hwclock. (kvalek)
- Kickstart firewall tests. (kvalek)
- Fix Repository New_Repository has no mirror or baseurl (#1215963) (jkonecny)

* Fri Jul 10 2015 Brian C. Lane <bcl@redhat.com> - 23.14-1
- Catch blivet formatDevice ValueError in custom (#1240226) (bcl)
- There's now a python3-rpmfluff, so revert this. (clumens)
- Fix a couple other pylint problems in the driver disk tests. (clumens)
- Merge pull request #194 from wgwoods/master (wwoods)
- dracut: fix boot failure waiting for finished/dd.sh (wwoods)
- Use builddir instead of srcdir to find the dd utils (dshea)
- Fix the dd_test for python3. (dshea)
- Fix %%files to deal with compiled python3 modules (dshea)
- Add a bunch of gi.require_version calls (dshea)
- Temporarily disable the error about not importing rpmfluff. (clumens)
- Don't try to iterate over threads directly in wait_all. (clumens)
- Update the btrfs kickstart tests to use functions.sh. (clumens)
- Merge pull request #182 from wgwoods/dd-refactor (wwoods)
- driver_updates: fixes from patch review (wwoods)
- Don't be too picky about what name is --device=link (dshea)
- Ignore stderr output from parse-kickstart. (dshea)
- Add an option to execReadlines to filter out stderr. (dshea)
- Ignore interruptible system calls in the dd test (dshea)
- Fix an undefined variable in writeStorageLate (dshea)
- Connect zfcp entries to the discovery buttons (dshea)
- Connect iscsi activations to buttons (dshea)
- Connect the dasd number entry to the discovery buttons. (dshea)
- Add keyboard layouts on the row-activated signal. (dshea)
- Connect dialog inputs to default actions. (dshea)
- Remove unnecessary GtkNotebooks. (dshea)
- Re-save some dialog glade files. (dshea)
- Merge pull request #181 from wgwoods/master (wwoods)
- dd-refactor: dracut + build bits (wwoods)
- Add kickstart test for RAID1 (bcl)
- pass PYTHONPATH to the kickstart test framework (bcl)
- Write servers to chronyd.conf even if it's off (#1197575) (wwoods)
- Refresh advanced disks after disk summary dialog (#1226354) (bcl)
- parse-kickstart: just emit 'inst.dd=XXX' for driverdisk (wwoods)
- parse-kickstart: pylint fixes (wwoods)
- dd-refactor: new driver_updates.py + tests (wwoods)
- payload: fix driverdisk repos (wwoods)
- dracut: fix boot with inst.ks and no inst.{repo,stage2} (#1238987) (wwoods)
- Use the most recent versions of the btrfs, logvol, part, and raid commands.
  (clumens)
- Allow /boot partition on iscsi with ibft (#1164195) (jkonecny)
- Add kickstart tests to test btrfs installation (vtrefny)
- Fix broken test by infiniband patch (#1177032) (jkonecny)

* Thu Jul 02 2015 Brian C. Lane <bcl@redhat.com> - 23.13-1
- Add a switch for the Airplane Mode label (dshea)
- Connect labels with keyboard accelerators to a widget (dshea)
- Add a test for dangling keyboard accelerators. (dshea)
- Use pocketlint for translation and markup checking (dshea)
- Flatten the glade test directory. (dshea)
- Add support for specifying arbitrary mkfs options. (clumens)
- Fix kickstart install with infiniband (#1177032) (jkonecny)
- anaconda-dracut: Fix sysroot mount for netroot (#1232411) (bcl)
- Add RAID swaps to /etc/fstab (#1234469) (bcl)
- network: catch another race when calling dbus methods on invalid devices
  (rvykydal)
- network: GUI, add connection even when virtual device activation failed
  (#1179276) (rvykydal)
- Fix IP / hostname mismatches when showing VNC server address (#1186726)
  (rvykydal)
- Check also ipv6 default routes when looking for onboot=yes device (#1185280)
  (rvykydal)
- Merge pull request #157 from wgwoods/master_dd_fixes (wwoods)
- Do not check dependencies on invalid payloads (dshea)
- network: don't set onboot=False for default autoconnections (#1212009)
  (rvykydal)
- Fix the types used to write anaconda-tb-all.log (dshea)
- dd: drop unnecessary archive_read_data_skip (wwoods)
- dd_extract: -l should not extract modules+firmware (wwoods)
- dd: fix permissions on extracted files (#1222056) (wwoods)
- tests: add dd_tests (wwoods)

* Fri Jun 26 2015 Brian C. Lane <bcl@redhat.com> - 23.12-1
- Revert "Add an optional conditional to progress_report." (bcl)
- Fix inconsistencies in the payload messages. (dshea)
- Fix install-requires and install-buildrequires (dshea)
- anaconda-dracut: Mount /dev/mapper/live-rw (#1232411) (bcl)
- Eliminate some false test results when running glade tests. (atodorov)
- Move the knowledge about network packages into ksdata.network. (clumens)
- Add an optional conditional to progress_report. (clumens)
- Move the big block of late storage writing out of install.py. (clumens)
- The attribute is named ostreesetup.nogpg. (clumens)
- Use the index in grubenv (#1209678) (bcl)
- Do not raise an exception on EINTR from os.close or os.dup2 (dshea)
- Merge pull request #154 from mulkieran/master-959701 (mulkieran)
- Improve focus behavior in the advanced user dialog (dshea)
- Re-save advanced_user.glade (dshea)
- Depsolve kickstarted packages on the summary hub (#961280) (dshea)
- Add a kickstart test for %%packages --ignoremissing (dshea)
- Remove descriptions for RAID levels (#959701) (amulhern)
- No kexec-tools on aarch64 (bcl)

* Fri Jun 19 2015 Brian C. Lane <bcl@redhat.com> - 23.11-1
- Do not import iutil from flags (dshea)
- Ignore EINTR errors in files unlikely to encounter them (dshea)
- Reimplement the open override for the dracut scripts (dshea)
- Wrap the only non-open call found by the new pocketlint checks (dshea)
- Redefine open to retry on EINTR (dshea)
- Remove __future__ imports (dshea)
- Use python 3's OSError subclasses instead of checking errno (dshea)
- Allow kwargs in eintr_retry_call (dshea)
- Remove explicit uses of /dev/null (dshea)
- Do not retry calls to close or dup2 (dshea)
- Remove another function from isys (dshea)
- Make dialogs behave better with timed input validation (dshea)
- Fix the password/confirm checks to work with delayed validation (dshea)
- Move the URL protocol removal out of the input check (dshea)
- Remove the vestigal capslock label from the password spoke (dshea)
- Re-saved a few glade files (dshea)
- Run set_status unconditionally from update_check_status (dshea)
- Do not run input checks for every keystroke of input (#1206307) (dshea)
- Add a method to execute timed actions early (dshea)
- Use comps.environments instead of comps.environments_iter (#1221736) (dshea)
- Merge pull request #83 from mulkieran/master-requires (mulkieran)
- Only show supported autopart choices in choices combo. (amulhern)
- Strip out device types that blivet is not able to support. (amulhern)
- Update blivet required version. (amulhern)
- Fix nfs4 stage2 and repo handling (#1230329) (bcl)
- Update upd-kernel so that it actually works (#1166535) (bcl)
- Fix passing ,nfsvers=3 to dracut (#1161820) (bcl)
- Require the python3 version of iscsi-initiator-utils (dshea)
- Fix the pylint pre-commit hook for python3 and pocketlint (dshea)
- Fix a type check to work with python 3. (dshea)
- Do not log Xorg output to tty5 (dshea)

* Wed Jun 10 2015 Brian C. Lane <bcl@redhat.com> - 23.10-1
- Deal with encrypted partitions not being readable by virt-cat. (clumens)
- Make use of the restore_signals Popen argument (dshea)
- Don't allow /boot on iSCSI. (#1164195) (sbueno+anaconda)
- Merge pull request #127 from mulkieran/master-kickstart (mulkieran)
- Actually distribute the clickable message test, too (dshea)
- Fix disk argument passing to virt-cat in the ostree test. (clumens)
- Relabel all password and group files in %%post (#1228489) (dshea)
- Deal with the order of ifcfg files not being guaranteed. (clumens)
- Add a __init__.py to fix up an error when running iutil_test.py. (clumens)
- Actually run the clickable message test (dshea)
- Add a false positive to pylint checking for S390Error. (clumens)
- Let the excludedocs test pass if there are only directories left. (clumens)
- Allow successful kstest results to provide more details. (clumens)
- The escrow_cert test cannot use autopart. (clumens)
- Don't warn on PyInit__isys being unused. (clumens)
- Test that root LV is encrypted. (amulhern)
- Deal with subprocess returning bytes in tests/lib/filelist.py, too. (clumens)
- Make anaconda+python3+pocketlint work. (clumens)
- Start using our new shared pylint framework in anaconda. (clumens)
- Remove our extra pylint checkers. (clumens)
- Remove a duplicate libselinux-python3 requires. (clumens)
- Run makeupdates with Python 2 for now (mkolman)
- Don't use the _safechars private property (#1014220) (mkolman)
- Make sure directory size is returned as int (#1014220) (mkolman)
- Only warn about missing yum-utils (#1014220) (mkolman)
- Make sure set_system_time() gets an integer (#1014220) (mkolman)
- Make sure the column number in TUI is an integer (#1141242) (mkolman)
- Python 3 compatible sorting fixes (#1014220) (mkolman)
- Make version comparison Python 3 compatible (#1014220) (mkolman)
- Don't apply numeric comparison on None (#1141242) (mkolman)
- Avoid comparing None to an integer (#1141242) (mkolman)
- Handle urllib split (#1014220) (mkolman)
- Don't try to decode strings (#1014220) (mkolman)
- Rename function attributes (#1014220) (mkolman)
- Replace raw_input() with input() (#1014220) (mkolman)
- Make iterators and their usage Python 3 compatible (#1014220) (mkolman)
- Convert Python 2 metaclass magic to Python 3 metaclass magic (#1014220)
  (mkolman)
- Make the raise syntax Python 3 compatible (#1014220) (mkolman)
- Python 3 no longer does tuple parameter unpacking (#1014220) (mkolman)
- Make isys Python 3 compatible (#1014220) (mkolman)
- Set a correct mode for the tempfile (#1014220) (mkolman)
- Python 3 temp files no longer reflect external changes (#1014220) (mkolman)
- Make print usage Python 3 compatible (#1014220) (mkolman)
- Rename the warnings spoke to warnings_spoke (#1014220) (mkolman)
- Replace list comprehension with for at class level (mkolman)
- Make gettext usage Python 3 compatible (#1014220) (mkolman)
- Do not open tty5 for writing in the "a" mode (#1014220) (vpodzime)
- Do not use pykickstart's RepoData as a key in a dict (#1014220) (vpodzime)
- Do not run repo attrs' checks if they are not set up yet (#1014220)
  (vpodzime)
- Don't depend on side effects of map() (#1141242) (mkolman)
- Don't use exceptions' message attribute (#1014220) (vpodzime)
- Addapt to string type changes (#1014220) (mkolman)
- Handle modules returning bytes in Python 3 (#1014220) (mkolman)
- Add and use function that makes sure we work with strings (#1014220)
  (vpodzime)
- Handle modules requiring different string types in Python 3 (#1014220)
  (mkolman)
- Remove sitecustomize (#1014220) (mkolman)
- Make ASCII conversions Python compatible (#1014220) (mkolman)
- Remove "is Unicode" tests (#1014220) (mkolman)
- Fix ASCII conversion tests (#1014220) (mkolman)
- Return a string when calling a program (#1014220) (mkolman)
- Handle subprocess returning bytes (#1014220) (mkolman)
- Handle latin-1 strings in locale -a output (#1014220) (mkolman)
- Open the VNC password file for binary writing (#1014220) (mkolman)
- Update parse-kickstart for python3 (#1014220) (bcl)
- Update driver-updates for python3 (#1014220) (bcl)
- Update python-deps for python3 (#1014220) (bcl)
- Add a test for parse-kickstart (#1014220) (bcl)
- Make the import Python 3 compatible (#1014220) (mkolman)
- Change configparser and queue imports (#1014220) (mkolman)
- Remove imports from the __future__ (#1014220) (mkolman)
- Use the imp module directly (#1014220) (mkolman)
- Use Python 3 versions of Python dependencies  (#1014220) (mkolman)
- Use /usr/bin/python3 in scripts (#1014220) (mkolman)
- Use Python 3 versions of nose and Pylint (#1014220) (mkolman)
- Build the Anaconda widgets for Python 3 (#1014220) (mkolman)
- Update makebumpver for python3 (#1014220) (bcl)
- Fix Kickstart installation without default gateway errors out (jkonecny)
- Fix results checking in a couple ks tests. (clumens)

* Wed Jun 03 2015 Brian C. Lane <bcl@redhat.com> - 23.9-1
- Fix a usage typo in run_once_ks script. (sbueno+anaconda)
- Add kickstart tests for keyboard settings. (sbueno+anaconda)
- Add a kickstart test for lang settings. (sbueno+anaconda)
- Fix a %% call inside _(). (clumens)
- Convert ntp-pools.* to using the new kstest functions and autopart. (clumens)
- Fix up the expected output in parse-kickstart_test.py. (clumens)
- Fix a couple more pylint problems in the s390 code. (clumens)
- Use the adapted Timezone class for kickstart data (vpodzime)
- Add a kickstart test for processing NTP servers/pools configuration
  (vpodzime)
- Show error on invalid username attempts in TUI. (#1171778) (sbueno+anaconda)
- Fix dracut reads ksdevice from missing os enviromnent (jkonecny)
- Run kickstart tests through an LMC-like program, not LMC itself. (clumens)
- Move common kickstart_test code out into its own functions.sh file. (clumens)
- Switch to using autopart in the kickstart tests. (clumens)
- Fix a couple pylint errors. (sbueno+anaconda)
- Make anaconda changes necessary for libblockdev s390 plugin.
  (sbueno+anaconda)
- Add a kickstart test for lvm with percentage-based sizes. (dlehman)
- Add kickstart test for basic fixed-size lvm layout. (dlehman)
- Add a kickstart test to validate the default fstype. (dlehman)
- Add kickstart test to test bond interface creation (jkonecny)
- Add kickstart test to test vlan creation (jkonecny)
- Fix --device=link and --device not specified (#1085310) (rvykydal)
- Add kickstart test to test hostname (jkonecny)
- Add a /boot to tmpfs-fixed_size.ks. (clumens)
- Fix bad warning message when user set illegal IP (jkonecny)
- Fix bad check of illegal ip address (jkonecny)
- Add a simple tmpfs kickstart test (mkolman)
- Add a kickstart test for escrow packets and backup passphrases (dshea)
- Fix a typo that caused us to discard corrected target sizes. (#1211746)
  (dlehman)
- Don't pass anything to ./configure. (dshea)
- Fix a pylint problem in parse-kickstart_test.py. (clumens)
- Fix 0 choice in Language and Storage in TUI mode (jkonecny)
- Update html documentation for new boot-options section (bcl)
- Convert boot-options to ReST and include it in the Sphinx documents. (bcl)

* Fri May 15 2015 Brian C. Lane <bcl@redhat.com> - 23.8-1
- Clean up after processKickstart in parse-kickstart_test.py. (clumens)
- Add support to dnfpayload.py for addon NFS repos. (clumens)
- Fix IndexError: list index out of range (#1219004) (jkonecny)
- Fix a typo in proxy-kickstart.sh that was causing a test time out. (clumens)
- iSCSI Name Validation using regexes (sujith_pandel)
- Add kickstart tests for proxy usage. (dshea)
- In dracut, do not display a warning for network lines with just a hostname.
  (clumens)
- Add transport adapters to support ftp and file fetching (dshea)
- Fix for "Kickstart installation fails..." (#1197960) (jkonecny)
- Allow passing kickstart tests to be run on the command line. (clumens)
- Automatically collect environment variables to be passed to ks tests.
  (clumens)
- Use isinstance instead of type for doing type checks. (clumens)
- Remove yumpayload.py, its support files, and most references to yum.
  (clumens)
- Fix the packages-and-group wildcard exclusion test (dshea)
- Set the GUI-selected environment in the ksdata (#1192100) (dshea)
- Don't crash if the disk model is None (#1215251) (dshea)
- Correct an error message in packages-and-groups-1.ks. (clumens)
- Switch from testing for emacs* to kacst*. (clumens)
- Tests that end in a traceback are failures, not successes. (clumens)
- Don't run run_report.sh from within run_kickstart_tests.sh. (clumens)
- If a kickstart test failed due to a traceback, display that. (clumens)
- Wrap device labels earlier (#1212586) (dshea)
- Remove the angle property from the device label (dshea)
- Get rid of the find button in the filter spoke. (dshea)
- Rearrange filter.glade (dshea)
- Fix errors in the vendor column renderers. (dshea)
- Fix some minor inconsistencies in filter.glade (dshea)
- Fix issues with advanced storage searching. (dshea)
- Remove duplicate entries from search combo boxes (dshea)
- Use named IDs for the filter type combo boxes. (dshea)
- Rearrange filter.glade the way glade wants it now (dshea)
- Add a reporting support script to kickstart tests. (clumens)
- Return a specific error code when a test times out. (clumens)
- Fix indentation in run_one_ks.sh. (clumens)
- Also remove all the fonts in the packages-and-groups-1 test. (clumens)
- Enable the basic-ftp and basic-ftp-yum kickstart tests. (clumens)
- Fix a typo in groups-and-envs-2.ks (clumens)
- Get NTP pools and servers from ksdata for the runtime config (vpodzime)
- Adapt to the new argument list for save_servers_to_config. (clumens)
- Remove the restriction that /boot be below 2TB for grub (#1082331) (dshea)
- Distinguish between NTP pools and servers in GUI (vpodzime)
- Add support for chrony pool directive (mlichvar)
- Add a readme pointing to the documentation (bcl)
- Sphinx docs - use source order (bcl)
- Add html documentation for Anaconda v23.7 (bcl)
- Place html docs under ./docs/html/ (bcl)
- Configure proxy settings for dnf payload (#1211122) (bcl)
- Change online action to change (bcl)
- Check for images/install.img first for netboot (bcl)
- Ignore addon and anaconda sections in handle-sshpw (bcl)
- Ignore %%anaconda section in parse-kickstart (bcl)
- Change of label in iscsi storage spoke (jkonecny)

* Wed Apr 22 2015 Brian C. Lane <bcl@redhat.com> - 23.7-1
- Fix doReqPartition import from autopart (bcl)
- Add support for reboot --kexec kickstart command (bcl)
- Add inst.kexec and --kexec support to reboot with kexec (bcl)
- Add setup_kexec method to prepare the system for a reboot with kexec (bcl)
- Add kickstart %%pre-install section support (bcl)
- Remove the custom help button from the toolbar (bcl)
- Use multiple streams for zRAM instead of multiple devices (vpodzime)
- iscsi: pass rd.* options of devices to be mouted in dracut (#1192398)
  (rvykydal)
- Remove the unused productName import from custom_storage_helpers.py.
  (clumens)
- Remove the old custom partitioning help dialog (mkolman)
- Implement the new reqpart command. (clumens)
- Sort disks by name when checking disk selection (vpodzime)
- Set both .format's and .originalFormat's passphrase on unlock (vpodzime)
- Make the Encrypt checkbox insensitive for encrypted non-BTRFS devices
  (#1210254) (vpodzime)
- Check for Gtk before importing escape_markup (bcl)
- If the network is disabled, also disable the network part of the source
  spoke. (#1192104) (clumens)
- Add handling for unusable storage configurations. (dlehman)
- Allow markup in the label/message of DetailedErrorDialog. (dlehman)
- Allow passing an optional button list to showDetailedError. (dlehman)
- Allow kwargs with gtk_action_wait, gtk_action_nowait decorators. (dlehman)
- Fix makeupdates handling of Release: (bcl)
- Make sure we unmount the path we mounted (bcl)
- Fix up one more back_clicked reference that got missed. (clumens)
- Don't unconditionally set ksdata.lang.seen to True (#1209927) (mkolman)
- Reset the back_clicked flag if we stay on the Storage spoke (#1210003)
  (vpodzime)
- Mark the back_clicked attribute of the Storage spoke as private (vpodzime)
- TUI pwpolicy setup was supposed to be in __init__ not refresh (#1208607)
  (bcl)
- Preserve the order of boot args added by kickstart. (clumens)
- Revert "allow /boot on btrfs subvol or filesystem" (bcl)
- Connect scroll adjustments in the right class (#1206472) (dshea)

* Thu Apr 02 2015 Brian C. Lane <bcl@redhat.com> - 23.6-1
- Enforce sane disk selections. (dlehman)
- Add a test for parse-kickstart (bcl)
- Add --tmpdir to parse-kickstart for testing (bcl)
- Use the correct format for IPMI messages. (clumens)
- Do not use min_luks_entropy with pre-existing devices (#1206101) (dshea)
- Remove the dnf cache directory when resetting the repo (dshea)
- Do not add separators to the addon list when not needed (dshea)
- Only use the instclass environment if it actually exists. (dshea)

* Fri Mar 27 2015 Brian C. Lane <bcl@redhat.com> - 23.5-1
- Mock external module dependencies for readthedocs (bcl)
- Generate the pyanaconda module documentation (bcl)
- Reformat kickstart.rst using better ReST markup (bcl)
- Add some deprecation-related false positives. (clumens)
- Add Sphinx documentation support (bcl)
- Add documentation on %%anaconda kickstart command (bcl)
- Prevent Storage spoke Done button method from multiple launch (jkonecny)
- Prevent spokes from being exited more times. (jkonecny)
- Only depend on pygobject3-base in anaconda-core (#1204469) (mkolman)
- Use proxy when configured for the base repo (#1196953) (sjenning)
- Assume UTC if setting the system time without a timezone (#1200444) (dshea)
- Add boolean as return to ThreadManager.wait (jkonecny)
- Make sure LANG is always set to something (#1201896) (dshea)
- Fix pylint/translation issues from the pwpolicy patches. (clumens)

* Fri Mar 20 2015 Brian C. Lane <bcl@redhat.com> - 23.4-1
- Clean out the mock chroot before attempting to run the rest of the test.
  (clumens)
- Implement %%anaconda kickstart section for pwpolicy (bcl)
- Add pwpolicy support to TUI interface (bcl)
- Add pwpolicy for the LUKS passphrase dialog. (bcl)
- Add pwpolicy for the user spoke. (bcl)
- Use pwpolicy for the root password spoke. (bcl)
- Add the text for weak passwords to constants (bcl)
- Add tests with an FTP instrepo (dshea)
- Add kickstart tests for an NFS instrepo and addon repos. (dshea)
- Handle /boot on btrfs for live (#1200539) (bcl)
- rpmostreepayload: write storage config after shared var is mounted (#1203234)
  (rvykydal)
- Tweak tmux configuration file (jkonecny)
- Remove --device= from the new kickstart tests. (clumens)
- Add more kickstart-based packaging tests. (clumens)
- Fix enlightbox call in ZFCPDialog. (#1151144) (sbueno+anaconda)
- fix crash with bare 'inst.virtiolog' in boot args (wwoods)
- Do not attempt to set None as a warning (dshea)
- fix inst.ks.sendmac for static ip=XXX (#826657) (wwoods)

* Fri Mar 13 2015 Brian C. Lane <bcl@redhat.com> - 23.3-1
- Only insert strings into the environment (#1201411) (dshea)
- Fix the rescue kernel version list in writeBootLoader (#1201429) (dshea)
- Missing local variable check (omerusta)
- Fix the handling of nfs:// URLs. (dshea)
- Add glob support for the -a/--add option in makeupdates (mkolman)
- White Space fixes (omerusta)
- Put all mock results into the top-level source dir. (clumens)
- Merge pull request #31 from dcantrell/master (david.l.cantrell)
- Require newt-python in anaconda-core (dshea)
- Make merge-pr executable (dshea)
- Display an error for exceptions during GUI setup (dshea)
- Remove unused invisible char properties (dshea)
- Add a check for invisible_char validity (dshea)
- Connect viewport adjustments to child focus adjustments (#1192155) (dshea)
- Support '%%packages --multilib' in dnfpayload.py (#1192628) (dcantrell)

* Fri Mar 06 2015 Brian C. Lane <bcl@redhat.com> - 23.2-1
- Add rc-release target (bcl)
- Change --skip-tx to --skip-zanata in scratch-bumpver (bcl)
- Add --newrelease to makebumpver (bcl)
- Improve the addon repo name collision code (#1125322) (bcl)
- Fix the import of mountExistingSystem (vpodzime)
- Fix import error in anaconda-cleanup. (sbueno+anaconda)
- Use the new static method to get possible PE sizes (vpodzime)
- Try using the global LUKS passphrase if none is given for LV/part (#1196112)
  (vpodzime)
- Fix the help button mnemonic display on spokes (dshea)
- Only set the hub message if the message has changed (dshea)
- Wrap the info bar in a GtkRevealer (dshea)
- Add links to clickable warning and error messages. (dshea)
- Add a test to look for clickable messages that aren't clickable enough.
  (dshea)
- Increment the widgets version number (dshea)
- Allow markup and links in the info bar. (dshea)
- Add more links to gtk-doc comments (dshea)
- Handle New_Repository name collision source spoke (#1125322) (bcl)
- Fix a bad usage of execWithRedirect (#1197290) (dshea)
- Have to be root to delete /var/tmp/kstest-* on the remote machines. (clumens)
- Use the LUKS device for swap in fstab (#1196200) (vpodzime)
- Clear TUI source spoke errors that may have been leftover from a prior
  attempt. (#1192259) (sbueno+anaconda)

* Fri Feb 27 2015 Brian C. Lane <bcl@redhat.com> - 23.1-1
- Make sure python2 dnf is required (bcl)
- Fix pykickstart requirement. (clumens)
- Extract xattrs from tar payload (#1195462) (bcl)
- Add a script to rebase and merge pull requests (dshea)
- Update translation documentation for Zanata (bcl)
- Switch translation support to fedora.zanata.org (bcl)
- install.py: fix the 'is team device' check (awilliam)
- Explain why Anaconda requires rpm-devel and libarchive-devel during build
  (mkolman)
- Revert "Switch to temporary transifex branch" (bcl)
- Revert "makebumpver needs to know about anaconda-1 transifex name" (bcl)
- Commit 23.0 anaconda.pot file (bcl)
- Rename queue.py to queuefactory.py. (clumens)
- Remove references to old_tests, which no longer exists. (clumens)
- Fix package and group removing with the dnf payload. (clumens)
- Don't try to run new-kernel-pkg if it doesn't exist. (clumens)

* Fri Feb 20 2015 Brian C. Lane <bcl@redhat.com> - 23.0-1
- Remove unused imports (dshea)
- Check for unused imports in __init__ files (dshea)
- Remove timestamp-based version support. (dshea)
- Add test lib methods to check regexes (dshea)
- Cleanup BuildRequires (mkolman)
- Remove obsolete imports. (amulhern)
- Make print statement print output w/out surrounding parentheses. (amulhern)
- Remove an unused import (dshea)
- rpmostreepayload: Honor noverifyssl (walters)
- typo: packaging: Don't vary name of "verified" (walters)
- Disable the metacity mouse-button-modifier setting (dshea)
- Fix completion setting in TUI language spoke. (#1192230) (sbueno+anaconda)
- Remove the pylint false positives for the GLib module (dshea)
- Use ExtendAction for --ignore flag (amulhern)
- Use a simple ExtendAction for add_rpms option. (amulhern)
- Fix log message formating (mkolman)
- Don't clear nonexistent DNF package download location (#1193121) (mkolman)
