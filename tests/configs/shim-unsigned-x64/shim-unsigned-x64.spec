%global pesign_vre 0.106-1
%global gnuefi_vre 1:3.0.5-6
%global openssl_vre 1.0.2j

%global debug_package %{nil}
%global __debug_package 1
%global _binaries_in_noarch_packages_terminate_build 0
%global __debug_install_post %{SOURCE100} x64 ia32
%undefine _debuginfo_subpackages

%global efidir %(eval echo $(grep ^ID= /etc/os-release | sed -e 's/^ID=//' -e 's/rhel/redhat/'))
%global shimrootdir %{_datadir}/shim/
%global shimversiondir %{shimrootdir}/%{version}-%{release}
%global efiarch x64
%global shimdir %{shimversiondir}/%{efiarch}
%global efialtarch ia32
%global shimaltdir %{shimversiondir}/%{efialtarch}

Name:		shim-unsigned-%{efiarch}
Version:	15.8
Release:	2.el8
Summary:	First-stage UEFI bootloader
ExclusiveArch:	x86_64
License:	BSD
URL:		https://github.com/rhboot/shim
Source0:	https://github.com/rhboot/shim/releases/download/%{version}/shim-%{version}.tar.bz2
Source1:	redhatsecurebootca5.cer
# currently here's what's in our dbx:
# nothing.
Source2:	dbx.esl
Source3:	sbat.redhat.csv
Source4:	shim.patches

Source100:	shim-find-debuginfo.sh

%include %{SOURCE4}

BuildRequires:	gcc make
BuildRequires:	elfutils-libelf-devel
BuildRequires:	git openssl-devel openssl
BuildRequires:	pesign >= %{pesign_vre}
BuildRequires:	dos2unix findutils

# Shim uses OpenSSL, but cannot use the system copy as the UEFI ABI is not
# compatible with SysV (there's no red zone under UEFI) and there isn't a
# POSIX-style C library.
# BuildRequires:	OpenSSL
Provides:	bundled(openssl) = %{openssl_vre}

%global desc \
Initial UEFI bootloader that handles chaining to a trusted full \
bootloader under secure boot environments.
%global debug_desc \
This package provides debug information for package %{expand:%%{name}} \
Debug information is useful when developing applications that \
use this package or when debugging this package.

%description
%desc

%package -n shim-unsigned-%{efialtarch}
Summary:	First-stage UEFI bootloader (unsigned data)
Provides:	bundled(openssl) = %{openssl_vre}

%description -n shim-unsigned-%{efialtarch}
%desc

%package debuginfo
Summary:	Debug information for shim-unsigned-%{efiarch}
Requires:	%{name}-debugsource = %{version}-%{release}
Group:		Development/Debug
AutoReqProv:	0
BuildArch:	noarch

%description debuginfo
%debug_desc

%package -n shim-unsigned-%{efialtarch}-debuginfo
Summary:	Debug information for shim-unsigned-%{efialtarch}
Group:		Development/Debug
Requires:	%{name}-debugsource = %{version}-%{release}
AutoReqProv:	0
BuildArch:	noarch

%description -n shim-unsigned-%{efialtarch}-debuginfo
%debug_desc

%package debugsource
Summary:	Debug Source for shim-unsigned
Group:		Development/Debug
AutoReqProv:	0
BuildArch:	noarch

%description debugsource
%debug_desc

%prep
%autosetup -S git_am -n shim-%{version}
git config --unset user.email
git config --unset user.name
mkdir build-%{efiarch}
mkdir build-%{efialtarch}
cp %{SOURCE3} data/

%build
COMMIT_ID=5914984a1ffeab841f482c791426d7ca9935a5e6
MAKEFLAGS="TOPDIR=.. -f ../Makefile COMMIT_ID=${COMMIT_ID} "
MAKEFLAGS+="EFIDIR=%{efidir} PKGNAME=shim RELEASE=%{release} "
MAKEFLAGS+="ENABLE_SHIM_HASH=true "
MAKEFLAGS+="SBAT_AUTOMATIC_DATE=2023012900 "
MAKEFLAGS+="%{_smp_mflags}"
if [ -s "%{SOURCE1}" ]; then
	MAKEFLAGS="$MAKEFLAGS VENDOR_CERT_FILE=%{SOURCE1} "
fi
if [ -s "%{SOURCE2}" ]; then
	MAKEFLAGS="$MAKEFLAGS VENDOR_DBX_FILE=%{SOURCE2} "
fi

cd build-%{efiarch}
make ${MAKEFLAGS} \
	DEFAULT_LOADER='\\\\grub%{efiarch}.efi' \
	all
cd ..

cd build-%{efialtarch}
setarch linux32 -B make ${MAKEFLAGS} ARCH=%{efialtarch} \
	DEFAULT_LOADER='\\\\grub%{efialtarch}.efi' \
	all
cd ..

%install
COMMIT_ID=5914984a1ffeab841f482c791426d7ca9935a5e6
MAKEFLAGS="TOPDIR=.. -f ../Makefile COMMIT_ID=${COMMIT_ID} "
MAKEFLAGS+="EFIDIR=%{efidir} PKGNAME=shim RELEASE=%{release} "
MAKEFLAGS+="ENABLE_HTTPBOOT=true ENABLE_SHIM_HASH=true "
MAKEFLAGS+="SBAT_AUTOMATIC_DATE=2023012900 "
if [ -s "%{SOURCE1}" ]; then
	MAKEFLAGS="$MAKEFLAGS VENDOR_CERT_FILE=%{SOURCE1} "
fi
if [ -s "%{SOURCE2}" ]; then
	MAKEFLAGS="$MAKEFLAGS VENDOR_DBX_FILE=%{SOURCE2} "
fi

cd build-%{efiarch}
make ${MAKEFLAGS} \
	DEFAULT_LOADER='\\\\grub%{efiarch}.efi' \
	DESTDIR=${RPM_BUILD_ROOT} \
	install-as-data install-debuginfo install-debugsource
cd ..

cd build-%{efialtarch}
setarch linux32 make ${MAKEFLAGS} ARCH=%{efialtarch} \
	DEFAULT_LOADER='\\\\grub%{efialtarch}.efi' \
	DESTDIR=${RPM_BUILD_ROOT} \
	install-as-data install-debuginfo install-debugsource
cd ..

%files
%license COPYRIGHT
%dir %{shimrootdir}
%dir %{shimversiondir}
%dir %{shimdir}
%{shimdir}/*.CSV
%{shimdir}/*.efi
%{shimdir}/*.hash

%files -n shim-unsigned-%{efialtarch}
%license COPYRIGHT
%dir %{shimrootdir}
%dir %{shimversiondir}
%dir %{shimaltdir}
%{shimaltdir}/*.CSV
%{shimaltdir}/*.efi
%{shimaltdir}/*.hash

%files debuginfo -f build-%{efiarch}/debugfiles.list

%files -n shim-unsigned-%{efialtarch}-debuginfo -f build-%{efialtarch}/debugfiles.list

%files debugsource -f build-%{efiarch}/debugsource.list

%changelog
* Wed Feb 07 2024 Peter Jones <pjones@redhat.com> - 15.8-2.el8
- Rebuild to fix the commit ident and MAKEFLAGS
  Resolves: RHEL-11259

* Tue Dec 05 2023 Peter Jones <pjones@redhat.com> - 15.8-1.el8
- Update to shim-15.8 for CVE-2023-40547
  Resolves: RHEL-11259

* Wed Jun 01 2022 Peter Jones <pjones@redhat.com> - 15.6-1.el8
- Update to shim-15.6
  Resolves: CVE-2022-28737

* Thu Sep 17 2020 Peter Jones <pjones@redhat.com> - 15-9.el8
- Fix an incorrect allocation size.
  Related: rhbz#1877253

* Thu Jul 30 2020 Peter Jones <pjones@redhat.com> - 15-8
- Fix a load-address-dependent forever loop.
  Resolves: rhbz#1861977
  Related: CVE-2020-10713
  Related: CVE-2020-14308
  Related: CVE-2020-14309
  Related: CVE-2020-14310
  Related: CVE-2020-14311
  Related: CVE-2020-15705
  Related: CVE-2020-15706
  Related: CVE-2020-15707

* Sat Jul 25 2020 Peter Jones <pjones@redhat.com> - 15-7
- Implement Lenny's workaround
  Related: CVE-2020-10713
  Related: CVE-2020-14308
  Related: CVE-2020-14309
  Related: CVE-2020-14310
  Related: CVE-2020-14311

* Fri Jul 24 2020 Peter Jones <pjones@redhat.com> - 15-5
- Once more with the MokListRT config table patch added.
  Related: CVE-2020-10713
  Related: CVE-2020-14308
  Related: CVE-2020-14309
  Related: CVE-2020-14310
  Related: CVE-2020-14311

* Thu Jul 23 2020 Peter Jones <pjones@redhat.com> - 15-4
- Rebuild for bug fixes and new signing keys
  Related: CVE-2020-10713
  Related: CVE-2020-14308
  Related: CVE-2020-14309
  Related: CVE-2020-14310
  Related: CVE-2020-14311

* Wed Jun 05 2019 Javier Martinez Canillas <javierm@redhat.com> - 15-3
- Make EFI variable copying fatal only on secureboot enabled systems
  Resolves: rhbz#1715878
- Fix booting shim from an EFI shell using a relative path
  Resolves: rhbz#1717064

* Tue Feb 12 2019 Peter Jones <pjones@redhat.com> - 15-2
- Fix MoK mirroring issue which breaks kdump without intervention
  Related: rhbz#1668966

* Fri Jul 20 2018 Peter Jones <pjones@redhat.com> - 15-1
- Update to shim 15

* Tue Sep 19 2017 Peter Jones <pjones@redhat.com> - 13-3
- Actually update to the *real* 13 final.
  Related: rhbz#1489604

* Thu Aug 31 2017 Peter Jones <pjones@redhat.com> - 13-2
- Actually update to 13 final.

* Fri Aug 18 2017 Peter Jones <pjones@redhat.com> - 13-1
- Make a new shim-unsigned-x64 package like the shim-unsigned-aarch64 one.
- This will (eventually) supersede what's in the "shim" package so we can
  make "shim" hold the signed one, which will confuse fewer people.
