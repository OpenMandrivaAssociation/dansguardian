%define build_clamav 0
%{?_with_clamav: %{expand: %%global build_clamav 1}}
%{?_without_clamav: %{expand: %%global build_clamav 0}}

%define AV_version 6.3.8

Summary:	A content filtering web proxy
Name:		dansguardian
Version:	2.8.0.6
Release:	%mkrel 1
License:	GPL
Group:		System/Servers
URL:		http://www.dansguardian.org
Source0:	http://www.%{name}.org/downloads/2/%{name}-%{version}.source.tar.bz2
Source1:	%{name}.init
Patch0:		%{name}-2.8.0.4-no-static-libz.diff
# (oe) http://www.harvest.com.br/asp/afn/dg.nsf
Patch3:		%{name}-2.8.0.4-antivirus-%{AV_version}.diff
BuildRequires:	zlib-devel
%if %{build_clamav}
BuildRequires:	clamav-devel libesmtp5-devel
%endif
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires(pre):	squid
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

You can build %{name} with some conditional build swithes;

(ie. use with rpm --rebuild):

--with[out] clamav	ClamAV support (disabled)

%if %{build_clamav}
This is DansGuardian with http://www.pcxperience.org Anti-Virus
Plugin v%{AV_version} built with ClamAV support. The Anti-Virus
patch is now maintained by Aecio F. Neto at:

http://www.harvest.com.br/asp/afn/dg.nsf
%endif

%prep

%setup -q -n %{name}-%{version}
%patch0 -p0

%if %{build_clamav}
%patch3 -p1
%endif

cp %{SOURCE1} %{name}.init

%build
%serverbuild

./configure \
    --installprefix=%{_prefix} \
    --bindir=%{_bindir}/ \
    --sysconfdir=%{_sysconfdir}/%{name}/ \
    --sysvdir=%{_initrddir}/ \
    --cgidir=/var/www/cgi-bin/ \
    --mandir=%{_mandir}/ \
    --logdir=/var/log/%{name}/ \
    --runas_usr=squid \
    --runas_grp=squid \
    --piddir=/var/run \
    --logrotatedir=%{_sysconfdir}/logrotate.d/

%make OPTIMISE="$CFLAGS" WARNING="-Wall -Wno-deprecated"

%install
rm -rf %{buildroot}

# don't fiddle with the initscript!
export DONT_GPRINTIFY=1

install -d %{buildroot}%{_sbindir}
install -d %{buildroot}%{_mandir}/man8
install -d %{buildroot}%{_sysconfdir}/%{name}
install -d %{buildroot}%{_sysconfdir}/logrotate.d
install -d %{buildroot}%{_initrddir}
install -d %{buildroot}/var/log/%{name}
install -d %{buildroot}/var/spool/MailScanner/quarantine
install -d %{buildroot}/var/www/cgi-bin

install -d bin
PATH=$PWD/bin:$PATH
ln -sf /bin/true bin/chown

make install INSTALLPREFIX=%{buildroot} CHKCONF=nowhere
mv %{buildroot}%{_bindir}/* %{buildroot}%{_sbindir}
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

%preun
%_preun_service %{name}
if [ $1 = 0 ] ; then
    rm -f /var/log/%{name}/*
fi

%post
%_post_service %{name}
touch /var/log/%{name}/access.log
chown -R squid:squid /var/log/%{name}
chmod -R u+rw /var/log/%{name}
chmod u+rwx /var/log/%{name}

%clean
rm -rf %{buildroot}

%files -f %{name}.filelist
%defattr(-,root,root)
%doc README INSTALL LICENSE README.urpmi
%attr(0644,squid,squid) %{_sysconfdir}/logrotate.d/%{name}
%attr(0755,root,root) %{_initrddir}/%{name}
%attr(0755,root,root) %{_sbindir}/%{name}
%attr(0644,root,root) %{_mandir}/man8/*
%attr(0755,root,root) /var/www/cgi-bin/%{name}.pl
%attr(0755,apache,apache) /var/spool/MailScanner/quarantine
%attr(0755,squid,squid) /var/log/%{name}
