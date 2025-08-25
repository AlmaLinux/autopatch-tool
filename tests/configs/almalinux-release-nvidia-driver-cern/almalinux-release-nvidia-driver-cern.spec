Name:		almalinux-release-nvidia-driver
Summary:	AlmaLinux NVIDIA driver repository configuration
Version:	%{?rhel}
Release:	3%{?dist}
License:	GPL-2.0-only
URL:		https://almalinux.org/
ExclusiveArch:  x86_64 %{x86_64} %{arm64}
Source0:	almalinux-nvidia.repo
Source1:	nvidia-cuda.repo

Requires:       epel-release
Requires(post): epel-release
Provides:	almalinux-release-nvidia-driver = %{version}
Conflicts:	epel-nvidia


%description
DNF configuration for AlmaLinux NVIDIA driver repository


%prep
%ifarch x86_64_v2
sed -i "s/\$basearch/x86_64_v2/g" %{SOURCE0}
sed -i '/^mirrorlist=/ s|$|?arch=x86_64_v2|g' %{SOURCE0}
%endif
%ifarch aarch64
sed -i "s/\$basearch/sbsa/g" %{SOURCE1}
%endif

%if %{?rhel} == 9
sed -i "s/\$gpgkey/D42D0685.pub/g" %{SOURCE1}
%endif
%if %{?rhel} == 10
sed -i "s/\$gpgkey/CDF6BA43.pub/g" %{SOURCE1}
%endif

%install
install -D -m 644 %{SOURCE0} %{buildroot}%{_sysconfdir}/yum.repos.d/almalinux-nvidia.repo
install -D -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/yum.repos.d/nvidia-cuda.repo


%post
if [ -x /usr/bin/crb ]; then
  /usr/bin/crb enable
fi


%files
%config(noreplace) %{_sysconfdir}/yum.repos.d/almalinux-nvidia.repo
%{_sysconfdir}/yum.repos.d/nvidia-cuda.repo


%changelog
* Wed Aug 06 2025 Jonathan Wright <jonathan@almalinux.org> - %{?rhel}-3
- Update mirror URLs/names

* Mon Aug 04 2025 Jonathan Wright <jonathan@almalinux.org> - %{?rhel}-2
- Rebase to official NVIDIA CUDA repo

* Mon May 26 2025 Jonathan Wright <jonathan@almalinux.org> - %{?rhel}-1
- Initial release
