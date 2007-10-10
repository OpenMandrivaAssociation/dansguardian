Summary:	A content filtering web proxy
Name:		dansguardian
Version:	2.9.9.1
Release:	%mkrel 0
License:	GPL
Group:		System/Servers
URL:		http://www.dansguardian.org
Source0:	http://www.dansguardian.org/downloads/2/dansguardian-%{version}.tar.gz
Source1:	dansguardian.init
BuildRequires:	zlib-devel
BuildRequires:	pcre-devel
BuildRequires:	clamav-devel
BuildRequires:	libesmtp-devel
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires(pre):	squid
Requires:	sendmail-command
Requires:	webserver
Requires:	squid
Provides:	DansGuardian = %{version}-%{release}
Obsoletes:	DansGuardian
BuildRoot:	%{_tmppath}/%{name}-buildroot

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

cp %{SOURCE1} %{name}.init

%build
%serverbuild

%configure2_5x \
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
    --with-proxyuser=squid \
    --with-proxygroup=squid \
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

%makeinstall_std

install -m0755 %{name}.init %{buildroot}%{_initrddir}/%{name}

cat << EOF > %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
/var/log/%{name}/access.log {
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
    sed -e "s|%{buildroot}||" | sed -e 's/^/%attr(0755,squid,squid) %dir /' > %{name}.filelist

find %{buildroot}%{_sysconfdir}/%{name} -type f | grep -v "\.orig" | \
    sed -e "s|%{buildroot}||" | sed -e 's/^/%attr(0640,squid,squid) %config(noreplace) /' >> %{name}.filelist

cat > README.urpmi << EOF
Be sure to change your /etc/%{name}/%{name}.conf to reflect your own 
settings.
Special attention must be given to the port that squid listens on, 
the port that %{name} will listen to and to the web url to the
%{name}.pl cgi-script.

Author: Daniel Barron
daniel@jadeb.com
EOF

# cleanup
rm -rf %{_datadir}/%{name}/scripts

%preun
%_preun_service %{name}
if [ $1 = 0 ] ; then
    rm -f /var/log/%{name}/*
fi

%post
%_post_service %{name}
touch /var/log/%{name}/access.log
chown -R squid:squid /var/log/%{name} /var/run/%{name}
chmod -R u+rw /var/log/%{name}
chmod u+rwx /var/log/%{name}

%clean
rm -rf %{buildroot}

%files -f %{name}.filelist
%defattr(-,root,root)
%doc AUTHORS COPYING README README.urpmi
%attr(0644,squid,squid) %{_sysconfdir}/logrotate.d/%{name}
%attr(0755,root,root) %{_initrddir}/%{name}
%attr(0755,root,root) %{_sbindir}/%{name}
%{_datadir}/%{name}
%attr(0644,root,root) %{_mandir}/man8/*
%attr(0755,root,root) /var/www/cgi-bin/%{name}.pl
%attr(0755,squid,squid) /var/log/%{name}
%attr(0755,squid,squid) /var/run/%{name}
