#  lets support clamav only when backpoting by default
%if %mdkversion < 200910
	%define clamav 1
%else
	%define clamav 0
%endif
# commandline overrides:
# rpm -ba|--rebuild --with 'xxx'
%{?_with_clamav: %{expand: %%global clamav 1}}
%{?_without_clamav: %{expand: %%global clamav 0}}


Summary:	A content filtering web proxy
Name:		dansguardian
Version:	2.10.1.1
Release:	%mkrel 10
License:	GPL
Group:		System/Servers
URL:		http://www.dansguardian.org
Source0:	http://www.dansguardian.org/downloads/2/dansguardian-%{version}.tar.gz
Source1:	dansguardian.init
Source2:	languages.tar.bz2
Source10:	bigblacklist.tar.gz
Source11:	badwords.zip
Source12:	new.zip
Source13:	extrem.zip
Patch0:		dansguardian-mdv_conf.diff
Patch1: 	dansguardian-2.10.0.3-gcc44.patch
Patch2:		dansguardian-2.10.1.1-gcc46.patch
BuildRequires:	zlib-devel
BuildRequires:	pcre-devel
BuildRequires:	libesmtp-devel
%if %{clamav}
BuildRequires:  clamav-devel
%endif

Requires(post): rpm-helper
Requires(preun): rpm-helper
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires:	sendmail-command
%if %mdkversion >= 200810
Suggests:	webproxy webserver c-icap-server
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
#tar xf %{SOURCE10}
#unzip -xo %{SOURCE11}
#unzip -xo %{SOURCE12}
#unzip -xo %{SOURCE13} -d extrem

%setup -q -n %{name}-%{version}
%patch0 -p1
%patch1 -p1
%patch2 -p0
tar -C configs/lists/ -xf %{SOURCE10} 
unzip -xo %{SOURCE11} -d configs/lists/phraselists/
unzip -xo %{SOURCE12} -d configs/lists/phraselists/
unzip -xo %{SOURCE13} -d configs/lists/phraselists/extremism

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
%if %{clamav}
    --enable-clamav=yes \
%else
    --enable-clamav=no \
%endif
    --enable-clamd=yes \
    --enable-icap=yes \
    --enable-kavd=no \
    --enable-commandline=yes \
    --enable-fancydm=yes \
    --enable-trickledm=yes \
    --enable-ntlm=yes \
    --enable-email=yes \
    --enable-orig-ip=yes \
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


%changelog
* Sat Aug 20 2011 Александр Казанцев <kazancas@mandriva.org> 2.10.1.1-9mdv2011.0
+ Revision: 695843
+ rebuild (emptylog)

* Sun Aug 14 2011 Sergey Zhemoitel <serg@mandriva.org> 2.10.1.1-8
+ Revision: 694524
- release 8. add phraselists russian (koi8,utf8)

* Tue May 03 2011 Funda Wang <fwang@mandriva.org> 2.10.1.1-7
+ Revision: 664020
- fix build with gcc 4.6

  + Oden Eriksson <oeriksson@mandriva.com>
    - mass rebuild

* Thu Dec 02 2010 Oden Eriksson <oeriksson@mandriva.com> 2.10.1.1-6mdv2011.0
+ Revision: 604774
- rebuild

* Sat May 01 2010 Luis Daniel Lucio Quiroz <dlucio@mandriva.org> 2.10.1.1-5mdv2010.1
+ Revision: 541501
- Some minor fixes to allow DG be backported

* Fri Apr 30 2010 Luis Daniel Lucio Quiroz <dlucio@mandriva.org> 2.10.1.1-4mdv2010.1
+ Revision: 541335
- Clamav support optional with --with-clamav when compilling
- icapd as suggest

* Mon Dec 28 2009 Eugeni Dodonov <eugeni@mandriva.com> 2.10.1.1-2mdv2010.1
+ Revision: 483004
- Fixed error messages when stopping service (#56496).

* Wed Jun 10 2009 Oden Eriksson <oeriksson@mandriva.com> 2.10.1.1-1mdv2010.0
+ Revision: 384799
- 2.10.1.1
- rediffed the patches
- enable the originalip code but disable it in the config. note that
  this is an attempt to fix CVE-2009-0801 but beware of the consequenses
  using it. read more about it in the documentation.

  + Christophe Fergeau <cfergeau@mandriva.com>
    - fix build with gcc 4.4

* Thu Feb 26 2009 Oden Eriksson <oeriksson@mandriva.com> 2.10.0.3-2mdv2009.1
+ Revision: 345317
- nuke the clamav dep

* Wed Feb 18 2009 Jérôme Soyer <saispo@mandriva.org> 2.10.0.3-1mdv2009.1
+ Revision: 342303
- New upstream release

* Mon Dec 08 2008 Oden Eriksson <oeriksson@mandriva.com> 2.10.0.2-1mdv2009.1
+ Revision: 311827
- 2.10.0.2

* Wed Nov 05 2008 Oden Eriksson <oeriksson@mandriva.com> 2.10.0.1-1mdv2009.1
+ Revision: 300106
- 2.10.0.1

* Wed Oct 15 2008 Oden Eriksson <oeriksson@mandriva.com> 2.10-1mdv2009.1
+ Revision: 293891
- 2.10

* Sun Oct 12 2008 Oden Eriksson <oeriksson@mandriva.com> 2.9.9.7-2mdv2009.1
+ Revision: 292773
- fix #44607 (Wrong path in configuration file preventing dansguardian from starting)

* Fri Sep 05 2008 Oden Eriksson <oeriksson@mandriva.com> 2.9.9.7-1mdv2009.0
+ Revision: 281106
- 2.9.9.7

* Thu Sep 04 2008 Oden Eriksson <oeriksson@mandriva.com> 2.9.9.4-4mdv2009.0
+ Revision: 280491
- rebuild against new clamav libs

  + Thierry Vignaud <tv@mandriva.org>
    - rebuild early 2009.0 package (before pixel changes)

  + Pixel <pixel@mandriva.com>
    - adapt to %%_localstatedir now being /var instead of /var/lib (#22312)

* Mon May 12 2008 Oden Eriksson <oeriksson@mandriva.com> 2.9.9.4-2mdv2009.0
+ Revision: 206226
- fix docs (borks on cs4 builds)

* Mon May 12 2008 Oden Eriksson <oeriksson@mandriva.com> 2.9.9.4-1mdv2009.0
+ Revision: 206122
- 2.9.9.4
- drop the clamav-0.93 patch, better fix upstream
- revert the "conform to the 2008 specs (don't start the services per
  default)" changes and let this be handled some other way...

* Thu Apr 17 2008 Oden Eriksson <oeriksson@mandriva.com> 2.9.9.3-1mdv2009.0
+ Revision: 195356
- 2.9.9.3
- make it compile against clamav-0.93

* Thu Mar 27 2008 Oden Eriksson <oeriksson@mandriva.com> 2.9.9.2-4mdv2008.1
+ Revision: 190729
- fix path to clamd socket in P0 (anne)

* Wed Mar 26 2008 Oden Eriksson <oeriksson@mandriva.com> 2.9.9.2-3mdv2008.1
+ Revision: 190342
- added new css html design from anne

* Mon Feb 18 2008 Oden Eriksson <oeriksson@mandriva.com> 2.9.9.2-2mdv2008.1
+ Revision: 171283
- added "Suggests: webproxy webserver"
- added P0 to set some defaults
- fixed the initscript
- run it under the dansguardian uid/gid
- reworked bits and pieces

* Sun Jan 27 2008 Oden Eriksson <oeriksson@mandriva.com> 2.9.9.2-1mdv2008.1
+ Revision: 158758
- 2.9.9.2
- misc spec file fixes
- added lsm headers

  + Olivier Blin <blino@mandriva.org>
    - restore BuildRoot

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request

* Thu Oct 11 2007 Oden Eriksson <oeriksson@mandriva.com> 2.9.9.1-1mdv2008.1
+ Revision: 96988
- bump release

* Wed Oct 10 2007 Oden Eriksson <oeriksson@mandriva.com> 2.9.9.1-0mdv2008.1
+ Revision: 96889
- 2.9.9.1

* Wed Oct 10 2007 Oden Eriksson <oeriksson@mandriva.com> 2.8.0.6-1mdv2008.1
+ Revision: 96869
- lowercasing the package name
- lowercase the package name


* Wed Mar 07 2007 Oden Eriksson <oeriksson@mandriva.com> 2.8.0.6-4mdv2007.0
+ Revision: 134421
- Import DansGuardian

* Sun Jul 30 2006 Oden Eriksson <oeriksson@mandriva.com> 2.8.0.6-4mdv2007.0
- rebuild

* Tue May 02 2006 Oden Eriksson <oeriksson@mandriva.com> 2.8.0.6-3mdk
- fix the initscript (S1) and fix #22229 (thanks misc and spturtle)

* Sat Apr 08 2006 Oden Eriksson <oeriksson@mandriva.com> 2.8.0.6-2mdk
- use a new clever initscript (S1) and fix #19399

* Mon Aug 15 2005 Oden Eriksson <oeriksson@mandriva.com> 2.8.0.6-1mdk
- 2.8.0.6 (Major bugfixes)
- fix deps
- drop the gcc4 patch (P1), it's implemented upstream

* Sat Jun 18 2005 Oden Eriksson <oeriksson@mandriva.com> 2.8.0.4-2mdk
- gcc4 fix (Frederic Lepied)
- use the %%mkrel macro
- require webserver instead of explicitly apache
- drop the requirement for perl-Mail-Sender and perl-devel
- re-added the clamav support but with a twist (P3)

* Sun Jun 12 2005 Oden Eriksson <oeriksson@mandriva.com> 2.8.0.4-1mdk
- 2.8.0.4
- drop upstream applied patches
- rediffed P0

* Wed Mar 30 2005 Frederic Lepied <flepied@mandrakesoft.com> 2.7.7.8-3mdk
- fixed some rpmlint reports
- parallel build
- rebuild to fix logrotate entry (bug #13729)

* Fri Jun 11 2004 Florin <florin@mandrakesoft.com> 2.7.7.8-2mdk
- add dan moinescu patches (perf improvement, etc)
- add the mad3 patch (clamav antivirus, etc)
- integrate the no-static-libz patch in mad3 for the moment

* Fri Jun 04 2004 Frederic Lepied <flepied@mandrakesoft.com> 2.7.7.8-1mdk
- 2.7.7-8
- removed patch0 (integrated upstream)

