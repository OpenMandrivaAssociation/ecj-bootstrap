%define bootstrap       0
%define ecj_bin         1
%define gcj_support     1
%define gccver          4.1.2
%if %{bootstrap}
%define gcj_support     0
%endif

# Redefine %jar so we don't need a jdk to build
%define jar %{_bindir}/fastjar

Summary:                Eclipse Compiler for Java
Name:                   ecj-bootstrap
Version:                3.2.2
Release:                %mkrel 1.1
Epoch:                  0
URL:                    http://www.eclipse.org/
Source0:                ftp://ftp.cse.buffalo.edu/pub/Eclipse/eclipse/downloads/drops/R-3.2.2-200702121330/ecjsrc.zip
Source1:                compilejdtcorewithjavac.xml
Source2:                compilejdtcore.xml
License:                CPL
Group:                  Development/Java
BuildRoot:              %{_tmppath}/%{name}-%{version}-root
Requires:               gcc-java >= 0:%{gccver}
%if !%{bootstrap}
BuildRequires:          ant
%endif
BuildRequires:          gcc-java = 0:%{gccver}
BuildRequires:          jpackage-utils
BuildRequires:          zip
Provides:               eclipse-ecj
%if !%{ecj_bin}
%if !%{gcj_support}
BuildArch:              noarch
%endif
%endif

%description
Ecj is the Java bytecode compiler of the Eclipse Project.

%prep
%setup -q -c -T
%{__install} -D -m 644 %{SOURCE0} jdtcoresrc/src/ecj.zip
%if !%{bootstrap}
%{__install} -D -m 644 %{SOURCE1} jdtcoresrc/compilejdtcorewithjavac.xml
%{__install} -D -m 644 %{SOURCE2} jdtcoresrc/compilejdtcore.xml
%{__perl} -pi -e 's/verbose="true"/verbose="\${javacVerbose}"/' jdtcoresrc/compilejdtcorewithjavac.xml jdtcoresrc/compilejdtcore.xml
%endif

%build
# Bootstrapping is 3 parts:
# 1. Build ecj with gcj -C
# 2. Build ecj with gcj-built ecj ("javac") using ant
# 3. Re-build ecj with output of 2 using ant

## 1. Build ecj with gcj -C
# Unzip the "stable compiler" source into a temp dir and build it.
# Note: we don't want to build the CompilerAdapter.
%{__mkdir_p} ecj-bootstrap-tmp
%{__unzip} -qq -d ecj-bootstrap-tmp jdtcoresrc/src/ecj.zip
%{__rm} ecj-bootstrap-tmp/org/eclipse/jdt/core/JDTCompilerAdapter.java

export CLASSPATH=

pushd ecj-bootstrap-tmp
for f in `%{_bindir}/find . -type f -name '*.java' | /bin/cut -c 3-`; do
  %{_bindir}/gcj -Wno-deprecated -I. -C $f
done
%{_bindir}/find -name '*.class' -or -name '*.properties' -or -name '*.rsc' | %{_bindir}/xargs -t %{jar} cf ../ecj-bootstrap.jar
popd

# Delete our modified ecj and restore the backup
%{__rm} -r ecj-bootstrap-tmp

%if !%{bootstrap}
%if %{gcj_support}
## 2. Build ecj
CLASSPATH=$ORIGCLASSPATH
export CLASSPATH=ecj-bootstrap.jar:$ORIGCLASSPATH
export OPT_JAR_LIST=:
%{ant} -buildfile jdtcoresrc/compilejdtcorewithjavac.xml \
       -DjavacFailOnError=true \
       -DjavacVerbose=false

%{__rm} ecj-bootstrap.jar

## 3. Use this ecj to rebuild itself
export CLASSPATH=`pwd`/jdtcoresrc/ecj.jar:$ORIGCLASSPATH
%{ant} -buildfile jdtcoresrc/compilejdtcore.xml \
       -DjavacFailOnError=true \
       -DjavacVerbose=false

%endif # gcj_support
%else
%{__mv} ecj-bootstrap.jar ecj.jar
%endif # !bootstrap

%install
%{__rm} -rf %{buildroot}

%{__install} -D -m 644 ecj.jar %{buildroot}%{_javadir}/eclipse-ecj.jar
(cd %{buildroot}%{_javadir} && %{__ln_s} eclipse-ecj.jar jdtcore.jar)
(cd %{buildroot}%{_javadir} && %{__ln_s} eclipse-ecj.jar ecj.jar)

%if %{gcj_support}
%{_bindir}/aot-compile-rpm
%endif

%if %{ecj_bin}
# Build and install ecj binary
%{__mkdir_p} %{buildroot}%{_bindir}
%if %{gcj_support}
  pushd %{buildroot}%{_libdir}/gcj/%{name}
  %{_bindir}/gcj -g -O2 --main=org.eclipse.jdt.internal.compiler.batch.Main \
    -Wl,-R,%{_libdir}/gcj/%{name} \
    eclipse-ecj.jar.so -o \
    %{buildroot}%{_bindir}/ecj
  popd
%else
  pushd %{buildroot}%{_javadir}
  %{_bindir}/gcj -g -O2 --main=org.eclipse.jdt.internal.compiler.batch.Main \
    -Wl,-R,%{_javadir} \
    eclipse-ecj.jar -o %{buildroot}%{_bindir}/ecj
  popd
%endif
%{__chmod} a+x %{buildroot}%{_bindir}/ecj
%endif

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(0644,root,root,0755)
%if %{ecj_bin}
%attr(0755,root,root) %{_bindir}/ecj
%endif
%{_javadir}/ecj.jar
%{_javadir}/eclipse-ecj.jar
%{_javadir}/jdtcore.jar
%if %{gcj_support}
%dir %{_libdir}/gcj/%{name}
%attr(-,root,root) %{_libdir}/gcj/%{name}/*
%endif


