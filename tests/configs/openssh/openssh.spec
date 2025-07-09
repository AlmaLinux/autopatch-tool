# Do we want SELinux & Audit
%if 0%{?!noselinux:1}
%global WITH_SELINUX 1
%else
%global WITH_SELINUX 0
%endif

%global _hardened_build 1

# Do we want to disable building of gnome-askpass? (1=yes 0=no)
%global no_gnome_askpass 0

# Do we want to link against a static libcrypto? (1=yes 0=no)
%global static_libcrypto 0

# Use GTK2 instead of GNOME in gnome-ssh-askpass
%global gtk2 1

# Build position-independent executables (requires toolchain support)?
%global pie 1

# Do we want kerberos5 support (1=yes 0=no)
%global kerberos5 1

# Do we want libedit support
%global libedit 1

# Whether to build pam_ssh_agent_auth
%if 0%{?!nopam:1}
%global pam_ssh_agent 1
%else
%global pam_ssh_agent 0
%endif

# Reserve options to override askpass settings with:
# rpm -ba|--rebuild --define 'skip_xxx 1'
%{?skip_gnome_askpass:%global no_gnome_askpass 1}

# Add option to build without GTK2 for older platforms with only GTK+.
# Red Hat Linux <= 7.2 and Red Hat Advanced Server 2.1 are examples.
# rpm -ba|--rebuild --define 'no_gtk2 1'
%{?no_gtk2:%global gtk2 0}

# Options for static OpenSSL link:
# rpm -ba|--rebuild --define "static_openssl 1"
%{?static_openssl:%global static_libcrypto 1}

# Do not forget to bump pam_ssh_agent_auth release if you rewind the main package release to 1
%global openssh_ver 8.7p1
%global openssh_rel 45
%global pam_ssh_agent_ver 0.10.4
%global pam_ssh_agent_rel 5

Summary: An open source implementation of SSH protocol version 2
Name: openssh
Version: %{openssh_ver}
Release: %{openssh_rel}%{?dist}
URL: http://www.openssh.com/portable.html
#URL1: https://github.com/jbeverly/pam_ssh_agent_auth/
Source0: ftp://ftp.openbsd.org/pub/OpenBSD/OpenSSH/portable/openssh-%{version}.tar.gz
Source1: ftp://ftp.openbsd.org/pub/OpenBSD/OpenSSH/portable/openssh-%{version}.tar.gz.asc
Source2: sshd.pam
Source3: gpgkey-736060BA.gpg
Source4: https://github.com/jbeverly/pam_ssh_agent_auth/archive/pam_ssh_agent_auth-%{pam_ssh_agent_ver}.tar.gz
Source5: pam_ssh_agent-rmheaders
Source6: ssh-keycat.pam
Source7: sshd.sysconfig
Source9: sshd@.service
Source10: sshd.socket
Source11: sshd.service
Source12: sshd-keygen@.service
Source13: sshd-keygen
Source15: sshd-keygen.target
Source16: ssh-agent.service
Source17: openssh-systemd-sysusers.conf
Source18: openssh-server-systemd-sysusers.conf

#https://bugzilla.mindrot.org/show_bug.cgi?id=2581
Patch100: openssh-6.7p1-coverity.patch

#https://bugzilla.mindrot.org/show_bug.cgi?id=1402
# https://bugzilla.redhat.com/show_bug.cgi?id=1171248
# record pfs= field in CRYPTO_SESSION audit event
Patch200: openssh-7.6p1-audit.patch
# Audit race condition in forked child (#1310684)
Patch201: openssh-7.1p2-audit-race-condition.patch
# Correctly audit hostname and IP address
Patch202: openssh-8.7p1-audit-hostname.patch

# --- pam_ssh-agent ---
# make it build reusing the openssh sources
Patch300: pam_ssh_agent_auth-0.9.3-build.patch
# check return value of seteuid()
# https://sourceforge.net/p/pamsshagentauth/bugs/23/
Patch301: pam_ssh_agent_auth-0.10.3-seteuid.patch
# explicitly make pam callbacks visible
Patch302: pam_ssh_agent_auth-0.9.2-visibility.patch
# update to current version of agent structure
Patch305: pam_ssh_agent_auth-0.9.3-agent_structure.patch
# remove prefixes to be able to build against current openssh library
Patch306: pam_ssh_agent_auth-0.10.2-compat.patch
# Fix NULL dereference from getpwuid() return value
# https://sourceforge.net/p/pamsshagentauth/bugs/22/
Patch307: pam_ssh_agent_auth-0.10.2-dereference.patch
# https://bugzilla.redhat.com/show_bug.cgi?id=2070113
Patch308: pam_ssh_agent_auth-0.10.4-rsasha2.patch

#https://bugzilla.mindrot.org/show_bug.cgi?id=1641 (WONTFIX)
Patch400: openssh-7.8p1-role-mls.patch
#https://bugzilla.redhat.com/show_bug.cgi?id=781634
Patch404: openssh-6.6p1-privsep-selinux.patch
#?
Patch502: openssh-6.6p1-keycat.patch

#https://bugzilla.mindrot.org/show_bug.cgi?id=1644
Patch601: openssh-6.6p1-allow-ip-opts.patch
#https://bugzilla.mindrot.org/show_bug.cgi?id=1893 (WONTFIX)
Patch604: openssh-6.6p1-keyperm.patch
#(drop?) https://bugzilla.mindrot.org/show_bug.cgi?id=1925
Patch606: openssh-5.9p1-ipv6man.patch
#?
Patch607: openssh-5.8p2-sigpipe.patch
#https://bugzilla.mindrot.org/show_bug.cgi?id=1789
Patch609: openssh-7.2p2-x11.patch

#?
Patch700: openssh-7.7p1-fips.patch
#?
Patch702: openssh-5.1p1-askpass-progress.patch
#https://bugzilla.redhat.com/show_bug.cgi?id=198332
Patch703: openssh-4.3p2-askpass-grab-info.patch
#https://bugzilla.mindrot.org/show_bug.cgi?id=1635 (WONTFIX)
Patch707: openssh-7.7p1-redhat.patch
# warn users for unsupported UsePAM=no (#757545)
Patch711: openssh-7.8p1-UsePAM-warning.patch
# make aes-ctr ciphers use EVP engines such as AES-NI from OpenSSL
Patch712: openssh-6.3p1-ctr-evp-fast.patch

# GSSAPI Key Exchange (RFC 4462 + RFC 8732)
# from https://github.com/openssh-gsskex/openssh-gsskex/tree/fedora/master
Patch800: openssh-8.0p1-gssapi-keyex.patch
#http://www.mail-archive.com/kerberos@mit.edu/msg17591.html
Patch801: openssh-6.6p1-force_krb.patch
# add new option GSSAPIEnablek5users and disable using ~/.k5users by default (#1169843)
# CVE-2014-9278
Patch802: openssh-6.6p1-GSSAPIEnablek5users.patch
# Improve ccache handling in openssh (#991186, #1199363, #1566494)
# https://bugzilla.mindrot.org/show_bug.cgi?id=2775
Patch804: openssh-7.7p1-gssapi-new-unique.patch
# Respect k5login_directory option in krk5.conf (#1328243)
Patch805: openssh-7.2p2-k5login_directory.patch


#https://bugzilla.mindrot.org/show_bug.cgi?id=1780
Patch901: openssh-6.6p1-kuserok.patch
# Use tty allocation for a remote scp (#985650)
Patch906: openssh-6.4p1-fromto-remote.patch
# privsep_preauth: use SELinux context from selinux-policy (#1008580)
Patch916: openssh-6.6.1p1-selinux-contexts.patch
# log via monitor in chroots without /dev/log (#2681)
Patch918: openssh-6.6.1p1-log-in-chroot.patch
# scp file into non-existing directory (#1142223)
Patch919: openssh-6.6.1p1-scp-non-existing-directory.patch
# apply upstream patch and make sshd -T more consistent (#1187521)
Patch922: openssh-6.8p1-sshdT-output.patch
# Add sftp option to force mode of created files (#1191055)
Patch926: openssh-6.7p1-sftp-force-permission.patch
# make s390 use /dev/ crypto devices -- ignore closefrom
Patch939: openssh-7.2p2-s390-closefrom.patch
# Move MAX_DISPLAYS to a configuration option (#1341302)
Patch944: openssh-7.3p1-x11-max-displays.patch
# Help systemd to track the running service
Patch948: openssh-7.4p1-systemd.patch
# Pass inetd flags for SELinux down to openbsd compat level
Patch949: openssh-7.6p1-cleanup-selinux.patch
# Sandbox adjustments for s390 and audit
Patch950: openssh-7.5p1-sandbox.patch
# PKCS#11 URIs (upstream #2817, 2nd iteration)
# https://github.com/Jakuje/openssh-portable/commits/jjelen-pkcs11
# git show > ~/devel/fedora/openssh/openssh-8.0p1-pkcs11-uri.patch
Patch951: openssh-8.0p1-pkcs11-uri.patch
# Unbreak scp between two IPv6 hosts (#1620333)
Patch953: openssh-7.8p1-scp-ipv6.patch
# Mention crypto-policies in manual pages (#1668325)
Patch962: openssh-8.0p1-crypto-policies.patch
# Use OpenSSL high-level API to produce and verify signatures (#1707485)
Patch963: openssh-8.0p1-openssl-evp.patch
# Use OpenSSL KDF (#1631761)
Patch964: openssh-8.0p1-openssl-kdf.patch
# sk-dummy.so built with -fvisibility=hidden does not work
Patch965: openssh-8.2p1-visibility.patch
# Do not break X11 without IPv6
Patch966: openssh-8.2p1-x11-without-ipv6.patch
# ssh-keygen printing fingerprint issue with Windows keys (#1901518)
Patch974: openssh-8.0p1-keygen-strip-doseol.patch
# sshd provides PAM an incorrect error code (#1879503)
Patch975: openssh-8.0p1-preserve-pam-errors.patch
# Use SFTP protocol by default for scp command
Patch976: openssh-8.7p1-sftp-default-protocol.patch
# Implement kill switch for SCP protocol
Patch977: openssh-8.7p1-scp-kill-switch.patch
# CVE-2021-41617
Patch978: openssh-8.7p1-upstream-cve-2021-41617.patch
# fix for `ssh-keygen -Y find-principals -f /dev/null -s /dev/null` (#2024902)
Patch979: openssh-8.7p1-find-principals-fix.patch
# Create non-existent directories when scp works in sftp mode and some more minor fixes
# upstream commits:
# ba61123eef9c6356d438c90c1199a57a0d7bcb0a
# 63670d4e9030bcee490d5a9cce561373ac5b3b23
# ac7c9ec894ed0825d04ef69c55babb49bab1d32e
Patch980: openssh-8.7p1-sftpscp-dir-create.patch
# Workaround for lack of sftp_realpath in older versions of RHEL
# https://bugzilla.redhat.com/show_bug.cgi?id=2038854
# https://github.com/openssh/openssh-portable/pull/299
# downstream only
Patch981: openssh-8.7p1-recursive-scp.patch
# https://github.com/djmdjm/openssh-wip/pull/13
Patch982: openssh-8.7p1-minrsabits.patch
# downstream only
Patch983: openssh-8.7p1-evpgenkey.patch
# downstream only, IBMCA tentative fix
# From https://bugzilla.redhat.com/show_bug.cgi?id=1976202#c14
Patch984: openssh-8.7p1-ibmca.patch
# Upstream ff89b1bed80721295555bd083b173247a9c0484e, 5062ad48814b06162511c4f5924a33d97b6b2566
Patch986: openssh-9.1p1-sshbanner.patch

# Minimize the use of SHA1 as a proof of possession for RSA key (#2031868)
# upstream commits:
# 291721bc7c840d113a49518f3fca70e86248b8e8
# 0fa33683223c76289470a954404047bc762be84c
# Avoid dubious diagnostics on update known hosts (#2115246)
# 8832402bd500d1661ccc80a476fd563335ef6cdc
Patch1000: openssh-8.7p1-minimize-sha1-use.patch
# Fix for scp clearing file when src and dest are the same (#2056884)
# upstream commits:
# 7b1cbcb7599d9f6a3bbad79d412604aa1203b5ee
Patch1001: openssh-8.7p1-scp-clears-file.patch
# Add missing options from ssh_config into ssh manpage
# upstream bug:
# https://bugzilla.mindrot.org/show_bug.cgi?id=3455
Patch1002: openssh-8.7p1-ssh-manpage.patch
# Always return allocated strings from the kex filtering so that we can free them
# upstream commits:
# 486c4dc3b83b4b67d663fb0fa62bc24138ec3946
# 6c31ba10e97b6953c4f325f526f3e846dfea647a
# 322964f8f2e9c321e77ebae1e4d2cd0ccc5c5a0b
Patch1003: openssh-8.7p1-mem-leak.patch
# Reenable MONITOR_REQ_GSSCHECKMIC after gssapi-with-mic failures
# upstream MR:
# https://github.com/openssh-gsskex/openssh-gsskex/pull/21
Patch1004: openssh-8.7p1-gssapi-auth.patch
# Fix host-based authentication with rsa keys
# upstream commits:
# 7aa7b096cf2bafe2777085abdeed5ce00581f641
# d9dbb5d9a0326e252d3c7bc13beb9c2434f59409
# fdb1d58d0d3888b042e5a500f6ce524486aaf782
Patch1005: openssh-8.7p1-host-based-auth.patch
# Don't propose disallowed algorithms during hostkey negotiation
# upstream MR:
# https://github.com/openssh/openssh-portable/pull/323
Patch1006: openssh-8.7p1-negotiate-supported-algs.patch
# 
Patch1007: openssh-8.7p1-nohostsha1proof.patch
# CVE-2023-25136
# upstream 12da7823336434a403f25c7cc0c2c6aed0737a35
# to fix 1005
Patch1008: openssh-8.7p1-CVE-2023-25136.patch

# fips compliance for signing, dh, ecdh
Patch1009: openssh-8.7p1-evp-fips-compl-sign.patch
Patch1010: openssh-8.7p1-evp-fips-compl-dh.patch
Patch1011: openssh-8.7p1-evp-fips-compl-ecdh.patch
Patch1012: openssh-8.7p1-evp-pkcs11.patch

# clarify rhbz#2068423 on the man page of ssh_config
Patch1013: openssh-8.7p1-man-hostkeyalgos.patch
# upstream commits
# ec1ddb72a146fd66d18df9cd423517453a5d8044
# b98a42afb69d60891eb0488935990df6ee571c4
# a00f59a645072e5f5a8d207af15916a7b23e2642
Patch1014: openssh-8.7p1-UTC-time-parse.patch
# upsream commit
# b23fe83f06ee7e721033769cfa03ae840476d280
Patch1015: openssh-9.3p1-upstream-cve-2023-38408.patch
#upstream commit b7afd8a4ecaca8afd3179b55e9db79c0ff210237
Patch1016: openssh-9.3p1-openssl-compat.patch
#upstream commit 01dbf3d46651b7d6ddf5e45d233839bbfffaeaec
Patch1017: openssh-9.4p2-limit-delay.patch
#upstream commit 1edb00c58f8a6875fad6a497aa2bacf37f9e6cd5
Patch1018: openssh-9.6p1-CVE-2023-48795.patch
#upstream commit 7ef3787c84b6b524501211b11a26c742f829af1a
Patch1019: openssh-9.6p1-CVE-2023-51385.patch
#upstream commit 96faa0de6c673a2ce84736eba37fc9fb723d9e5c
Patch1020: openssh-8.7p1-sigpipe.patch
Patch1021: openssh-9.8p1-upstream-cve-2024-6387.patch
Patch1022: openssh-8.7p1-redhat-help.patch
Patch1023: openssh-8.7p1-openssl-log.patch
#upstream commit 52dfe3c72d98503d8b7c6f64fc7e19d685636c0b
Patch1024: openssh-8.7p1-allow-duplicate-subsystem.patch
# upstream 6ce00f0c2ecbb9f75023dbe627ee6460bcec78c2
# upstream 0832aac79517611dd4de93ad0a83577994d9c907
Patch1025: openssh-9.9p2-error_processing.patch

License: BSD
Requires: /sbin/nologin

%if ! %{no_gnome_askpass}
%if %{gtk2}
BuildRequires: gtk2-devel
BuildRequires: libX11-devel
%else
BuildRequires: gnome-libs-devel
%endif
%endif

BuildRequires: autoconf, automake, perl-interpreter, perl-generators, zlib-devel
BuildRequires: audit-libs-devel >= 2.0.5
BuildRequires: util-linux, groff
BuildRequires: pam-devel
BuildRequires: openssl-devel >= 0.9.8j
BuildRequires: perl-podlators
BuildRequires: systemd-devel
BuildRequires: systemd-rpm-macros
BuildRequires: gcc make
BuildRequires: p11-kit-devel
BuildRequires: libfido2-devel
Obsoletes: openssh-ldap < 8.3p1-4
Obsoletes: openssh-cavs < 8.4p1-5

%if %{kerberos5}
BuildRequires: krb5-devel
%endif

%if %{libedit}
BuildRequires: libedit-devel ncurses-devel
%endif

%if %{WITH_SELINUX}
Requires: libselinux >= 2.3-5
BuildRequires: libselinux-devel >= 2.3-5
Requires: audit-libs >= 1.0.8
BuildRequires: audit-libs >= 1.0.8
%endif

BuildRequires: xauth
# for tarball signature verification
BuildRequires: gnupg2

%package clients
Summary: An open source SSH client applications
Requires: openssh = %{version}-%{release}
Requires: crypto-policies >= 20200610-1

%package server
Summary: An open source SSH server daemon
Requires: openssh = %{version}-%{release}
Requires(pre): /usr/sbin/useradd
Requires: pam >= 1.0.1-3
Requires: crypto-policies >= 20200610-1
%{?systemd_requires}

%package keycat
Summary: A mls keycat backend for openssh
Requires: openssh = %{version}-%{release}

%package askpass
Summary: A passphrase dialog for OpenSSH and X
Requires: openssh = %{version}-%{release}

%package sk-dummy
Summary: OpenSSH SK driver for test purposes
Requires: openssh = %{version}-%{release}

%package -n pam_ssh_agent_auth
Summary: PAM module for authentication with ssh-agent
Version: %{pam_ssh_agent_ver}
Release: %{pam_ssh_agent_rel}.%{openssh_rel}%{?dist}
License: BSD

%description
SSH (Secure SHell) is a program for logging into and executing
commands on a remote machine. SSH is intended to replace rlogin and
rsh, and to provide secure encrypted communications between two
untrusted hosts over an insecure network. X11 connections and
arbitrary TCP/IP ports can also be forwarded over the secure channel.

OpenSSH is OpenBSD's version of the last free version of SSH, bringing
it up to date in terms of security and features.

This package includes the core files necessary for both the OpenSSH
client and server. To make this package useful, you should also
install openssh-clients, openssh-server, or both.

%description clients
OpenSSH is a free version of SSH (Secure SHell), a program for logging
into and executing commands on a remote machine. This package includes
the clients necessary to make encrypted connections to SSH servers.

%description server
OpenSSH is a free version of SSH (Secure SHell), a program for logging
into and executing commands on a remote machine. This package contains
the secure shell daemon (sshd). The sshd daemon allows SSH clients to
securely connect to your SSH server.

%description keycat
OpenSSH mls keycat is backend for using the authorized keys in the
openssh in the mls mode.

%description askpass
OpenSSH is a free version of SSH (Secure SHell), a program for logging
into and executing commands on a remote machine. This package contains
an X11 passphrase dialog for OpenSSH.

%description sk-dummy
This package contains a test SK driver used for OpenSSH test purposes

%description -n pam_ssh_agent_auth
This package contains a PAM module which can be used to authenticate
users using ssh keys stored in a ssh-agent. Through the use of the
forwarding of ssh-agent connection it also allows to authenticate with
remote ssh-agent instance.

The module is most useful for su and sudo service stacks.

%prep
gpgv2 --quiet --keyring %{SOURCE3} %{SOURCE1} %{SOURCE0}
%setup -q -a 4

%if %{pam_ssh_agent}
pushd pam_ssh_agent_auth-pam_ssh_agent_auth-%{pam_ssh_agent_ver}
%patch300 -p2 -b .psaa-build
%patch301 -p2 -b .psaa-seteuid
%patch302 -p2 -b .psaa-visibility
%patch306 -p2 -b .psaa-compat
%patch305 -p2 -b .psaa-agent
%patch307 -p2 -b .psaa-deref
%patch308 -p2 -b .rsasha2
# Remove duplicate headers and library files
rm -f $(cat %{SOURCE5})
popd
%endif

%patch400 -p1 -b .role-mls
%patch404 -p1 -b .privsep-selinux

%patch502 -p1 -b .keycat

%patch601 -p1 -b .ip-opts
%patch604 -p1 -b .keyperm
%patch606 -p1 -b .ipv6man
%patch607 -p1 -b .sigpipe
%patch609 -p1 -b .x11
%patch702 -p1 -b .progress
%patch703 -p1 -b .grab-info
%patch707 -p1 -b .redhat
%patch711 -p1 -b .log-usepam-no
%patch712 -p1 -b .evp-ctr
# 
%patch800 -p1 -b .gsskex
%patch801 -p1 -b .force_krb
%patch804 -p1 -b .ccache_name
%patch805 -p1 -b .k5login
# 
%patch901 -p1 -b .kuserok
%patch906 -p1 -b .fromto-remote
%patch916 -p1 -b .contexts
%patch918 -p1 -b .log-in-chroot
%patch919 -p1 -b .scp
%patch802 -p1 -b .GSSAPIEnablek5users
%patch922 -p1 -b .sshdt
%patch926 -p1 -b .sftp-force-mode
%patch939 -p1 -b .s390-dev
%patch944 -p1 -b .x11max
%patch948 -p1 -b .systemd
%patch949 -p1 -b .refactor
%patch950 -p1 -b .sandbox
%patch951 -p1 -b .pkcs11-uri
%patch953 -p1 -b .scp-ipv6
%patch962 -p1 -b .crypto-policies
%patch963 -p1 -b .openssl-evp
%patch964 -p1 -b .openssl-kdf
%patch965 -p1 -b .visibility
%patch966 -p1 -b .x11-ipv6
%patch974 -p1 -b .keygen-strip-doseol
%patch975 -p1 -b .preserve-pam-errors
%patch976 -p1 -b .sftp-by-default
%patch977 -p1 -b .kill-scp
%patch978 -p1 -b .cve-2021-41617
%patch979 -p1 -b .find-principals
%patch980 -p1 -b .sftpdirs
%patch981 -p1 -b .scp-sftpdirs
%patch982 -p1 -b .minrsabits
%patch983 -p1 -b .evpgenrsa
%patch984 -p1 -b .ibmca
%patch986 -p1 -b .91cleanup

%patch200 -p1 -b .audit
%patch201 -p1 -b .audit-race
%patch202 -p1 -b .audit-hostname
%patch700 -p1 -b .fips

%patch1000 -p1 -b .minimize-sha1-use
%patch1001 -p1 -b .scp-clears-file
%patch1002 -p1 -b .ssh-manpage
%patch1003 -p1 -b .mem-leak
%patch1004 -p1 -b .gssapi-auth
%patch1005 -p1 -b .host-based-auth
%patch1006 -p1 -b .negotiate-supported-algs

%patch100 -p1 -b .coverity

%patch1007 -p1 -b .sshrsacheck
%patch1008 -p1 -b .cve-2023-25136

%patch1009 -p1 -b .evp_fips_sign
%patch1010 -p1 -b .evp_fips_dh
%patch1011 -p1 -b .evp_fips_ecdh
%patch1012 -p1 -b .evp_pkcs11

%patch1013 -p1 -b .man-hostkeyalgos
%patch1014 -p1 -b .utc_parse
%patch1015 -p1 -b .cve-2023-38408
%patch1016 -p1 -b .openssl3compat
%patch1017 -p1 -b .limitdelay
%patch1018 -p1 -b .cve-2023-48795
%patch1019 -p1 -b .cve-2023-51385
%patch1020 -p1 -b .earlypipe
%patch1021 -p1 -b .cve-2024-6387
%patch1022 -p1 -b .redhat-help
%patch1023 -p1 -b .openssl-log
%patch1024 -p1 -b .allow-dup-subsystem
%patch1025 -p1 -b .errcode_set

autoreconf
pushd pam_ssh_agent_auth-pam_ssh_agent_auth-%{pam_ssh_agent_ver}
autoreconf
popd

%build
# the -fvisibility=hidden is needed for clean build of the pam_ssh_agent_auth
# it is needed for lib(open)ssh build too since it is linked to the pam module too
CFLAGS="$RPM_OPT_FLAGS -fvisibility=hidden"; export CFLAGS
%if %{pie}
%ifarch s390 s390x sparc sparcv9 sparc64
CFLAGS="$CFLAGS -fPIC"
%else
CFLAGS="$CFLAGS -fpic"
%endif
SAVE_LDFLAGS="$LDFLAGS"
LDFLAGS="$LDFLAGS -pie -z relro -z now"

export CFLAGS
export LDFLAGS

%endif
%if %{kerberos5}
if test -r /etc/profile.d/krb5-devel.sh ; then
	source /etc/profile.d/krb5-devel.sh
fi
krb5_prefix=`krb5-config --prefix`
if test "$krb5_prefix" != "%{_prefix}" ; then
	CPPFLAGS="$CPPFLAGS -I${krb5_prefix}/include -I${krb5_prefix}/include/gssapi"; export CPPFLAGS
	CFLAGS="$CFLAGS -I${krb5_prefix}/include -I${krb5_prefix}/include/gssapi"
	LDFLAGS="$LDFLAGS -L${krb5_prefix}/%{_lib}"; export LDFLAGS
else
	krb5_prefix=
	CPPFLAGS="-I%{_includedir}/gssapi"; export CPPFLAGS
	CFLAGS="$CFLAGS -I%{_includedir}/gssapi"
fi
%endif

%configure \
	--sysconfdir=%{_sysconfdir}/ssh \
	--libexecdir=%{_libexecdir}/openssh \
	--datadir=%{_datadir}/openssh \
	--with-default-path=/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin \
	--with-superuser-path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin \
	--with-privsep-path=%{_datadir}/empty.sshd \
	--disable-strip \
	--without-zlib-version-check \
	--with-ssl-engine \
	--with-ipaddr-display \
	--with-pie=no \
	--without-hardening `# The hardening flags are configured by system` \
	--with-systemd \
	--with-default-pkcs11-provider=yes \
	--with-security-key-builtin=yes \
	--with-pam \
%if %{WITH_SELINUX}
	--with-selinux --with-audit=linux \
	--with-sandbox=seccomp_filter \
%endif
%if %{kerberos5}
	--with-kerberos5${krb5_prefix:+=${krb5_prefix}} \
%else
	--without-kerberos5 \
%endif
%if %{libedit}
	--with-libedit
%else
	--without-libedit
%endif

%if %{static_libcrypto}
perl -pi -e "s|-lcrypto|%{_libdir}/libcrypto.a|g" Makefile
%endif

%make_build
make regress/misc/sk-dummy/sk-dummy.so

# Define a variable to toggle gnome1/gtk2 building.  This is necessary
# because RPM doesn't handle nested %%if statements.
%if %{gtk2}
	gtk2=yes
%else
	gtk2=no
%endif

%if ! %{no_gnome_askpass}
pushd contrib
if [ $gtk2 = yes ] ; then
	CFLAGS="$CFLAGS %{?__global_ldflags}" \
	    make gnome-ssh-askpass2
	mv gnome-ssh-askpass2 gnome-ssh-askpass
else
	CFLAGS="$CFLAGS %{?__global_ldflags}"
	    make gnome-ssh-askpass1
	mv gnome-ssh-askpass1 gnome-ssh-askpass
fi
popd
%endif

%if %{pam_ssh_agent}
pushd pam_ssh_agent_auth-pam_ssh_agent_auth-%{pam_ssh_agent_ver}
LDFLAGS="$SAVE_LDFLAGS"
%configure --with-selinux \
	--libexecdir=/%{_libdir}/security \
	--with-mantype=man \
	--without-openssl-header-check `# The check is broken`
%make_build
popd
%endif

%check
#to run tests use "--with check"
%if %{?_with_check:1}%{!?_with_check:0}
make tests
%endif

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p -m755 $RPM_BUILD_ROOT%{_sysconfdir}/ssh
mkdir -p -m755 $RPM_BUILD_ROOT%{_sysconfdir}/ssh/ssh_config.d
mkdir -p -m755 $RPM_BUILD_ROOT%{_sysconfdir}/ssh/sshd_config.d
mkdir -p -m755 $RPM_BUILD_ROOT%{_libexecdir}/openssh
%make_install

install -d $RPM_BUILD_ROOT/etc/pam.d/
install -d $RPM_BUILD_ROOT/etc/sysconfig/
install -d $RPM_BUILD_ROOT%{_libexecdir}/openssh
install -m644 %{SOURCE2} $RPM_BUILD_ROOT/etc/pam.d/sshd
install -m644 %{SOURCE6} $RPM_BUILD_ROOT/etc/pam.d/ssh-keycat
install -m644 %{SOURCE7} $RPM_BUILD_ROOT/etc/sysconfig/sshd
install -m644 ssh_config_redhat $RPM_BUILD_ROOT/etc/ssh/ssh_config.d/50-redhat.conf
install -m644 sshd_config_redhat $RPM_BUILD_ROOT/etc/ssh/sshd_config.d/50-redhat.conf
install -d -m755 $RPM_BUILD_ROOT/%{_unitdir}
install -m644 %{SOURCE9} $RPM_BUILD_ROOT/%{_unitdir}/sshd@.service
install -m644 %{SOURCE10} $RPM_BUILD_ROOT/%{_unitdir}/sshd.socket
install -m644 %{SOURCE11} $RPM_BUILD_ROOT/%{_unitdir}/sshd.service
install -m644 %{SOURCE12} $RPM_BUILD_ROOT/%{_unitdir}/sshd-keygen@.service
install -m644 %{SOURCE15} $RPM_BUILD_ROOT/%{_unitdir}/sshd-keygen.target
install -d -m755 $RPM_BUILD_ROOT/%{_userunitdir}
install -m644 %{SOURCE16} $RPM_BUILD_ROOT/%{_userunitdir}/ssh-agent.service
install -m744 %{SOURCE13} $RPM_BUILD_ROOT/%{_libexecdir}/openssh/sshd-keygen
install -m755 contrib/ssh-copy-id $RPM_BUILD_ROOT%{_bindir}/
install contrib/ssh-copy-id.1 $RPM_BUILD_ROOT%{_mandir}/man1/
install -d -m711 ${RPM_BUILD_ROOT}/%{_datadir}/empty.sshd
install -p -D -m 0644 %{SOURCE17} %{buildroot}%{_sysusersdir}/openssh.conf
install -p -D -m 0644 %{SOURCE18} %{buildroot}%{_sysusersdir}/openssh-server.conf

%if ! %{no_gnome_askpass}
install contrib/gnome-ssh-askpass $RPM_BUILD_ROOT%{_libexecdir}/openssh/gnome-ssh-askpass
%endif

%if ! %{no_gnome_askpass}
ln -s gnome-ssh-askpass $RPM_BUILD_ROOT%{_libexecdir}/openssh/ssh-askpass
install -m 755 -d $RPM_BUILD_ROOT%{_sysconfdir}/profile.d/
install -m 755 contrib/redhat/gnome-ssh-askpass.csh $RPM_BUILD_ROOT%{_sysconfdir}/profile.d/
install -m 755 contrib/redhat/gnome-ssh-askpass.sh $RPM_BUILD_ROOT%{_sysconfdir}/profile.d/
%endif

%if %{no_gnome_askpass}
rm -f $RPM_BUILD_ROOT/etc/profile.d/gnome-ssh-askpass.*
%endif

perl -pi -e "s|$RPM_BUILD_ROOT||g" $RPM_BUILD_ROOT%{_mandir}/man*/*

%if %{pam_ssh_agent}
pushd pam_ssh_agent_auth-pam_ssh_agent_auth-%{pam_ssh_agent_ver}
%make_install
popd
%endif

install -m 755 -d $RPM_BUILD_ROOT%{_libdir}/sshtest/
install -m 755 regress/misc/sk-dummy/sk-dummy.so $RPM_BUILD_ROOT%{_libdir}/sshtest

%pre
%sysusers_create_compat %{SOURCE17}

%pre server
%sysusers_create_compat %{SOURCE18}

%post server
%systemd_post sshd.service sshd.socket
# Migration scriptlet for Fedora 31 and 32 installations to sshd_config
# drop-in directory (in F32+).
# Do this only if the file generated by anaconda exists, contains our config
# directive and sshd_config contains include directive as shipped in our package
%global sysconfig_anaconda /etc/sysconfig/sshd-permitrootlogin
test -f %{sysconfig_anaconda} && \
  test ! -f /etc/ssh/sshd_config.d/01-permitrootlogin.conf && \
  grep -q '^PERMITROOTLOGIN="-oPermitRootLogin=yes"' %{sysconfig_anaconda} && \
  grep -q '^Include /etc/ssh/sshd_config.d/\*.conf' /etc/ssh/sshd_config && \
  echo "PermitRootLogin yes" >> /etc/ssh/sshd_config.d/25-permitrootlogin.conf && \
  rm %{sysconfig_anaconda} || :

%preun server
%systemd_preun sshd.service sshd.socket

%postun server
%systemd_postun_with_restart sshd.service

%post clients
%systemd_user_post ssh-agent.service

%preun clients
%systemd_user_preun ssh-agent.service

%files
%license LICENCE
%doc CREDITS ChangeLog OVERVIEW PROTOCOL* README README.platform README.privsep README.tun README.dns TODO
%attr(0755,root,root) %dir %{_sysconfdir}/ssh
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/ssh/moduli
%attr(0755,root,root) %{_bindir}/ssh-keygen
%attr(0644,root,root) %{_mandir}/man1/ssh-keygen.1*
%attr(0755,root,root) %dir %{_libexecdir}/openssh
%attr(2555,root,ssh_keys) %{_libexecdir}/openssh/ssh-keysign
%attr(0644,root,root) %{_mandir}/man8/ssh-keysign.8*
%attr(0644,root,root) %{_sysusersdir}/openssh.conf

%files clients
%attr(0755,root,root) %{_bindir}/ssh
%attr(0644,root,root) %{_mandir}/man1/ssh.1*
%attr(0755,root,root) %{_bindir}/scp
%attr(0644,root,root) %{_mandir}/man1/scp.1*
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/ssh/ssh_config
%dir %attr(0755,root,root) %{_sysconfdir}/ssh/ssh_config.d/
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/ssh/ssh_config.d/50-redhat.conf
%attr(0644,root,root) %{_mandir}/man5/ssh_config.5*
%attr(0755,root,root) %{_bindir}/ssh-agent
%attr(0755,root,root) %{_bindir}/ssh-add
%attr(0755,root,root) %{_bindir}/ssh-keyscan
%attr(0755,root,root) %{_bindir}/sftp
%attr(0755,root,root) %{_bindir}/ssh-copy-id
%attr(0755,root,root) %{_libexecdir}/openssh/ssh-pkcs11-helper
%attr(0755,root,root) %{_libexecdir}/openssh/ssh-sk-helper
%attr(0644,root,root) %{_mandir}/man1/ssh-agent.1*
%attr(0644,root,root) %{_mandir}/man1/ssh-add.1*
%attr(0644,root,root) %{_mandir}/man1/ssh-keyscan.1*
%attr(0644,root,root) %{_mandir}/man1/sftp.1*
%attr(0644,root,root) %{_mandir}/man1/ssh-copy-id.1*
%attr(0644,root,root) %{_mandir}/man8/ssh-pkcs11-helper.8*
%attr(0644,root,root) %{_mandir}/man8/ssh-sk-helper.8*
%attr(0644,root,root) %{_userunitdir}/ssh-agent.service

%files server
%dir %attr(0711,root,root) %{_datadir}/empty.sshd
%attr(0755,root,root) %{_sbindir}/sshd
%attr(0755,root,root) %{_libexecdir}/openssh/sftp-server
%attr(0755,root,root) %{_libexecdir}/openssh/sshd-keygen
%attr(0644,root,root) %{_mandir}/man5/sshd_config.5*
%attr(0644,root,root) %{_mandir}/man5/moduli.5*
%attr(0644,root,root) %{_mandir}/man8/sshd.8*
%attr(0644,root,root) %{_mandir}/man8/sftp-server.8*
%attr(0600,root,root) %config(noreplace) %{_sysconfdir}/ssh/sshd_config
%dir %attr(0700,root,root) %{_sysconfdir}/ssh/sshd_config.d/
%attr(0600,root,root) %config(noreplace) %{_sysconfdir}/ssh/sshd_config.d/50-redhat.conf
%attr(0644,root,root) %config(noreplace) /etc/pam.d/sshd
%attr(0640,root,root) %config(noreplace) /etc/sysconfig/sshd
%attr(0644,root,root) %{_unitdir}/sshd.service
%attr(0644,root,root) %{_unitdir}/sshd@.service
%attr(0644,root,root) %{_unitdir}/sshd.socket
%attr(0644,root,root) %{_unitdir}/sshd-keygen@.service
%attr(0644,root,root) %{_unitdir}/sshd-keygen.target
%attr(0644,root,root) %{_sysusersdir}/openssh-server.conf

%files keycat
%doc HOWTO.ssh-keycat
%attr(0755,root,root) %{_libexecdir}/openssh/ssh-keycat
%attr(0644,root,root) %config(noreplace) /etc/pam.d/ssh-keycat

%if ! %{no_gnome_askpass}
%files askpass
%attr(0644,root,root) %{_sysconfdir}/profile.d/gnome-ssh-askpass.*
%attr(0755,root,root) %{_libexecdir}/openssh/gnome-ssh-askpass
%attr(0755,root,root) %{_libexecdir}/openssh/ssh-askpass
%endif

%files sk-dummy
%attr(0755,root,root) %{_libdir}/sshtest/sk-dummy.so

%if %{pam_ssh_agent}
%files -n pam_ssh_agent_auth
%license pam_ssh_agent_auth-pam_ssh_agent_auth-%{pam_ssh_agent_ver}/OPENSSH_LICENSE
%attr(0755,root,root) %{_libdir}/security/pam_ssh_agent_auth.so
%attr(0644,root,root) %{_mandir}/man8/pam_ssh_agent_auth.8*
%endif

%changelog
* Tue Feb 18 2025 Dmitry Belyavskiy <dbelyavs@redhat.com> - 8.7p1-45
- Fix missing error codes set and invalid error code checks in OpenSSH. It
  prevents memory exhaustion attack and a MITM attack when VerifyHostKeyDNS
  is on (CVE-2025-26465).
  Resolves: RHEL-78700

* Mon Oct 21 2024 Dmitry Belyavskiy <dbelyavs@redhat.com> - 8.7p1-44
- Add extra help information on ssh early failure
  Resolves: RHEL-33809
- Provide details on crypto error instead of "error in libcrypto"
  Resolves: RHEL-52293
- Allow duplicate Subsystem directive
  Resolves: RHEL-47112
