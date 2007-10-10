%define build_clamav 0
%{?_with_clamav: %{expand: %%global build_clamav 1}}
%{?_without_clamav: %{expand: %%global build_clamav 0}}

%define new_name dansguardian
%define AV_version 6.3.8

Summary:	A content filtering web proxy
Name:		DansGuardian
Version:	2.8.0.6
Release:	%mkrel 4
License:	GPL
Group:		System/Servers
URL:		http://www.dansguardian.org
Source0:	http://www.dansguardian.org/downloads/2/dansguardian-%{version}.source.tar.bz2
Source1:	dansguardian.init
Patch0:		dansguardian-2.8.0.4-no-static-libz.diff
# (oe) http://www.harvest.com.br/asp/afn/dg.nsf
Patch3:		dansguardian-2.8.0.4-antivirus-%{AV_version}.diff
BuildRequires:	zlib-devel
%if %{build_clamav}
BuildRequires:	clamav-devel libesmtp5-devel
%endif
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires(pre):	squid
Requires:	webserver
Requires:	squid
BuildRoot:	%{_tmppath}/%{new_name}-buildroot

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

%setup -q -n dansguardian-%{version}
%patch0 -p0
%if %{build_clamav}
%patch3 -p1
%endif

cp %{SOURCE1} dansguardian.init

%build

export CFLAGS="%{optflags}"
export CXXFLAGS="%{optflags}"

./configure \
    --installprefix=%{_prefix} \
    --bindir=%{_bindir}/ \
    --sysconfdir=%{_sysconfdir}/%{new_name}/ \
    --sysvdir=%{_initrddir}/ \
    --cgidir=/var/www/cgi-bin/ \
    --mandir=%{_mandir}/ \
    --logdir=/var/log/%{new_name}/ \
    --runas_usr=squid \
    --runas_grp=squid \
    --piddir=/var/run \
    --logrotatedir=%{_sysconfdir}/logrotate.d/

%make OPTIMISE="%{optflags}" WARNING="-Wall -Wno-deprecated"

%install
rm -rf %{buildroot}

# don't fiddle with the initscript!
export DONT_GPRINTIFY=1

install -d %{buildroot}%{_sbindir}
install -d %{buildroot}%{_mandir}/man8
install -d %{buildroot}%{_sysconfdir}/%{new_name}
install -d %{buildroot}%{_sysconfdir}/logrotate.d
install -d %{buildroot}%{_initrddir}
install -d %{buildroot}/var/log/dansguardian
install -d %{buildroot}/var/spool/MailScanner/quarantine
install -d %{buildroot}/var/www/cgi-bin

install -d bin
PATH=$PWD/bin:$PATH
ln -sf /bin/true bin/chown

make install INSTALLPREFIX=%{buildroot} CHKCONF=nowhere
mv %{buildroot}%{_bindir}/* %{buildroot}%{_sbindir}
install -m0755 dansguardian.init %{buildroot}%{_initrddir}/dansguardian

cat << EOF > %{buildroot}%{_sysconfdir}/logrotate.d/dansguardian
/var/log/dansguardian/access.log {
    rotate 5
    weekly
    sharedscripts
    prerotate
	service dansguardian stop
    endscript
    postrotate
	service dansguardian start
    endscript
}
EOF

# construct file lists
find %{buildroot}%{_sysconfdir}/%{new_name} -type d | \
    sed -e "s|%{buildroot}||" | sed -e 's/^/%attr(0755,squid,squid) %dir /' > %{name}.filelist

find %{buildroot}%{_sysconfdir}/%{new_name} -type f | grep -v "\.orig" | \
    sed -e "s|%{buildroot}||" | sed -e 's/^/%attr(0640,squid,squid) %config(noreplace) /' >> %{name}.filelist

cat > README.urpmi << EOF
Be sure to change your /etc/dansguardian/dansguardian.conf to reflect your own 
settings.
Special attention must be given to the port that squid listens on, 
the port that dansguardian will listen to and to the web url to the
dansguardian.pl cgi-script.

Author: Daniel Barron
daniel@jadeb.com
EOF

%preun
%_preun_service dansguardian
if [ $1 = 0 ] ; then
    rm -f /var/log/dansguardian/*
fi

%post
%_post_service dansguardian
touch /var/log/dansguardian/access.log
chown -R squid:squid /var/log/dansguardian
chmod -R u+rw /var/log/dansguardian
chmod u+rwx /var/log/dansguardian

%clean
rm -rf %{buildroot}

%files -f %{name}.filelist
%defattr(-,root,root)
%doc README INSTALL LICENSE README.urpmi
%attr(0644,squid,squid) %{_sysconfdir}/logrotate.d/dansguardian
%attr(0755,root,root) %{_initrddir}/dansguardian
%attr(0755,root,root) %{_sbindir}/%{new_name}
%attr(0644,root,root) %{_mandir}/man8/*
%attr(0755,root,root) /var/www/cgi-bin/dansguardian.pl
%attr(0755,apache,apache) /var/spool/MailScanner/quarantine
%attr(0755,squid,squid) /var/log/dansguardian


