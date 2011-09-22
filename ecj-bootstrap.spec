Summary:	Eclipse Compiler for Java
Name:		ecj-bootstrap
Version:	3.4.2
Release:	1
URL:		http://www.eclipse.org
License:	EPL
Group:		Development/Java
Source0:	http://download.eclipse.org/eclipse/downloads/drops/R-%{version}-%{qualifier}/ecjsrc-%{version}.zip
Source1:	ecj.sh.in
# Use ECJ for GCJ
# cvs -d:pserver:anonymous@sourceware.org:/cvs/rhug \
# export -r eclipse_r34_1 eclipse-gcj
# tar cjf ecj-gcj.tar.bz2 eclipse-gcj
Source2:	ecj-gcj.tar.bz2
Source3:	http://repo2.maven.org/maven2/org/eclipse/jdt/core/3.3.0-v_771/core-3.3.0-v_771.pom
BuildArch:      noarch
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

BuildRequires:	gcc-java >= 4.0.0
BuildRequires:	fastjar
BuildRequires:	java-1.5.0-gcj-devel
BuildRequires:	java-gcj-compat
Requires:	libgcj >= 4.0.0
Requires(post):	java-gcj-compat
Requires(postun): java-gcj-compat
Provides:	eclipse-ecj = 1:%{version}-%{release}

# Always generate debug info when building RPMs (Andrew Haley)
Patch0:		ecj-rpmdebuginfo.patch
Patch1:		ecj-defaultto1.5.patch
Patch2:		ecj-generatedebuginfo.patch

%description
ECJ is the Java bytecode compiler of the Eclipse Platform.  It is also known as
the JDT Core batch compiler.

%prep
%setup -q -c
%patch0 -p1
%patch1 -p1
%patch2 -p1

cp %{SOURCE3} pom.xml
# Use ECJ for GCJ's bytecode compiler
tar jxf %{SOURCE2}
mv eclipse-gcj/org/eclipse/jdt/internal/compiler/batch/GCCMain.java \
  org/eclipse/jdt/internal/compiler/batch/
cat eclipse-gcj/gcc.properties >> \
  org/eclipse/jdt/internal/compiler/batch/messages.properties
rm -rf eclipse-gcj

# Remove bits of JDT Core we don't want to build
rm -r org/eclipse/jdt/internal/compiler/tool
rm -r org/eclipse/jdt/internal/compiler/apt

# JDTCompilerAdapter isn't used by the batch compiler
rm -f org/eclipse/jdt/core/JDTCompilerAdapter.java

%build
for f in `find -name '*.java' | cut -c 3- | LC_ALL=C sort`; do
    gcj -Wno-deprecated -C $f
done
find -name '*.class' -or -name '*.properties' -or -name '*.rsc' |	\
    xargs fastjar cf ecj-%{version}.jar

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_javadir}
cp -a *.jar %{buildroot}%{_javadir}/ecj-%{version}.jar
pushd %{buildroot}%{_javadir}
ln -s ecj-%{version}.jar ecj.jar
ln -s ecj-%{version}.jar eclipse-ecj-%{version}.jar
ln -s eclipse-ecj-%{version}.jar eclipse-ecj.jar
ln -s ecj-%{version}.jar jdtcore.jar
popd
# Install the ecj wrapper script
install -p -D -m0755 %{SOURCE1} $RPM_BUILD_ROOT%{_bindir}/ecj
sed --in-place "s:@JAVADIR@:%{_javadir}:" $RPM_BUILD_ROOT%{_bindir}/ecj

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%doc about.html
%{_bindir}/ecj
%{_javadir}/ecj*.jar
%{_javadir}/eclipse-ecj*.jar
%{_javadir}/jdtcore.jar
