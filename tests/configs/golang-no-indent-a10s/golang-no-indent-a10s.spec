%bcond_with bootstrap
# temporalily ignore test failures
# due to https://github.com/golang/go/issues/39466
%ifarch aarch64
%bcond_without ignore_tests
%else
%bcond_with ignore_tests
%endif

# Enable race by default
%global race 1

# Disable race on riscv64 as it's not supported
%ifarch riscv64
%global race 0
%endif

# build ids are not currently generated:
# https://code.google.com/p/go/issues/detail?id=5238
#
# also, debuginfo extraction currently fails with
# "Failed to write file: invalid section alignment"
%global debug_package %{nil}

# we are shipping the full contents of src in the data subpackage, which
# contains binary-like things (ELF data for tests, etc)
%global _binaries_in_noarch_packages_terminate_build 0

# Do not check any files in doc or src for requires
%global __requires_exclude_from ^(%{_datadir}|/usr/lib)/%{name}/(doc|src)/.*$

# Don't alter timestamps of especially the .a files (or else go will rebuild later)
# Actually, don't strip at all since we are not even building debug packages and this corrupts the dwarf testdata
%global __strip /bin/true

# rpmbuild magic to keep from having meta dependency on libc.so.6
%define _use_internal_dependency_generator 0
%define __find_requires %{nil}
%global __spec_install_post /usr/lib/rpm/check-rpaths   /usr/lib/rpm/check-buildroot  \
  /usr/lib/rpm/brp-compress

%global golibdir %{_libdir}/golang

# This macro may not always be defined, ensure it is
%{!?gopath: %global gopath %{_datadir}/gocode}

# Golang build options.

# Disable FIPS by default
%global fips 0
# Enable FIPS by default in RHEL
%if 0%{?rhel}
%global fips 1
%endif

# Build golang using external/internal(close to cgo disabled) linking.
%ifarch %{ix86} x86_64 ppc64le %{arm} aarch64 s390x riscv64
%global external_linker 1
%else
%global external_linker 0
%endif

# Build golang with cgo enabled/disabled(later equals more or less to internal linking).
%ifarch %{ix86} x86_64 ppc64le %{arm} aarch64 s390x riscv64
%global cgo_enabled 1
%else
%global cgo_enabled 0
%endif

# Use golang/gcc-go as bootstrap compiler
%if %{with bootstrap}
%global golang_bootstrap 0
%else
%global golang_bootstrap 1
%endif

# Controls what ever we fail on failed tests
%if %{with ignore_tests}
%global fail_on_tests 0
%else
%global fail_on_tests 1
%endif

# shared mode is breaks Go 1.21 in ELN
%global shared 0

# Fedora GOROOT
%global goroot          /usr/lib/%{name}

%ifarch x86_64
%global gohostarch  amd64
%endif
%ifarch %{ix86}
%global gohostarch  386
%endif
%ifarch %{arm}
%global gohostarch  arm
%endif
%ifarch aarch64
%global gohostarch  arm64
%endif
%ifarch ppc64
%global gohostarch  ppc64
%endif
%ifarch ppc64le
%global gohostarch  ppc64le
%endif
%ifarch s390x
%global gohostarch  s390x
%endif
%ifarch riscv64
%global gohostarch  riscv64
%endif

%global go_api 1.25
# Use only for prerelease versions
#global go_prerelease rc3
%global go_patch 1
%global go_version %{go_api}%{?go_patch:.%{go_patch}}%{?go_prerelease:~%{go_prerelease}}
%global go_source %{go_api}%{?go_patch:.%{go_patch}}%{?go_prerelease}
# Go FIPS package release
%global pkg_release 1

# For rpmdev-bumpspec and releng automation.
%global baserelease 1

# LLVM compiler-rt version for race detector
%global llvm_compiler_rt_version 18.1.8

Name:           golang
Version:	%{go_version}
Release:        %autorelease
Summary:        The Go Programming Language
# source tree includes several copies of Mark.Twain-Tom.Sawyer.txt under Public Domain
License:        BSD-3-Clause AND LicenseRef-Fedora-Public-Domain
URL:            https://go.dev
Source0:        https://go.dev/dl/go%{go_source}.src.tar.gz
# Go's FIPS mode bindings are now provided as a standalone
# module instead of in tree.  This makes it easier to see
# the actual changes vs upstream Go.  The module source is
# located at https://github.com/golang-fips/openssl-fips,
# And pre-genetated patches to set up the module for a given
# Go release are located at https://github.com/golang-fips/go.
# making a source conditional creates odd behaviors so for now, include FIPS always
Source1:        https://github.com/golang-fips/go/archive/refs/tags/go%{go_source}-%{pkg_release}-openssl-fips.tar.gz
# make possible to override default traceback level at build time by setting build tag rpm_crashtraceback
Source2:        fedora.go
Source3:       https://github.com/llvm/llvm-project/releases/download/llvmorg-%{llvm_compiler_rt_version}/compiler-rt-%{llvm_compiler_rt_version}.src.tar.xz

# The compiler is written in Go. Needs go(1.4+) compiler for build.
%if !%{golang_bootstrap}
BuildRequires:  gcc-go >= 5
%else
BuildRequires:  golang > 1.4
%endif

# Install hostname(1) or net-tools(1) depending on the OS version
%if 0%{?rhel} > 6 || 0%{?fedora} > 0
BuildRequires:  hostname
%else
BuildRequires:  net-tools
%endif

# If FIPS is enabled, we need openssl-devel
%if %{fips}
BuildRequires:  openssl-devel
Requires:       openssl-devel
%endif

BuildRequires:  glibc-static

# For running the tests on Fedora
%if 0%{?fedora}
BuildRequires:  perl-interpreter, procps-ng
%endif

# For running the tests on RHEL
%if 0%{?rhel}
BuildRequires:  perl
%endif
# For building llvm address sanitizer for Go race detector
BuildRequires: libstdc++-devel
BuildRequires: clang

Provides:       go = %{version}-%{release}

%if 0%{?fedora}
# Bundled/Vendored provides generated by bundled-deps.sh based on the in tree module data
Provides: bundled(golang(github.com/google/pprof)) = 0.0.0.20250208200701.d0013a598941
Provides: bundled(golang(github.com/ianlancetaylor/demangle)) = 0.0.0.20240912202439.0a2b6291aafd
Provides: bundled(golang(golang.org/x/arch)) = 0.18.1.0.20250605182141.b2f4e2807dec
Provides: bundled(golang(golang.org/x/build)) = 0.0.0.20250606033421.8c8ff6f34a83
Provides: bundled(golang(golang.org/x/crypto)) = 0.39.0
Provides: bundled(golang(golang.org/x/mod)) = 0.25.0
Provides: bundled(golang(golang.org/x/net)) = 0.41.0
Provides: bundled(golang(golang.org/x/sync)) = 0.15.0
Provides: bundled(golang(golang.org/x/sys)) = 0.33.0
Provides: bundled(golang(golang.org/x/telemetry)) = 0.0.0.20250606142133.60998feb31a8
Provides: bundled(golang(golang.org/x/term)) = 0.32.0
Provides: bundled(golang(golang.org/x/text)) = 0.26.0
Provides: bundled(golang(golang.org/x/tools)) = 0.27.0
Provides: bundled(golang(golang.org/x/tools)) = 0.34.0
Provides: bundled(golang(rsc.io/markdown)) = 0.0.0.20240306144322.0bf8f97ee8ef
%endif

Requires:       %{name}-bin = %{version}-%{release}
Requires:       %{name}-src = %{version}-%{release}
%if %{race}
Requires:       %{name}-race = %{version}-%{release}
%endif

Patch1:         0001-Modify-go.env.patch
Patch6:         0006-Default-to-ld.bfd-on-ARM64.patch
# Related: https://sourceware.org/bugzilla/show_bug.cgi?id=33204
Patch7:         revert_dwarf5.patch

# Having documentation separate was broken
Obsoletes:      %{name}-docs < 1.1-4

# RPM can't handle symlink -> dir with subpackages, so merge back
Obsoletes:      %{name}-data < 1.1.1-4

# go1.4 deprecates a few packages
Obsoletes:      %{name}-vim < 1.4
Obsoletes:      emacs-%{name} < 1.4

# These are the only RHEL/Fedora architectures that we compile this package for
ExclusiveArch:  %{golang_arches}

Source100:      golang-gdbinit
Source101:      golang-prelink.conf

%description
%{summary}.

%package       docs
Summary:       Golang compiler docs
Requires:      %{name} = %{version}-%{release}
BuildArch:     noarch
Obsoletes:     %{name}-docs < 1.1-4

%description   docs
%{summary}.

%package       misc
Summary:       Golang compiler miscellaneous sources
Requires:      %{name} = %{version}-%{release}
BuildArch:     noarch

%description   misc
%{summary}.

%package       tests
Summary:       Golang compiler tests for stdlib
Requires:      %{name} = %{version}-%{release}
BuildArch:     noarch

%description   tests
%{summary}.

%package        src
Summary:        Golang compiler source tree
BuildArch:      noarch
%description    src
%{summary}

%package        bin
Summary:        Golang core compiler tools
# Some distributions refer to this package by this name
Provides:       %{name}-go = %{version}-%{release}
Requires:       go = %{version}-%{release}
# Pre-go1.5, all arches had to be bootstrapped individually, before usable, and
# env variables to compile for the target os-arch.
# Now the host compiler needs only the GOOS and GOARCH environment variables
# set to compile for the target os-arch.
Obsoletes:      %{name}-pkg-bin-linux-386 < 1.4.99
Obsoletes:      %{name}-pkg-bin-linux-amd64 < 1.4.99
Obsoletes:      %{name}-pkg-bin-linux-arm < 1.4.99
Obsoletes:      %{name}-pkg-linux-386 < 1.4.99
Obsoletes:      %{name}-pkg-linux-amd64 < 1.4.99
Obsoletes:      %{name}-pkg-linux-arm < 1.4.99
Obsoletes:      %{name}-pkg-darwin-386 < 1.4.99
Obsoletes:      %{name}-pkg-darwin-amd64 < 1.4.99
Obsoletes:      %{name}-pkg-windows-386 < 1.4.99
Obsoletes:      %{name}-pkg-windows-amd64 < 1.4.99
Obsoletes:      %{name}-pkg-plan9-386 < 1.4.99
Obsoletes:      %{name}-pkg-plan9-amd64 < 1.4.99
Obsoletes:      %{name}-pkg-freebsd-386 < 1.4.99
Obsoletes:      %{name}-pkg-freebsd-amd64 < 1.4.99
Obsoletes:      %{name}-pkg-freebsd-arm < 1.4.99
Obsoletes:      %{name}-pkg-netbsd-386 < 1.4.99
Obsoletes:      %{name}-pkg-netbsd-amd64 < 1.4.99
Obsoletes:      %{name}-pkg-netbsd-arm < 1.4.99
Obsoletes:      %{name}-pkg-openbsd-386 < 1.4.99
Obsoletes:      %{name}-pkg-openbsd-amd64 < 1.4.99

Obsoletes:      golang-vet < 0-12.1
Obsoletes:      golang-cover < 0-12.1

Requires(post): %{_sbindir}/update-alternatives
Requires(preun): %{_sbindir}/update-alternatives

# We strip the meta dependency, but go does require glibc.
# This is an odd issue, still looking for a better fix.
Requires:       glibc
Requires:       gcc
%if 0%{?rhel} && 0%{?rhel} < 8
Requires:       git, subversion, mercurial
%else
Recommends:     git, subversion, mercurial
%endif
%description    bin
%{summary}

# Workaround old RPM bug of symlink-replaced-with-dir failure
%pretrans -p <lua>
for _,d in pairs({"api", "doc", "include", "lib", "src"}) do
  path = "%{goroot}/" .. d
  if posix.stat(path, "type") == "link" then
    os.remove(path)
    posix.mkdir(path)
  end
end

%if %{shared}
%package        shared
Summary:        Golang shared object libraries

%description    shared
%{summary}.
%endif

%package -n go-toolset
Summary:        Package that installs go-toolset
Requires:       %{name} = %{version}-%{release}
%ifarch x86_64 aarch64 ppc64le
Requires:       delve
%endif

%description -n go-toolset
This is the main package for go-toolset.

%if %{race}
%package race
Summary:       Race detetector library object files.
Requires:       %{name} = %{version}-%{release}

%description    race
Binary library objects for Go's race detector.
%endif


%prep
%autosetup -p1 -n go
# Copy fedora.go to ./src/runtime/
cp %{SOURCE2} ./src/runtime/
sed -i '1s/$/ (%{?rhel:Red Hat} %{version}-%{release})/' VERSION
# Delete the bundled race detector objects.
find ./src/runtime/race/ -name "race_*.syso" -exec rm {} \;
# Delete the boring binary blob.  We use the system OpenSSL instead.
rm -rf src/crypto/internal/boring/syso

# If FIPS is enabled, install the FIPS source
%if %{fips}
    echo "Preparing FIPS patches"
    pushd ..
    tar -xf %{SOURCE1}
    popd
    # TODO Check here, this is failing due to the external linker flag? maybe, but it's clearly related to that according tho this commit:
    # https://github.com/golang-fips/go/blob/main/patches/000-initial-setup.patch#L48
    # Add --no-backup-if-mismatch option to avoid creating .orig temp files
    patch_dir="../go-go%{version}-%{pkg_release}-openssl-fips/patches"
    for p in "$patch_dir"/*.patch; do
	echo "Applying $p"
	patch --no-backup-if-mismatch -p1 < $p
    done

    # Configure crypto tests
    echo "Configure crypto tests"
    pushd ../go-go%{version}-%{pkg_release}-openssl-fips
    ln -s ../go go
    ./scripts/configure-crypto-tests.sh
    popd
%endif

%build
# -x: print commands as they are executed
# -e: exit immediately if a command exits with a non-zero status
set -xe

# print out system information
uname -a
cat /proc/cpuinfo
cat /proc/meminfo

# Build race detector .syso's from llvm sources
# The race detector requests a -fno-exceptions build.
%global tsan_buildflags %(rpm -D 'toolchain clang' -E '%{optflags}' | sed 's/-fexceptions//')
%global tsan_optflag -O1
mkdir ../llvm

tar -xf %{SOURCE3} -C ../llvm
tsan_go_dir="../llvm/compiler-rt-%{llvm_compiler_rt_version}.src/lib/tsan/go"

# The script uses uname -a and grep to set the GOARCH.  This
# is unreliable and can get the wrong architecture in
# circumstances like cross-architecture emulation.  We fix it
# by just reading GOARCH directly from Go.
export GOARCH=$(go env GOARCH)

%if %{race}
%ifarch x86_64
pushd "${tsan_go_dir}"
  CFLAGS="%{tsan_buildflags} %{tsan_optflag}" CC=clang GOAMD64=v3 ./buildgo.sh
popd
cp "${tsan_go_dir}"/race_linux_amd64.syso ./src/runtime/race/internal/amd64v3/race_linux.syso

pushd "${tsan_go_dir}"
  CFLAGS="%{tsan_buildflags} %{tsan_optflag}" CC=clang GOAMD64=v3 ./buildgo.sh
popd
cp "${tsan_go_dir}"/race_linux_amd64.syso ./src/runtime/race/internal/amd64v1/race_linux.syso

%else
pushd "${tsan_go_dir}"
  CFLAGS="%{tsan_buildflags} %{tsan_optflag}" CC=clang ./buildgo.sh
popd
cp "${tsan_go_dir}"/race_linux_%{gohostarch}.syso ./src/runtime/race/race_linux_%{gohostarch}.syso
%endif
%endif

# bootstrap compiler GOROOT
%if !%{golang_bootstrap}
export GOROOT_BOOTSTRAP=/
%else
export GOROOT_BOOTSTRAP=%{goroot}
%endif

# set up final install location
export GOROOT_FINAL=%{goroot}

export GOHOSTOS=linux
export GOHOSTARCH=%{gohostarch}
export GOAMD64=v3
export GOPPC64='power9'

pushd src
# use our gcc options for this build, but store gcc as default for compiler
export CFLAGS="$RPM_OPT_FLAGS"
export LDFLAGS="$RPM_LD_FLAGS"
export CC="gcc"
export CC_FOR_TARGET="gcc"
export GOOS=linux
export GOARCH=%{gohostarch}
export GOAMD64=v3
export GOPPC64='power9'

DEFAULT_GO_LD_FLAGS=""
%if !%{external_linker}
export GO_LDFLAGS="-linkmode internal $DEFAULT_GO_LD_FLAGS"
%else
# Only pass a select subset of the external hardening flags. We do not pass along
# the default $RPM_LD_FLAGS as on certain arches Go does not fully, correctly support
# building in PIE mode.
export GO_LDFLAGS="\"-extldflags=-Wl,-z,now,-z,relro\" $DEFAULT_GO_LD_FLAGS"
%endif

%if !%{cgo_enabled}
export CGO_ENABLED=0
%endif

./make.bash --no-clean -v
popd

# build shared std lib
%if %{shared}
GOROOT=$(pwd) PATH=$(pwd)/bin:$PATH go install -buildmode=shared -v -x std
%endif

%if %{race}
GOROOT=$(pwd) PATH=$(pwd)/bin:$PATH go install -race std
%endif

%install
rm -rf $RPM_BUILD_ROOT
# remove GC build cache
rm -rf pkg/obj/go-build/*

# create the top level directories
mkdir -p $RPM_BUILD_ROOT%{_bindir}
mkdir -p $RPM_BUILD_ROOT%{goroot}

# install everything into libdir (until symlink problems are fixed)
# https://code.google.com/p/go/issues/detail?id=5830
cp -apv api bin doc lib pkg src misc test go.env VERSION \
   $RPM_BUILD_ROOT%{goroot}

# bz1099206
find $RPM_BUILD_ROOT%{goroot}/src -exec touch -r $RPM_BUILD_ROOT%{goroot}/VERSION "{}" \;
# and level out all the built archives
touch $RPM_BUILD_ROOT%{goroot}/pkg
find $RPM_BUILD_ROOT%{goroot}/pkg -exec touch -r $RPM_BUILD_ROOT%{goroot}/pkg "{}" \;
# generate the spec file ownership of this source tree and packages
cwd=$(pwd)
src_list=$cwd/go-src.list
pkg_list=$cwd/go-pkg.list
shared_list=$cwd/go-shared.list
race_list=$cwd/go-race.list
misc_list=$cwd/go-misc.list
docs_list=$cwd/go-docs.list
tests_list=$cwd/go-tests.list
rm -f $src_list $pkg_list $docs_list $misc_list $tests_list $shared_list $race_list
touch $src_list $pkg_list $docs_list $misc_list $tests_list $shared_list $race_list

##################
# Register files #
##################
pushd $RPM_BUILD_ROOT%{goroot}
    find src/ -type d -a \( ! -name testdata -a ! -ipath '*/testdata/*' \) -printf '%%%dir %{goroot}/%p\n' >> $src_list
    find src/ ! -type d -a \( ! -ipath '*/testdata/*' -a ! -name '*_test.go' \) -printf '%{goroot}/%p\n' >> $src_list

    find bin/ pkg/ -type d -a ! -path '*_dynlink/*' -a ! -path '*_race/*' -printf '%%%dir %{goroot}/%p\n' >> $pkg_list
    find bin/ pkg/ ! -type d -a ! -path '*_dynlink/*' -a ! -path '*_race/*' -printf '%{goroot}/%p\n' >> $pkg_list

    find doc/ -type d -printf '%%%dir %{goroot}/%p\n' >> $docs_list
    find doc/ ! -type d -printf '%{goroot}/%p\n' >> $docs_list

    find misc/ -type d -printf '%%%dir %{goroot}/%p\n' >> $misc_list
    find misc/ ! -type d -printf '%{goroot}/%p\n' >> $misc_list

%if %{shared}
    mkdir -p %{buildroot}/%{_libdir}/
    mkdir -p %{buildroot}/%{golibdir}/
    for file in $(find .  -iname "*.so" ); do
        chmod 755 $file
        mv  $file %{buildroot}/%{golibdir}
        pushd $(dirname $file)
        ln -fs %{golibdir}/$(basename $file) $(basename $file)
        popd
        echo "%%{goroot}/$file" >> $shared_list
        echo "%%{golibdir}/$(basename $file)" >> $shared_list
    done

    find pkg/*_dynlink/ -type d -printf '%%%dir %{goroot}/%p\n' >> $shared_list
    find pkg/*_dynlink/ ! -type d -printf '%{goroot}/%p\n' >> $shared_list
%endif
    find test/ -type d -printf '%%%dir %{goroot}/%p\n' >> $tests_list
    find test/ ! -type d -printf '%{goroot}/%p\n' >> $tests_list
    find src/ -type d -a \( -name testdata -o -ipath '*/testdata/*' \) -printf '%%%dir %{goroot}/%p\n' >> $tests_list
    find src/ ! -type d -a \( -ipath '*/testdata/*' -o -name '*_test.go' \) -printf '%{goroot}/%p\n' >> $tests_list
    # this is only the zoneinfo.zip
    find lib/ -type d -printf '%%%dir %{goroot}/%p\n' >> $tests_list
    find lib/ ! -type d -printf '%{goroot}/%p\n' >> $tests_list
popd
# remove the doc Makefile
rm -rfv $RPM_BUILD_ROOT%{goroot}/doc/Makefile

# put binaries to bindir, linked to the arch we're building,
# leave the arch independent pieces in {goroot}
mkdir -p $RPM_BUILD_ROOT%{goroot}/bin/linux_%{gohostarch}
ln -sf %{goroot}/bin/go $RPM_BUILD_ROOT%{goroot}/bin/linux_%{gohostarch}/go
ln -sf %{goroot}/bin/gofmt $RPM_BUILD_ROOT%{goroot}/bin/linux_%{gohostarch}/gofmt

# ensure these exist and are owned
mkdir -p $RPM_BUILD_ROOT%{gopath}/src/github.com
mkdir -p $RPM_BUILD_ROOT%{gopath}/src/bitbucket.org
mkdir -p $RPM_BUILD_ROOT%{gopath}/src/code.google.com/p
mkdir -p $RPM_BUILD_ROOT%{gopath}/src/golang.org/x

# make sure these files exist and point to alternatives
rm -f $RPM_BUILD_ROOT%{_bindir}/go
ln -sf /etc/alternatives/go $RPM_BUILD_ROOT%{_bindir}/go
rm -f $RPM_BUILD_ROOT%{_bindir}/gofmt
ln -sf /etc/alternatives/gofmt $RPM_BUILD_ROOT%{_bindir}/gofmt

# gdbinit
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/gdbinit.d
cp -av %{SOURCE100} $RPM_BUILD_ROOT%{_sysconfdir}/gdbinit.d/golang.gdb

# prelink blacklist
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/prelink.conf.d
cp -av %{SOURCE101} $RPM_BUILD_ROOT%{_sysconfdir}/prelink.conf.d/golang.conf

%if %{fips}
# Quick fix for the rhbz#2014704
sed -i 's/const defaultGO_LDSO = `.*`/const defaultGO_LDSO = ``/' $RPM_BUILD_ROOT%{goroot}/src/internal/buildcfg/zbootstrap.go
%endif

%check
export GOROOT=$(pwd -P)
export PATH="$GOROOT"/bin:"$PATH"
cd src

# Add some sanity checks.
echo "GO VERSION:"
go version

echo "GO ENVIRONMENT:"
go env

export CC="gcc"
export CFLAGS="$RPM_OPT_FLAGS"
export LDFLAGS="$RPM_LD_FLAGS"
export GOAMD64=v3
export GOPPC64='power9'
%if !%{external_linker}
export GO_LDFLAGS="-linkmode internal"
%else
export GO_LDFLAGS="-extldflags '$RPM_LD_FLAGS'"
%endif
%if !%{cgo_enabled} || !%{external_linker}
export CGO_ENABLED=0
%endif

# make sure to not timeout
export GO_TEST_TIMEOUT_SCALE=2

export GO_TEST_RUN=""
%ifarch aarch64
  export GO_TEST_RUN="-run=!testshared"
%endif

echo "=== Start testing ==="
%if %{fail_on_tests}
    ./run.bash --no-rebuild -v -v -v -k $GO_TEST_RUN
    %if %{fips}
        echo "=== Running FIPS tests ==="
        # tested25519vectors needs network connectivity but it should be cover by
        # this test https://pkgs.devel.redhat.com/cgit/tests/golang/tree/regression/internal-testsuite/runtest.sh#n127

        # run tests with fips enabled.
        export GOLANG_FIPS=1
        export OPENSSL_FORCE_FIPS_MODE=1
        echo "=== Run all crypto test skipping tls ==="
        pushd crypto
          # run all crypto tests but skip tls, we will run fips specific tls tests later
          go test $(go list ./... | grep -v tls) -v -skip="TestEd25519Vectors|TestACVP"
          # check that signature functions have parity between boring and notboring
          CGO_ENABLED=0 go test $(go list ./... | grep -v tls) -v -skip="TestEd25519Vectors|TestACVP"
        popd
        echo "=== Run tls tests ==="
        # run all fips specific tls tests
        pushd crypto/tls
          go test -v -run "Boring"
        popd
    %endif
%else
    ./run.bash --no-rebuild -v -v -v -k || :
%endif
echo "=== End testing ==="
cd ..

%post bin
%{_sbindir}/update-alternatives --install %{_bindir}/go \
    go %{goroot}/bin/go 90 \
    --slave %{_bindir}/gofmt gofmt %{goroot}/bin/gofmt

%preun bin
if [ $1 = 0 ]; then
    %{_sbindir}/update-alternatives --remove go %{goroot}/bin/go
fi


%files
%license LICENSE PATENTS
# VERSION has to be present in the GOROOT, for `go install std` to work
%doc %{goroot}/VERSION
%dir %{goroot}/doc

# go files
%dir %{goroot}
%{goroot}/api/
%{goroot}/lib/time/

# ensure directory ownership, so they are cleaned up if empty
%dir %{gopath}
%dir %{gopath}/src
%dir %{gopath}/src/github.com/
%dir %{gopath}/src/bitbucket.org/
%dir %{gopath}/src/code.google.com/
%dir %{gopath}/src/code.google.com/p/
%dir %{gopath}/src/golang.org
%dir %{gopath}/src/golang.org/x

# gdbinit (for gdb debugging)
%{_sysconfdir}/gdbinit.d

# prelink blacklist
%{_sysconfdir}/prelink.conf.d

%files src -f go-src.list
%if %{race}
%ifarch x86_64
%exclude %{goroot}/src/runtime/race/internal/amd64v1/race_linux.syso
%exclude %{goroot}/src/runtime/race/internal/amd64v3/race_linux.syso
%else
%exclude %{goroot}/src/runtime/race/race_linux_%{gohostarch}.syso
%endif
%endif

%files docs -f go-docs.list

%files misc -f go-misc.list

%files tests -f go-tests.list

%files bin -f go-pkg.list
%{_bindir}/go
%{_bindir}/gofmt
%{goroot}/go.env
%{goroot}/bin/linux_%{gohostarch}/go
%{goroot}/bin/linux_%{gohostarch}/gofmt

%if %{shared}
%files shared -f go-shared.list
%endif

%files -n go-toolset

%if %{race}
%files race
%ifarch x86_64
%{goroot}/src/runtime/race/internal/amd64v1/race_linux.syso
%{goroot}/src/runtime/race/internal/amd64v3/race_linux.syso
%else
%{goroot}/src/runtime/race/race_linux_%{gohostarch}.syso
%endif
%endif

%changelog
%autochangelog
