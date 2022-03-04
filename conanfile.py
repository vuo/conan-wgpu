from conans import ConanFile, tools
from conans.errors import ConanInvalidConfiguration
import platform
import shutil

class WgpuConan(ConanFile):
    name = 'wgpu'

    wgpu_version = '0.11.0.1.patched'
    wgpu_revision = '13afd6f1683ab7c4b4be9e453db1caeda50d837d'  # Latest commit as of 2022.03.05, which is 0.11.0.1 plus some Metal fixes (not yet in a tagged release).
    package_version = '0'
    version = '%s-%s' % (wgpu_version, package_version)

    settings = 'os', 'arch'
    url = 'https://github.com/gfx-rs/wgpu'
    license = 'https://github.com/gfx-rs/wgpu/blob/810dc5aa271d87312001081bb4cbb161ad135c6c/LICENSE.MIT'
    description = 'Safe and portable GPU abstraction in Rust, implementing WebGPU API'
    source_dir = 'wgpu-native'

    def validate(self):
        self.sysroot = ''
        if self.settings.os == 'Linux':
            if not self.settings.arch in ['x86_64', 'aarch64']:
                raise ConanInvalidConfiguration('Unknown arch "%s"' % self.settings.arch)
            self.target_suffix = '-unknown-linux-gnu'
            self.dylib_ext = 'so'
            self.arches = [ self.settings.arch ]
            if self.settings.arch == 'aarch64' and self.settings.arch != platform.machine():
                # Cross-compiling on x86_64 for aarch64.
                self.sysroot = '--sysroot /usr/aarch64-linux-gnu'
        elif self.settings.os == 'Macos':
            if self.settings.arch != 'x86_64':  # On macOS, we treat x86_64 as universal (x86_64 + arm64).
                raise ConanInvalidConfiguration('Unknown arch "%s"' % self.settings.arch)
            self.target_suffix = '-apple-darwin'
            self.dylib_ext = 'dylib'
            self.arches = ['x86_64', 'aarch64']
        else:
            raise ConanInvalidConfiguration('Unknown OS "%s"' % self.settings.os)

    def requirements(self):
        if self.settings.os == 'Macos':
            self.requires('macos-sdk/11.0-0@vuo/stable')

    def source(self):
        self.run("git clone --recurse-submodules https://github.com/gfx-rs/wgpu-native.git")
        with tools.chdir(self.source_dir):
            self.run("git checkout %s" % self.wgpu_revision)

        self.run('mv %s/LICENSE.MIT %s/%s.txt' % (self.source_dir, self.source_dir, self.name))

    def build(self):
        self.dylibs = []
        with tools.environment_append({
            'WGPU_NATIVE_VERSION': self.version,
            'BINDGEN_EXTRA_CLANG_ARGS': self.sysroot
        }):
            for arch in self.arches:
                target = '%s%s' % (arch, self.target_suffix)
                self.output.info("=== Build for %s ===" % target)
                with tools.chdir(self.source_dir):
                    if self.settings.os == 'Linux':
                        if self.settings.arch == 'aarch64' and self.settings.arch != platform.machine():
                            # Cross-compiling on x86_64 for aarch64.
                            tools.mkdir('.cargo')
                            with open('.cargo/config.toml', 'w') as f:
                                f.write('[target.aarch64-unknown-linux-gnu]\nlinker = "aarch64-linux-gnu-ld"\nrustflags = [ "-C", "link-arg=-L/usr/lib/gcc-cross/aarch64-linux-gnu/10" ]')

                    self.run('~/.cargo/bin/cargo build --release --target %s' % target)

                    dylib = 'target/%s/release/libwgpu_native.%s' % (target, self.dylib_ext)
                    if self.settings.os == 'Linux':
                        self.run('cp %s ..' % dylib)
                    elif self.settings.os == 'Macos':
                        self.run('install_name_tool -id @rpath/libwgpu_native.dylib %s' % dylib)
                    self.dylibs.append(dylib)

    def package(self):
        self.copy('*.h', src='%s/ffi' % self.source_dir, dst='include')

        if self.settings.os == 'Macos':
            self.run('lipo -create %s -output libwgpu_native.dylib' % ' '.join([self.source_dir + '/' + dylib for dylib in self.dylibs]))
        self.copy('libwgpu_native.%s' % self.dylib_ext, dst='lib')

        self.copy('%s.txt' % self.name, src=self.source_dir, dst='license')

    def package_info(self):
        self.cpp_info.libs = ['wgpu_native']
