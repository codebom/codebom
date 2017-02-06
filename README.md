[![Join the chat at https://gitter.im/codebom/codebom](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/codebom/codebom?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![Build Status](https://travis-ci.org/codebom/codebom.svg?branch=master)](https://travis-ci.org/codebom/codebom)
[![codecov.io](http://codecov.io/github/codebom/codebom/coverage.svg?branch=master)](http://codecov.io/github/codebom/codebom?branch=master)

CodeBOM
===

CodeBOM is a command-line tool that can scan for or verify software licensing
declarations and visualize their implications. Its purpose is to help
organizations leverage open source software. CodeBOM helps engineers to
understand the implications of incorporating open source components into their
products before requesting legal approval to distribute them. An engineering
team armed with CodeBOM is one looking to maximize use of open source while
minimizing time spent in the release pipeline.

To use CodeBOM, one creates a BOM file that describes the relationships between
a product's software components. The BOM author declares which directories
represent software components, the license each is distributed under, which
components are product dependencies, and which are used only for development.
One then uses the command-line tool `codebom` to verify that those declarations
are consistent with the codebase.

With a verified BOM in hand, downstream teams may use the declarations in
different ways. A legal team may use them to ensure licensing terms are in
compliance before distribution. A security team, on the other hand, may use
code origin declarations to detect known security vulnerabilities.

![bombuilding101](doc/bombuilding101.png?raw=true)

CodeBOM includes a set of subcommands, `scan`, `verify` and `graph`. How you
use the subcommands will depend on what source code management tools you use.
If you use a package manager to download dependencies and build with a
traditional `configure && make && make install`, then your `configure` script
might use the data from the package manager to generate a BOM automatically. In
this case, your BOM would be ready to ship downstream immediately and
CodeBOM's `scan` and `verify` commands would only be useful as means to test
your `configure` script. If, on the other hand, your process is to copy
dependencies into your version control system (or are concerned others have),
then you can use `codebom scan` to help you detect missing declarations and
`codebom verify` to ensure all declarations are kept up to date.


Installation
===

Use Python's `pip3` to install the latest release of CodeBOM from PyPI:

```bash
$ pip3 install codebom
```

To use the `codebom graph` command, install 'graphviz' and afterward, ensure `dot`
is in the system `PATH`.


Ubuntu
---

```bash
$ sudo apt-get install graphviz
```

OS X
---

```bash
$ brew install graphviz
```


Usage
===

```
usage: codebom [-h] [--version] [-f FILE] {scan,verify,graph} ...

Validate a Bill of Materials

positional arguments:
  {scan,verify,analyze,graph}
    scan                Scan the codebase for missing declarations
    verify              Verify declarations are consistent with the codebase
    analyze             Analyze potential implications of the declarations
    graph               Graph license dependencies

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -f FILE
```

Sample Bill of Materials `.bom.yaml`:

```yaml
license: AllRightsReserved
license-file: LICENSE
dependencies:
  - root: lib/gitpython
    origin: https://github.com/gitpython-developers/GitPython/archive/0.3.6.tar.gz
    license: BSD-3-Clause
    license-file: LICENSE
development-dependencies:
  - setup.py
  - lib/pytest
```


Tutorial
===

The simplest `.bom.yaml` file is an empty file. It tells CodeBOM that
the directory containing `.bom.yaml` is the root directory and that
all code in that directory and its subdirectories contain proprietary
code. The following is equivalent to an empty `.bom.yaml`.

```yaml
root: .
```

When you run `codebom scan`, it traverses the directory structure in search
of evidence that the codebase is inconsistent with what has been declared
in the `.bom.yaml`. If `codebom` encounters a `LICENSE` file, for instance,
it will report an error and return a nonzero exit code.

```bash
$ touch .bom.yaml
$ touch LICENSE
$ codebom scan
.bom.yaml:1:1: error: Undeclared license file 'LICENSE' in directory '.'
```

Declare the license file and try again:

```bash
$ echo 'license-file: LICENSE' >> .bom.yaml
$ codebom scan
```

No output. In Unix tradition, that translates to Great Success!

Now let's break it again.

```bash
$ mkdir -p foss
$ touch foss/LICENSE
$ codebom scan
.bom.yaml:1:1: error: Undeclared license file 'foss/LICENSE' in directory '.'
```

Declare it and try again:

```bash
$ echo 'dependencies:' >> .bom.yaml
$ echo '  - root: foss' >> .bom.yaml
$ echo '    license-file: LICENSE' >> .bom.yaml
$ echo '    license: GPL-3.0' >> .bom.yaml
$ codebom scan
```

Next, to verify the declarations are consistent with each other and the
filesystem.

```
$ codebom verify
.bom.yaml:2:10: warning: The license 'Unknown' may be incompatible with the
license 'GPL-3.0' in 'foss'. If this dependency is used only for development,
move it to the 'development-dependencies' section.
```

To fix this, either declare a compatible license or move the dependency to the
'development-dependencies'.

```yaml
development-dependencies:
  - root: foss
    license-file: LICENSE
    license: GPL-3.0
```

CodeBOM operates under the assumption we are verifying a binary distribution,
and therefore doesn't need to know the license of development dependencies used
to generate it - just that those directories can safely be ignored. CodeBOM will
only use the license information to verify source distributions, which can be
specified by adding the `--source-distribution` flag.

Wrapping up, a minimal BOM for the project above looks like this:

```yaml
license-file: LICENSE
license: AllRightsReserved
development-dependencies:
  - foss
```

The root directory contains two files, a `.bom.yaml` and a `LICENSE` file
stating this is proprietary software. The `foss` directory contains a
GPL `LICENSE` file, but is ignored by CodeBOM because the `foss` directory
is declared as a tool.


Tucking away the BOM
---

By default, CodeBOM looks for a file `.bom.yaml` in the current directory.
To specify a different location, use the `-f` flag. CodeBOM will interpret
the file from the directory containing that file.

Alternatively, to direct CodeBOM to a BOM at a different location, use
a path to a BOM file anywhere you might declare the contents for a
directory.

```yaml
qosp/codebom/bom.yaml
```

Component BOMs
---

BOMs may reference other BOMs. In the `dependencies` or
`development-dependencies` section, CodeBOM will look for a `.bom.yaml` file in
the `root` directory.

```yaml
dependencies:
  - src/lua
```

Or specify the BOM explicitly:

```yaml
dependencies:
  - src/lua/.bom.yaml
```

If `src/lua` contains the following BOM:

```yaml
license: MIT
```

Then CodeBOM can generate a single merged BOM by specifying an output file:

```bash
$ codebom verify -o my-lua-app.yaml
$ cat my-lua-app.yaml
--- # Bill of Materials
license: Unknown
dependencies:
  - root: src/lua
    license: MIT
```

Commands
===

codebom scan
---

The `scan` command reads a BOM and traverses its `root` directory and the `root`
directory of dependencies in the hopes of discovering missing declarations. It
will not traverse any dependency under `development-dependencies` unless the
`--source-distribution` flag is added. Likewise, it will not traverse component
BOMs unless the `--recursive` flag is added.

When the `--add` flag is present, the `scan` command can be used to generate
BOM files. It can generate a new BOM or start from an existing one. Rather than
reporting an error when it discovers a missing declaration, it adds the
declaration to a copy of the BOM. The resulting BOM is then written to the file
specified by the `-o` flag, which defaults to stdout. CodeBOM attempts to mimic
handwritten BOMs by coalescing missing declarations. To turn off automatic
coalescing, add `--coalesce=none`.

```
usage: codebom scan [-h] [--source-distribution] [--recursive] [--add]
                    [--coalesce {all,none}] [-o FILE]

optional arguments:
  -h, --help            show this help message and exit
  --source-distribution
  --recursive, -r       Recurse into components
  --add, -a             Add missing declarations to output
  --coalesce {all,none} Merge declarations
  -o FILE
```


codebom verify
---

The `verify` command attempts to find contradictions in a BOM's declarations.
For example, if the user declares `license: MIT`, then `codebom verify` may
inspect the file at `license-file` to ensure its text is similar to the license
template defined by [SPDX](http://spdx.org/licenses/index.html). By default, the
`verify` command will not access the network to do its verification. To check
that the contents of the `origin` URI matches the contents of the `root`
directory, use the `--check-origins=contents` flag. To check only that the
`origin` URI is valid network endpoint, use `--check-origins=uri`.

```
usage: codebom verify [-h] [--source-distribution] [-o FILE]
                      [--check-origins {uri,contents}]

optional arguments:
  -h, --help            show this help message and exit
  --source-distribution
  -o FILE
  --check-origins {uri,contents}
```

codebom analyze
---

The `analyze` command attempts to report the implications of the BOM's
declarations. For instance, if a project depends on another with a
more restrictive license and no licensees are declared, it will
output a message telling you there may be license conflict. The
`analyze` command is the textual counterpart to the `graph` command.

```
usage: codebom analyze [-h] [--source-distribution] [-o FILE]

optional arguments:
  -h, --help            show this help message and exit
  --source-distribution
  -o FILE
```

codebom graph
---

The `graph` command can be used to visualize the dependency graph and how
license terms may be inferred. It colors *tainted* nodes red, as well as
all edges from the top node down to the node that introduced the potential
licensing conflict.

```
usage: codebom graph [-h] [--source-distribution] [-o FILE]

optional arguments:
  -h, --help            show this help message and exit
  --source-distribution
  -o FILE
```

In the [topsecret example](examples/topsecret), we can see how declaring
`development-dependencies` tells CodeBOM not to worry about a license conflict
in the context of a binary distribution.

```bash
$ codebom -f examples/topsecret/.bom.yaml graph -o topsecret-bindist.png
```

![topsecret-bindist](doc/topsecret-bindist.png?raw=true)

Running the same command again but with the `--source-distribution` flag, we
can see how license terms can reach up to potentially derivative works.

```bash
$ codebom -f examples/topsecret/.bom.yaml graph --source-distribution -o topsecret-srcdist.png
```

![topsecret-srcdist](doc/topsecret-srcdist.png?raw=true)



BOM Format
===

A BOM is a YAML dictionary containing *declarations* that describe a software
component.

```antlr
bom           : declaration* ;

declaration   : origin
              | root-matches-origin
              | license
              | license-file
              | root
              | files
              | name
              | copyright-holders
              | licensees
              | dependencies
              | development-dependencies ;
```

origin
---

If you specify an `origin` URI, CodeBOM will download it and verify its contents
match the files in the `root`. If the URI points to a file, CodeBOM will
verify `root` points to a file as well and the file contents match. If the
files in `root` are from a subdirectory of `origin`, use a URI fragment to tell
CodeBOM the path to the files that match those in `root`.

```yaml
--- # Bill of Materials
dependencies:
  - root: lua/lua-5.3.0
    origin: http://www.lua.org/ftp/lua-5.3.0.tar.gz#lua-5.3.0
    license: MIT
    license-file: doc/readme.html
  - root: sha1
    files: [sha1.c]
    license-file: sha1.c
    origin: http://downloads.sourceforge.net/project/jbig2dec/jbig2dec/0.11/jbig2dec-0.11.tar.gz#jbig2dec-0.11
    license: PublicDomain
    root-matches-origin: false
```

* type: `string | null`
* default: `null`


root-matches-origin
---

Setting the `root-matches-origin` property to `false` tells CodeBOM not to expect the file
contents to match. It exists so that you can *always* declare an `origin` for
your open source dependencies.

* type: `bool | null`
* default: `null`


license
---

The `license` declaration may be an Identifier found at [SPDX Licenses](https://spdx.org/licenses/).
If the code is in the public domain, declare it 'PublicDomain'. If it is
proprietary code, declare it 'AllRightsReserved'.  If the license is not listed
at spdx.org or you are not sure what the license is, declare it as `Unknown`.

* type: `string | null`
* default: `null`


license-file
---

The path to the license file relative to the `root` declaration.

* type: `filepath | null`
* default: `null`


root
---

The parent directory of all additonal declartions. It may be a path relative to
the BOM file or an absolute path.  If a dependency also specificies a root, it
will be relative to the parent's root directory.  For example:

```yaml
--- myproject/bom.yaml
root: foo
license-file: LICENSE.txt
dependencies:
  - root: bar
    license-file: license.md
```

```bash
$ codebom -f myproject/bom.yaml
```

CodeBOM will expect to find `LICENSE.txt` at `myproject/foo/LICENSE.txt` and
`license.md` at `myproject/foo/bar/license.md`.

* type: `filepath`
* default: `.`


files
---

List of files under `root` for which the remaining declarations apply to.  A
`null` value implies all files under `root` including those in subdirectories.

* type: `[filepath] | null`
* default: null


name
---

Display name used by `codebom graph`. If `null`, CodeBOM will use the last
path element in the `origin` declaration. If the `origin` declaration is
`null`, CodeBOM will use the last path element in the `root` declaration.

* type: `string | null`
* default: null


copyright-holders
---

A list of copyright holders. CodeBOM expects to find these names in the
copyright notice.

* type: `[string]`
* default: `[]`


licensees
---

A list of authorized clients. If a component has a restrictive license, the
`verify` command will warn if an unauthorized client adds it as a dependency.
To silence CodeBOM, ensure that at least one of the client's `copyright-holders`
is in the component's `licenees`.

* type: `[string]`
* default: `[]`


dependencies
---

A list of dependencies. Each item may be either a path to a BOM, a path to a
directory containing a `.bom.yaml`, a path to a root, or a BOM pertaining to
the the files at its `root` field.

* type: `[filepath | bom]`
* default: `[]`


development-dependencies
---

A list of dependencies used only for development.

* type: `[filepath | bom]`
* default: `[]`
