Summary:	A content filtering web proxy
Name:		dansguardian
Version:	2.10.0.3
Release:	%mkrel 1
License:	GPL
Group:		System/Servers
URL:		http://www.dansguardian.org
Source0:	http://www.dansguardian.org/downloads/2/dansguardian-%{version}.tar.gz
Source1:	dansguardian.init
Source2:	languages.tar.bz2
Patch0:		dansguardian-mdv_conf.diff
BuildRequires:	zlib-devel
BuildRequires:	pcre-devel
BuildRequires:	clamav-devel >= 0.93
BuildRequires:	libesmtp-devel
Requires(post): rpm-helper
Requires(preun): rpm-helper
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires:	sendmail-command
%if %mdkversion >= 200810
Suggests:	webproxy webserver
%endif
Provides:	DansGuardian = %{version}-%{release}
Obsoletes:	DansGuardian
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
DansGuardian is a filtering proxy for Linux, FreeBSD, OpenBSD and Solaris.
It filters using multiple methods. These methods include URL and domain
filtering, content phrase filtering, PICS filtering, MIME filtering, file
extension filtering, POST filtering.

The content phrase filtering will check for pages that contain profanities
and phrases often associated with pornography and other undesirable content.
The POST filtering allows you to block or limit web upload.  The URL and
domain filtering is able to handle huge lists and is significantly faster
than squidGuard.

The filtering has configurable domain, user and ip exception lists.
SSL Tunneling is supported.

%prep

%setup -q -n %{name}-%{version}
%patch0 -p1

cp %{SOURCE1} %{name}.init

# fix path to the ipc files
perl -pi -e "s|\@localstatedir\@|/var/lib|g" %{name}.init

# mdv design
pushd data
    tar -jxf %{SOURCE2}
popd

%build
%serverbuild

%configure2_5x \
    --localstatedir=/var/lib \
    --enable-pcre=yes \
    --enable-clamav=yes \
    --enable-clamd=yes \
    --enable-icap=yes \
    --enable-kavd=no \
    --enable-commandline=yes \
    --enable-fancydm=yes \
    --enable-trickledm=yes \
    --enable-ntlm=yes \
    --enable-email=yes \
    --with-proxyuser=%{name} \
    --with-proxygroup=%{name} \
    --with-piddir=/var/run/%{name} \
    --with-logdir=/var/log/%{name} \
    --with-sysconfsubdir=%{name}

%make

%install
rm -rf %{buildroot}

install -d %{buildroot}%{_sysconfdir}/logrotate.d
install -d %{buildroot}%{_initrddir}
install -d %{buildroot}/var/log/%{name}
install -d %{buildroot}/var/run/%{name}
install -d %{buildroot}/var/www/cgi-bin
install -d %{buildroot}/var/lib/%{name}/tmp

%makeinstall_std

# cleanup
rm -rf %{buildroot}%{_datadir}/doc/dansguardian*

install -m0755 %{name}.init %{buildroot}%{_initrddir}/%{name}

cat << EOF > %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
/var/log/%{name}/access.log {
    create 644 %{name} %{name}
    rotate 5
    weekly
    sharedscripts
    prerotate
	service %{name} stop
    endscript
    postrotate
	service %{name} start
    endscript
}
EOF

install -m0755 data/dansguardian.pl %{buildroot}/var/www/cgi-bin/

# make sure this file is present
echo "localhost" >> %{buildroot}%{_sysconfdir}/%{name}/lists/exceptionfileurllist

# construct file lists
find %{buildroot}%{_sysconfdir}/%{name} -type d | \
    sed -e "s|%{buildroot}||" | sed -e 's/^/%attr(0755,root,root) %dir /' > %{name}.filelist

find %{buildroot}%{_sysconfdir}/%{name} -type f | grep -v "\.orig" | \
    sed -e "s|%{buildroot}||" | sed -e 's/^/%attr(0644,root,root) %config(noreplace) /' >> %{name}.filelist

cat > README.urpmi << EOF
Make sure to change your /etc/%{name}/%{name}.conf to reflect your own settings.
Special attention must be given to the port that the proxy server is listening to,
the port that %{name} will listen to and to the web url to the %{name}.pl cgi-script.

Author: Daniel Barron
daniel@jadeb.com
EOF

touch %{buildroot}/var/log/%{name}/access.log

# cleanup
rm -rf %{buildroot}%{_datadir}/%{name}/scripts

%pre
%_pre_useradd %{name} /var/lib/%{name} /bin/false

%preun
%_preun_service %{name}
if [ $1 = 0 ] ; then
    rm -f /var/log/%{name}/*
fi

%post
%create_ghostfile /var/log/%{name}/access.log %{name} %{name} 644
%_post_service %{name}

%postun
%_postun_userdel %{name}

%clean
rm -rf %{buildroot}

%files -f %{name}.filelist
%defattr(-,root,root)
%doc AUTHORS COPYING README README.urpmi
%doc doc/AuthPlugins doc/ContentScanners doc/DownloadManagers
%doc doc/FAQ doc/FAQ.html doc/Plugins
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%attr(0755,root,root) %{_initrddir}/%{name}
%attr(0755,root,root) %{_sbindir}/%{name}
%{_datadir}/%{name}
%attr(0755,root,root) /var/www/cgi-bin/%{name}.pl
%dir %attr(0755,%{name},%{name}) /var/log/%{name}
%dir %attr(0755,%{name},%{name}) /var/run/%{name}
%dir %attr(0755,%{name},%{name}) /var/lib/%{name}
%dir %attr(0755,%{name},%{name}) /var/lib/%{name}/tmp
%ghost %attr(0644,%{name},%{name}) /var/log/%{name}/access.log
%attr(0644,root,root) %{_mandir}/man8/*
