<!-- Source: https://www.lua.org/manual/5.4/readme.html
     Fetched: 2026-06-20
     License: Lua is distributed under the terms of the Lua license (an MIT-style license; see license.md).
     Reproduced under that license with attribution to Lua.org, PUC-Rio.
     This is the core Lua 5.4 reference, scraped from the official manual.
     Do not edit manually — re-fetch from the source above to update. -->

# Welcome to Lua 5.4

[about](#about) · [installation](#install) · [changes](#changes) · [license](#license) · [reference manual](https://www.lua.org/manual/5.4/contents.html)

## About Lua

Lua is a powerful, efficient, lightweight, embeddable scripting language developed by a [team](https://www.lua.org/authors.html) at [PUC-Rio](https://www.puc-rio.br/), the Pontifical Catholic University of Rio de Janeiro in Brazil. Lua is [free software](#license) used in [many products and projects](https://www.lua.org/uses.html) around the world.

Lua's [official website](https://www.lua.org/) provides complete information about Lua, including an [executive summary](https://www.lua.org/about.html), tips on [getting started](https://www.lua.org/start.html), and updated [documentation](https://www.lua.org/docs.html), especially the [reference manual](https://www.lua.org/manual/5.4/), which may differ slightly from the [local copy](https://www.lua.org/manual/5.4/contents.html) distributed in this package.

## Installing Lua

Lua is distributed in [source](https://www.lua.org/ftp/) form. You need to build it before using it. Building Lua should be straightforward because Lua is implemented in pure ISO C and compiles unmodified in all known platforms that have an ISO C compiler. Lua also compiles unmodified as C++. The instructions given below for building Lua are for Unix-like platforms, such as Linux and macOS. See also [instructions for other systems](#other) and [customization options](#customization).

If you don't have the time or the inclination to compile Lua yourself, get a binary from [LuaBinaries](https://luabinaries.sourceforge.net).

### Building Lua

In most common Unix-like platforms, simply do "make". Here are the details.

1. Open a terminal window and move to the top-level directory, which is named `lua-5.4.8`. The `Makefile` there controls both the build process and the installation process.

2. Do "make". The `Makefile` will guess your platform and build Lua for it.

3. If the guess failed, do "make help" and see if your platform is listed. The platforms currently supported are:

  guess aix bsd c89 freebsd generic ios linux linux-readline macosx mingw posix solaris

  If your platform is listed, just do "make xxx", where xxx is your platform name.

  If your platform is not listed, try the closest one or posix, generic, c89, in this order.

4. The compilation takes only a few moments and produces three files in the `src` directory: lua (the interpreter), luac (the compiler), and liblua.a (the library).

5. To check that Lua has been built correctly, do "make test" after building Lua. This will run the interpreter and print its version.

If you're running Linux, try "make linux-readline" to build the interactive Lua interpreter with handy line-editing and history capabilities. If you get compilation errors, make sure you have installed the `readline` development package (which is probably named `libreadline-dev` or `readline-devel`). If you get link errors after that, then try "make linux-readline MYLIBS=-ltermcap".

### Installing Lua

Once you have built Lua, you may want to install it in an official place in your system. In this case, do "make install". The official place and the way to install files are defined in the `Makefile`. You'll probably need the right permissions to install files, and so may need to do "sudo make install".

To build and install Lua in one step, do "make all install", or "make xxx install", where xxx is your platform name.

To install Lua locally after building it, do "make local". This will create a directory `install` with subdirectories `bin`, `include`, `lib`, `man`, `share`, and install Lua as listed below. To install Lua locally, but in some other directory, do "make install INSTALL_TOP=xxx", where xxx is your chosen directory. The installation starts in the `src` and `doc` directories, so take care if `INSTALL_TOP` is not an absolute path.

bin:

lua luac

include:

lua.h luaconf.h lualib.h lauxlib.h lua.hpp

lib:

liblua.a

man/man1:

lua.1 luac.1

These are the only directories you need for development. If you only want to run Lua programs, you only need the files in `bin` and `man`. The files in `include` and `lib` are needed for embedding Lua in C or C++ programs.

### Customization

Three kinds of things can be customized by editing a file:

- Where and how to install Lua — edit `Makefile`.

- How to build Lua — edit `src/Makefile`.

- Lua features — edit `src/luaconf.h`.

You don't actually need to edit the Makefiles because you may set the relevant variables in the command line when invoking make. Nevertheless, it's probably best to edit and save the Makefiles to record the changes you've made.

On the other hand, if you need to customize some Lua features, edit `src/luaconf.h` before building and installing Lua. The edited file will be the one installed, and it will be used by any Lua clients that you build, to ensure consistency. Further customization is available to experts by editing the Lua sources.

### Building Lua on other systems

If you're not using the usual Unix tools, then the instructions for building Lua depend on the compiler you use. You'll need to create projects (or whatever your compiler uses) for building the library, the interpreter, and the compiler, as follows:

library:

lapi.c lcode.c lctype.c ldebug.c ldo.c ldump.c lfunc.c lgc.c llex.c lmem.c lobject.c lopcodes.c lparser.c lstate.c lstring.c ltable.c ltm.c lundump.c lvm.c lzio.c lauxlib.c lbaselib.c lcorolib.c ldblib.c liolib.c lmathlib.c loadlib.c loslib.c lstrlib.c ltablib.c lutf8lib.c linit.c

interpreter:

library, lua.c

compiler:

library, luac.c

To use Lua as a library in your own programs, you need to know how to create and use libraries with your compiler. Moreover, to dynamically load C libraries for Lua, you'll need to know how to create dynamic libraries and you'll need to make sure that the Lua API functions are accessible to those dynamic libraries — but *don't* link the Lua library into each dynamic library. For Unix, we recommend that the Lua library be linked statically into the host program and its symbols exported for dynamic linking; `src/Makefile` does this for the Lua interpreter. For Windows, we recommend that the Lua library be a DLL. In all cases, the compiler luac should be linked statically.

As mentioned above, you may edit `src/luaconf.h` to customize some features before building Lua.

## Changes since Lua 5.3

Here are the main changes introduced in Lua 5.4. The [reference manual](https://www.lua.org/manual/5.4/contents.html) lists the [incompatibilities](https://www.lua.org/manual/5.4/manual.html#8) that had to be introduced.

### Main changes

- new generational mode for garbage collection

- to-be-closed variables

- const variables

- userdata can have multiple user values

- new implementation for math.random

- warning system

- debug information about function arguments and returns

- new semantics for the integer 'for' loop

- optional 'init' argument to 'string.gmatch'

- new functions 'lua_resetthread' and 'coroutine.close'

- string-to-number coercions moved to the string library

- allocation function allowed to fail when shrinking a memory block

- new format '%p' in 'string.format'

- utf8 library accepts codepoints up to 2^31

## License

Lua is free software distributed under the terms of the [MIT license](https://opensource.org/license/mit) reproduced below; it may be used for any purpose, including commercial purposes, at absolutely no cost without having to ask us. The only requirement is that if you do use Lua, then you should give us credit by including the appropriate copyright notice somewhere in your product or its documentation. For details, see the [license page](https://www.lua.org/license.html).

Copyright © 1994–2025 Lua.org, PUC-Rio.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
