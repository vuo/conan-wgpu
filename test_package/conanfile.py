from conans import ConanFile, CMake
import platform

class WgpuTestConan(ConanFile):
    settings = 'os', 'arch'
    generators = 'cmake'

    def build(self):
        cmake = CMake(self)

        self.run_test_app = True
        if self.settings.os == 'Linux':
            if self.settings.arch == 'aarch64' and self.settings.arch != platform.machine():
                # Cross-compiling on x86_64 for aarch64.
                cmake.definitions['CMAKE_C_COMPILER'] = 'aarch64-linux-gnu-gcc'
                # `binfmt-support` + `qemu` almost works,
                # but there's no straightforward way for an x86_64 Ubuntu installation to get an arm64 version of `libvulkan.so.1`,
                # and its absence causes wgpu-native to abort.
                # This may eventually become a trappable error: https://github.com/gfx-rs/wgpu-native/issues/113
                # For now, skip running the test.
                self.run_test_app = False

        cmake.configure()
        cmake.build()

    def imports(self):
        self.copy('*', src='bin', dst='bin')
        self.copy('*', src='lib', dst='lib')

    def test(self):
        if self.run_test_app:
            self.run('./bin/test_package')

        # Ensure we only link to system libraries and our own libraries.
        if self.settings.os == 'Macos':
            self.run('! (otool -L lib/libwgpu_native.dylib | grep -v "^lib/" | egrep -v "^\s*(/usr/lib/|/System/|@rpath/)")')
            self.run('! (otool -L lib/libwgpu_native.dylib | fgrep "libstdc++")')
            self.run('! (otool -l lib/libwgpu_native.dylib | grep -A2 LC_RPATH | cut -d"(" -f1 | grep "\s*path" | egrep -v "^\s*path @(executable|loader)_path")')
        elif self.settings.os == 'Linux':
            if self.run_test_app:
                self.run('! (ldd lib/libwgpu_native.so | grep "/" | egrep -v "(\s(/lib64/|(/usr)?/lib/x86_64-linux-gnu/)|test_package/build)")')
                self.run('! (ldd lib/libwgpu_native.so | fgrep "libstdc++")')
            else:
                # ldd only works on the host platform, so use `readelf` which at least lets us verify the load commands.
                self.run('! (aarch64-linux-gnu-readelf --dynamic lib/libwgpu_native.so | grep NEEDED | egrep -v "\[lib(dl|gcc_s|pthread|m|c)\.so")')
                self.run('! (aarch64-linux-gnu-readelf --dynamic lib/libwgpu_native.so | fgrep "libstdc++")')
